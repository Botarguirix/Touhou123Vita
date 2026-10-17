#!/usr/bin/env python3
"""Run TH123 Player::canActivateCard (00468e80) against controlled hand states."""

from __future__ import annotations

import argparse
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
CAN_ACTIVATE_CARD = 0x00468E80
DEQUE_INDEX = 0x00456C80
PLAYER = 0x01000000
CARD_DEQUE = 0x01100000
CARD = 0x01200000
STACK = 0x02000000
STOP = 0x03000000
HAND_CARD_COUNT = 0x05E6
HAND_DEQUE = 0x05E8
WEATHER_ID = 0x052C


class CardActivationOracle:
    def __init__(self, exe: Path):
        raw = exe.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != REFERENCE_SHA256:
            raise ValueError(f"reference SHA-256 mismatch: {self.sha256}")
        pe = pefile.PE(data=raw)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        image = pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(self.base, (len(image) + 0xFFF) & ~0xFFF)
        self.uc.mem_write(self.base, image)
        for address, size in ((PLAYER, 0x1000), (CARD_DEQUE, 0x1000),
                              (CARD, 0x1000), (STACK, 0x10000)):
            self.uc.mem_map(address, size)
        self.indices: list[int] = []
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address != DEQUE_INDEX:
            return
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret, index = struct.unpack("<II", uc.mem_read(esp, 8))
        self.indices.append(index)
        pointer = CARD + index * 0x40
        uc.reg_write(UC_X86_REG_EAX, pointer)
        uc.reg_write(UC_X86_REG_ESP, esp + 8)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def run_case(self, slot: int, card_count: int, cost: int, weather_id: int) -> dict[str, object]:
        if not 0 <= slot <= 255 or not 0 <= card_count <= 255 or not 0 <= cost <= 65535:
            raise ValueError("slot/count/cost are outside supported input ranges")
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(CARD_DEQUE, struct.pack("<III", CARD, 0, max(card_count, 1)))
        uc.mem_write(PLAYER + HAND_DEQUE, struct.pack("<III", CARD_DEQUE, 0, card_count))
        uc.mem_write(PLAYER + HAND_CARD_COUNT, bytes([card_count]))
        uc.mem_write(PLAYER + WEATHER_ID, struct.pack("<I", weather_id))
        uc.mem_write(CARD, bytes(0x1000))
        for index in range(max(card_count, 1)):
            uc.mem_write(CARD + index * 0x40 + 2, struct.pack("<H", cost))
        self.indices = []
        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<II", STOP, slot))
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, CAN_ACTIVATE_CARD)
        uc.emu_start(CAN_ACTIVATE_CARD, STOP, count=10000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"canActivateCard did not return: {hex(uc.reg_read(UC_X86_REG_EIP))}")
        return {
            "slot": slot,
            "card_count": card_count,
            "card_cost": cost,
            "weather_id": weather_id,
            "can_activate": bool(uc.reg_read(UC_X86_REG_EAX) & 0xFF),
            "deque_indices": list(self.indices),
            "stack_balanced": uc.reg_read(UC_X86_REG_ESP) == entry_sp + 8,
        }


def analyze(exe: Path) -> dict[str, object]:
    oracle = CardActivationOracle(exe)
    cases = [
        ("empty_hand", 0, 0, 1, 0, False),
        ("hand_count_below_slot", 1, 0, 1, 0, False),
        ("cost_exceeds_hand", 0, 2, 3, 0, False),
        ("cost_exactly_met", 0, 3, 3, 0, True),
        ("weather_2_reduces_cost", 0, 2, 3, 2, True),
        ("weather_2_still_requires_one", 0, 0, 3, 2, False),
        ("weather_11_allows_one_card", 0, 1, 4, 11, True),
        ("slot_1_uses_second_hand_card", 1, 2, 2, 0, True),
    ]
    rows = []
    for name, slot, card_count, cost, weather, expected in cases:
        row = oracle.run_case(slot, card_count, cost, weather)
        row["case"] = name
        if row["can_activate"] != expected:
            raise AssertionError(f"canActivateCard contract mismatch: {row}; expected {expected}")
        # The helper only looks up cards when the requested slot exists; the
        # common cost path can perform one or two lookups depending on cost.
        if card_count > slot and len(row["deque_indices"]) not in (1, 2):
            raise AssertionError(f"unexpected deque lookup trace: {row}")
        if card_count <= slot and row["deque_indices"]:
            raise AssertionError(f"out-of-range slot performed a card lookup: {row}")
        if not row["stack_balanced"]:
            raise AssertionError(f"stack imbalance: {row}")
        rows.append(row)
    return {
        "schema": 1,
        "reference_sha256": oracle.sha256,
        "helper_va": hex(CAN_ACTIVATE_CARD),
        "cases": rows,
        "passed": True,
        "scope": (
            "Executes the original canActivateCard helper with hand/deque state controlled. "
            "The deque indexer is stubbed; the original cost/weather/count decisions execute x86."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path("original/th123.exe"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/x86-card-activation-oracle.json"))
    args = parser.parse_args()
    report = analyze(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"canActivateCard x86: {len(report['cases'])} cases; passed; output={args.output}")


if __name__ == "__main__":
    main()
