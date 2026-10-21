#!/usr/bin/env python3
"""Execute Suika's original 623B/623C skill-selection blocks from the pinned PE."""
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
ENTRY = 0x0060A45C  # Suika handleInputs, test Player+0x7c8 for 623C
GET_MOVE_LOCK = 0x00489610
EVENT_SKILL_USE = 0x00483CE0
USE_SKILL = 0x00487BA0
RESEED_INPUT = 0x0046D950
PLAYER = 0x01000000
VTABLE = PLAYER + 0x900
STACK = 0x02000000
STOP = 0x03000000
SET_ACTION_HOOK = STOP + 0x100


class Suika623CProbe:
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
        self.uc.mem_map(PLAYER, 0x1000)
        self.uc.mem_map(STACK, 0x10000)
        self.uc.mem_map(STOP, 0x1000)
        self.current: dict[str, object] = {}
        self.move_lock_result = 0
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _return(self, uc: Uc, esp: int, cleanup: int) -> None:
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        uc.reg_write(UC_X86_REG_ESP, esp + cleanup)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address == GET_MOVE_LOCK:
            esp = uc.reg_read(UC_X86_REG_ESP)
            action = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
            self.current["move_lock_queries"].append(action)  # type: ignore[union-attr]
            uc.reg_write(UC_X86_REG_EAX, self.move_lock_result & 0xFFFF)
            self._return(uc, esp, 8)  # thiscall ret 4
        elif address == EVENT_SKILL_USE:
            self.current["event_skill_use_calls"] = int(self.current["event_skill_use_calls"]) + 1
            self._return(uc, uc.reg_read(UC_X86_REG_ESP), 4)
        elif address == USE_SKILL:
            esp = uc.reg_read(UC_X86_REG_ESP)
            selected_action, second_arg = struct.unpack("<II", uc.mem_read(esp + 4, 8))
            self.current["selected_action"] = selected_action
            self.current["use_skill_second_argument"] = second_arg
            self.current["use_skill_original_body_executed"] = True
        elif address == SET_ACTION_HOOK:
            esp = uc.reg_read(UC_X86_REG_ESP)
            _ret, action = struct.unpack("<II", uc.mem_read(esp, 8))
            self.current["set_action_requests"].append(action)  # type: ignore[union-attr]
            uc.reg_write(UC_X86_REG_EAX, 1)
            self._return(uc, esp, 8)  # thiscall ret 4
        elif address == RESEED_INPUT:
            self.current["input_reseed_calls"] = int(self.current["input_reseed_calls"]) + 1
            self._return(uc, uc.reg_read(UC_X86_REG_ESP), 4)

    def run_case(self, effective_level_9: int, effective_level_5: int,
                 move_lock_result: int = 0, command_mask: int = 0x400,
                 entry: int | None = None) -> dict[str, object]:
        if effective_level_9 not in range(4) or effective_level_5 not in range(4):
            raise ValueError("fixture levels must be in [0, 3]")
        self.move_lock_result = move_lock_result
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(PLAYER + 0x13C, struct.pack("<H", 0x180))
        uc.mem_write(PLAYER + 0x6A9, bytes([effective_level_5]))
        uc.mem_write(PLAYER + 0x6AD, bytes([effective_level_9]))
        uc.mem_write(PLAYER + 0x7C8, struct.pack("<I", command_mask))
        uc.mem_write(PLAYER, struct.pack("<I", VTABLE))
        uc.mem_write(VTABLE + 2 * 4, struct.pack("<I", SET_ACTION_HOOK))
        self.current = {
            "effective_level_9": effective_level_9,
            "effective_level_5": effective_level_5,
            "command_mask": command_mask,
            "move_lock_queries": [],
            "event_skill_use_calls": 0,
            "selected_action": -1,
            "use_skill_second_argument": -1,
            "use_skill_original_body_executed": False,
            "set_action_requests": [],
            "input_reseed_calls": 0,
        }

        # ENTRY is inside the handler after its prologue. The original return
        # epilogue consumes four saved registers and two local dwords.
        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack(
            "<IIIIIII", 0xEEEEEEEE, 0xDDDDDDDD, 0xCCCCCCCC,
            0xBBBBBBBB, 0, 0, STOP,
        ))
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESI, PLAYER)
        uc.reg_write(UC_X86_REG_EBP, 0)
        uc.reg_write(UC_X86_REG_EBX, 1)
        uc.reg_write(UC_X86_REG_EDI, 0)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        entry_address = ENTRY if entry is None else entry
        uc.reg_write(UC_X86_REG_EIP, entry_address)
        uc.emu_start(entry_address, STOP, count=1000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"623C block did not return: EIP={uc.reg_read(UC_X86_REG_EIP):#x}")
        if uc.reg_read(UC_X86_REG_ESP) != entry_sp + 28:
            raise RuntimeError("623C epilogue returned with an unexpected stack position")
        return dict(self.current)


