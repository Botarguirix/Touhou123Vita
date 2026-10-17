#!/usr/bin/env python3
"""Execute the pinned TH123 Player::onSkillUpgrade helper under Unicorn."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local/python-deps"))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
ON_SKILL_UPGRADE = 0x00489660
DEQUE_INDEX = 0x00456C80
CREATE_OBJECT = 0x00438CE0
CONSUME_CARD = 0x00469C70
EVENT_SPELL_USE = 0x00483D60
TAIL_UPDATE = 0x00468B50
PLAYER = 0x01000000
CARD_DEQUE = 0x01100000
CARD = 0x01200000
STACK = 0x02000000
STOP = 0x03000000
SKILL_LEVELS_OFFSET = 0x06C4


def read_skill_slots(path: Path) -> dict[int, int]:
    slots: dict[int, int] = {}
    with path.open(encoding="cp932", newline="") as stream:
        for row in csv.reader(stream):
            if len(row) >= 4 and row[0].isdigit() and 100 <= int(row[0]) <= 111:
                if row[2] != "1" or not row[3].isdigit():
                    raise ValueError(f"Card {row[0]} is not a valid skill card")
                slots[int(row[0])] = int(row[3])
    if set(slots) != set(range(100, 112)):
        raise ValueError(f"Expected Reimu skill cards 100..111, found {sorted(slots)}")
    return slots


class SkillUpgradeOracle:
    def __init__(self, exe: Path):
        image_bytes = exe.read_bytes()
        self.sha256 = hashlib.sha256(image_bytes).hexdigest()
        if self.sha256 != REFERENCE_SHA256:
            raise ValueError(f"reference SHA-256 mismatch: {self.sha256}")
        pe = pefile.PE(data=image_bytes)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        image = pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(self.base, (len(image) + 0xFFF) & ~0xFFF)
        self.uc.mem_write(self.base, image)
        for address, size in ((PLAYER, 0x1000), (CARD_DEQUE, 0x1000),
                              (CARD, 0x1000), (STACK, 0x10000)):
            self.uc.mem_map(address, size)
        self.current: dict[str, object] = {}
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address not in (DEQUE_INDEX, CREATE_OBJECT, CONSUME_CARD, EVENT_SPELL_USE, TAIL_UPDATE):
            return
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        if address == DEQUE_INDEX:
            arg = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
            if arg != 0:
                raise AssertionError(f"onSkillUpgrade indexed unexpected hand position {arg}")
            uc.reg_write(UC_X86_REG_EAX, CARD)
            self.current["deque_index_calls"] = int(self.current["deque_index_calls"]) + 1
            cleanup = 8  # return address plus one 32-bit thiscall argument
        elif address == CREATE_OBJECT:
            action = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
            self.current["spawn_actions"].append(action)  # type: ignore[union-attr]
            uc.reg_write(UC_X86_REG_EAX, 0)
            cleanup = 0x18  # return address plus five stack argument words
        elif address == CONSUME_CARD:
            args = struct.unpack("<III", uc.mem_read(esp + 4, 12))
            self.current["consume_card_args"] = list(args)
            cleanup = 0x10  # return address plus three arguments
        elif address == EVENT_SPELL_USE:
            self.current["spell_use_events"] = int(self.current["spell_use_events"]) + 1
            cleanup = 4
        else:
            self.current["tail_update_calls"] = int(self.current["tail_update_calls"]) + 1
            self.current["stack_at_tail"] = esp
            uc.reg_write(UC_X86_REG_ESP, esp + 4)
            uc.reg_write(UC_X86_REG_EIP, ret)
            uc.emu_stop()
            return
        uc.reg_write(UC_X86_REG_ESP, esp + cleanup)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def run_case(self, card_id: int, initial_levels: bytes) -> dict[str, object]:
        if not 100 <= card_id <= 111:
            raise ValueError("This oracle currently covers Reimu skill cards 100..111")
        if len(initial_levels) != 32:
            raise ValueError("initial_levels must contain the 32-byte skilledSkillLevel array")
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(PLAYER + 0x5E8, struct.pack("<III", CARD_DEQUE, 0, 1))
        uc.mem_write(CARD_DEQUE, struct.pack("<III", CARD, 0, 1))
        uc.mem_write(CARD, struct.pack("<H", card_id) + bytes(30))
        uc.mem_write(PLAYER + SKILL_LEVELS_OFFSET, initial_levels)
        self.current = {
            "deque_index_calls": 0,
            "spawn_actions": [],
            "consume_card_args": None,
            "spell_use_events": 0,
            "tail_update_calls": 0,
        }
        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, ON_SKILL_UPGRADE)
        uc.emu_start(ON_SKILL_UPGRADE, STOP, count=100000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"onSkillUpgrade did not return for card {card_id}")
        levels = bytes(uc.mem_read(PLAYER + SKILL_LEVELS_OFFSET, 32))
        return {
            "card_id": card_id,
            "skill_index": card_id - 100,
            "skill_level_before": initial_levels[card_id - 100],
            "skill_level_after": levels[card_id - 100],
            "skill_levels_after": list(levels),
            "spawn_actions": self.current["spawn_actions"],
            "consume_card_args": self.current["consume_card_args"],
            "deque_index_calls": self.current["deque_index_calls"],
            "spell_use_events": self.current["spell_use_events"],
            "tail_update_calls": self.current["tail_update_calls"],
            "stack_balanced_at_return": uc.reg_read(UC_X86_REG_ESP) == entry_sp + 4,
        }


def analyze(exe: Path, spellcard_csv: Path) -> dict[str, object]:
    slots = read_skill_slots(spellcard_csv)
    oracle = SkillUpgradeOracle(exe)
    rows = []
    for card_id in range(100, 112):
        levels = bytearray(32)
        row = oracle.run_case(card_id, bytes(levels))
        row["cost_or_slot"] = slots[card_id]
        index = card_id - 100
        same_slot_indices = [other - 100 for other, slot in slots.items()
                             if slot == slots[card_id] and other != card_id]
        # For the 12 entries present in Reimu's deck CSV, the other card
        # variants occupy +4 strides in skilledSkillLevel. Include absent
        # IDs where the common helper has a fourth variant in the 16-card table.
        reset_indices = [candidate for candidate in range(index % 4, 16, 4)
                         if candidate != index]
        row["same_cost_or_slot_card_indices"] = sorted(same_slot_indices)
        row["invalidated_skill_indices"] = reset_indices
        if row["skill_level_after"] != 1:
            raise AssertionError(f"fresh skill did not initialize to level 1: {row}")
        if any(row["skill_levels_after"][candidate] != 0xFF for candidate in reset_indices):
            raise AssertionError(f"same-slot alternatives were not invalidated: {row}")
        if row["spawn_actions"] != [0x47, 0x83]:
            raise AssertionError(f"unexpected upgrade effect object actions: {row}")
        if row["consume_card_args"] != [0, 0, 60]:
            raise AssertionError(f"unexpected card consumption arguments: {row}")
        if row["deque_index_calls"] != 2 or row["spell_use_events"] != 1:
            raise AssertionError(f"unexpected helper side effects: {row}")
        if row["tail_update_calls"] != 1 or not row["stack_balanced_at_return"]:
            raise AssertionError(f"unexpected helper exit contract: {row}")
        rows.append(row)

    cap_rows = []
    for initial, expected in ((0xFF, 1), (0, 1), (2, 3), (3, 4), (4, 4)):
        levels = bytearray(32)
        levels[0] = initial
        row = oracle.run_case(100, bytes(levels))
        if row["skill_level_after"] != expected:
            raise AssertionError(f"skill-level transition mismatch {initial:#x}: {row}")
        expected_spawn_actions = [0x47, 0x82 + expected]
        if row["spawn_actions"] != expected_spawn_actions:
            raise AssertionError(f"skill effect did not reflect resulting level: {row}")
        cap_rows.append({"before": initial, "after": expected,
                         "spawn_actions": row["spawn_actions"]})
    return {
        "schema": 1,
        "reference_sha256": oracle.sha256,
        "helper_va": hex(ON_SKILL_UPGRADE),
        "character": "Reimu",
        "card_cases": rows,
        "level_boundary_cases": cap_rows,
        "passed": True,
        "scope": (
            "Executes the original onSkillUpgrade code for Reimu cards 100..111. External deque, "
            "object creation, card consumption, spell event, and tail update helpers are stubbed; "
            "the helper's own skilledSkillLevel mutations and selected object actions execute x86."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path("original/th123.exe"))
    parser.add_argument("--spellcard", type=Path,
                        default=Path("artifacts/extracted/data/csv/reimu/spellcard.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/x86-skill-upgrade-oracle.json"))
    args = parser.parse_args()
    report = analyze(args.exe, args.spellcard)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"onSkillUpgrade x86: {len(report['card_cases'])} cards; passed; output={args.output}")


if __name__ == "__main__":
    main()
