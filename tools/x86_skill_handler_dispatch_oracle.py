#!/usr/bin/env python3
"""Execute Reimu's original grounded/airborne skill-card dispatch blocks."""

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
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ECX,
    UC_X86_REG_EDI, UC_X86_REG_EIP, UC_X86_REG_ESI, UC_X86_REG_ESP,
)

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
GROUND_SWITCH = 0x004AE8B1
AIR_SWITCH = 0x004AF821
EVENT_SKILL_USE = 0x00483CE0
ON_SKILL_UPGRADE = 0x00489660
USE_SKILL = 0x00487BA0
PLAYER = 0x01000000
CARD = 0x01100000
STACK = 0x02000000
STOP = 0x03000000


class SkillHandlerDispatchOracle:
    def __init__(self, exe: Path):
        raw = exe.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != REFERENCE_SHA256:
            raise ValueError(f"reference SHA-256 mismatch: {self.sha256}")
        pe = pefile.PE(data=raw)
        base = pe.OPTIONAL_HEADER.ImageBase
        image = pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(base, (len(image) + 0xFFF) & ~0xFFF)
        self.uc.mem_write(base, image)
        for address, size in ((PLAYER, 0x1000), (CARD, 0x1000), (STACK, 0x10000)):
            self.uc.mem_map(address, size)
        self.current: dict[str, int | str] = {}
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address not in (EVENT_SKILL_USE, ON_SKILL_UPGRADE, USE_SKILL):
            return
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        if address == USE_SKILL:
            action, action_lock = struct.unpack("<II", uc.mem_read(esp + 4, 8))
            self.current["use_skill_action"] = action
            self.current["use_skill_action_lock"] = action_lock
            cleanup = 12  # ret 8: return address plus two arguments
        else:
            key = "event_skill_use_calls" if address == EVENT_SKILL_USE else "upgrade_calls"
            self.current[key] = int(self.current[key]) + 1
            cleanup = 4
        uc.reg_write(UC_X86_REG_ESP, esp + cleanup)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def run_case(self, context: str, card_id: int, action_lock: int = 23) -> dict[str, int | str]:
        if context not in ("grounded", "airborne"):
            raise ValueError("context must be grounded or airborne")
        if not 100 <= card_id <= 111:
            raise ValueError("card_id must be between 100 and 111")
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(CARD, struct.pack("<H", card_id) + bytes(30))
        self.current = {
            "context": context,
            "card_id": card_id,
            "event_skill_use_calls": 0,
            "upgrade_calls": 0,
            "use_skill_action": -1,
            "use_skill_action_lock": -1,
        }

        # This block is entered after handleInputs' shared prologue. Its selected
        # case returns through the matching shared epilogue.
        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack(
            "<IIIIIII", 0xEEEEEEEE, 0xDDDDDDDD, 0xCCCCCCCC,
            0xBBBBBBBB, 0xAAAAAAAA, 0x99999999, STOP,
        ))
        uc.reg_write(UC_X86_REG_EAX, CARD)
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESI, PLAYER)
        uc.reg_write(UC_X86_REG_EBP, action_lock)
        uc.reg_write(UC_X86_REG_EBX, action_lock)
        uc.reg_write(UC_X86_REG_EDI, 0)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        start = GROUND_SWITCH if context == "grounded" else AIR_SWITCH
        uc.reg_write(UC_X86_REG_EIP, start)
        uc.emu_start(start, STOP, count=1000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(
                f"switch failed to return for {context} card {card_id}: "
                f"EIP={uc.reg_read(UC_X86_REG_EIP):#x}"
            )
        if uc.reg_read(UC_X86_REG_ESP) != entry_sp + 28:
            raise RuntimeError("handler switch returned with an unexpected stack position")
        return dict(self.current)


def run(exe: Path) -> dict[str, object]:
    oracle = SkillHandlerDispatchOracle(exe)
    # Airborne cards with no explicit case jump into the rest of handleInputs;
    # those are verified as absent by the image jump table/static route analyzer.
    expected = {
        "grounded": {100: 500, 101: 520, 102: 540, 103: 560, 104: 505, 105: 525,
                     106: 545, 107: 565, 108: 510, 109: 530, 110: 550, 111: 570},
        "airborne": {100: 502, 101: 522, 102: 540, 104: 507, 105: 527, 106: 545,
                     108: 512, 111: 572},
    }
    rows = []
    for context, routes in expected.items():
        for card_id, action_id in routes.items():
            row = oracle.run_case(context, card_id)
            if row["use_skill_action"] != action_id:
                raise AssertionError(f"dispatch mismatch: expected {action_id}, got {row}")
            if row["use_skill_action_lock"] != 23:
                raise AssertionError(f"actionLock argument mismatch: {row}")
            if row["event_skill_use_calls"] != 1 or row["upgrade_calls"] != 1:
                raise AssertionError(f"expected one event and upgrade call: {row}")
            rows.append(row)
    return {
        "schema": 1,
        "reference_sha256": oracle.sha256,
        "entrypoints": {"grounded": hex(GROUND_SWITCH), "airborne": hex(AIR_SWITCH)},
        "executed_dispatches": len(rows),
        "rows": rows,
        "scope": "Original x86 card-switch blocks and epilogue executed; shared activation guards and side-effect helpers were bypassed or stubbed.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path("original/th123.exe"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/x86-skill-handler-dispatch.json"))
    args = parser.parse_args()
    report = run(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {report['executed_dispatches']} original x86 dispatches; wrote {args.output}")


if __name__ == "__main__":
    main()