def run(exe: Path) -> dict[str, object]:
    probe = Suika623CProbe(exe)
    cases = [
        (1, 0, 0, 531, [531]),
        (0, 1, 0, 526, [526]),
        (0, 0, 0, 521, [521]),
        (1, 1, 0xFFFF, -1, [531, 526, 521]),
    ]
    rows = []
    for level9, level5, lock_result, expected_action, expected_queries in cases:
        row = probe.run_case(level9, level5, lock_result)
        if row["selected_action"] != expected_action:
            raise AssertionError(f"action selection mismatch: expected {expected_action}, got {row}")
        if row["move_lock_queries"] != expected_queries:
            raise AssertionError(f"move-lock query mismatch: expected {expected_queries}, got {row}")
        expected_event_calls = int(expected_action != -1)
        expected_second_arg = 0 if expected_event_calls else -1
        if (row["event_skill_use_calls"] != expected_event_calls
                or row["use_skill_second_argument"] != expected_second_arg):
            raise AssertionError(f"skill activation side effects mismatch: {row}")
        expected_setter_calls = [expected_action] if expected_action != -1 else []
        expected_reseed_calls = int(expected_action != -1)
        if (row["set_action_requests"] != expected_setter_calls
                or row["input_reseed_calls"] != expected_reseed_calls
                or row["use_skill_original_body_executed"] != bool(expected_action != -1)):
            raise AssertionError(f"original useSkill path mismatch: {row}")
        rows.append(row)
    b_cases=[]
    for level9,level5,lock_result,expected_action,expected_queries in [
            (1,0,0,530,[530]),(0,1,0,525,[525]),(0,0,0,520,[520]),
            (1,1,0xFFFF,-1,[530,525,520])]:
        row=probe.run_case(level9,level5,lock_result,command_mask=0x200,entry=0x0060A5B0)
        if row["selected_action"]!=expected_action or row["move_lock_queries"]!=expected_queries:
            raise AssertionError(f"original 623B route mismatch: expected {expected_action}/{expected_queries}, got {row}")
        event_calls=int(expected_action!=-1)
        if (row["event_skill_use_calls"]!=event_calls or
                row["use_skill_second_argument"]!=(0 if event_calls else -1) or
                row["set_action_requests"]!=([expected_action] if event_calls else []) or
                row["input_reseed_calls"]!=event_calls or
                row["use_skill_original_body_executed"]!=bool(event_calls)):
            raise AssertionError(f"original 623B useSkill side effects mismatch: {row}")
        b_cases.append(row)
    return {
        "schema": 1,
        "reference_sha256": probe.sha256,
        "entry": hex(ENTRY),
        "cases": rows,
        "623b_entry": "0x60a5b0",
        "623b_cases": b_cases,
        "passed": True,
        "scope": "Original Suika 623C block (0x60a45c, command bit 0x400) and 623B block (0x60a5b0, command bit 0x200), including each useSkill body, execute from the pinned PE. Move-lock/eventSkillUse, the virtual setAction boundary, and input reseed are controlled/observed. Full input production, actual action initialization/update, objects and collision are not executed by this probe.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path("original/th123.exe"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/x86-suika-623c-dispatch.json"))
    args = parser.parse_args()
    report = run(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(report['cases'])} original Suika 623C level routes; wrote {args.output}")


if __name__ == "__main__":
    main()
