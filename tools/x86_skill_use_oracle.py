#!/usr/bin/env python3
"""Execute Player::useSkill (00487ba0) from the pinned TH123 PE under Unicorn."""

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
USE_SKILL = 0x00487BA0
RESEED_INPUT = 0x0046D950
REBUILD_HISTORY = 0x0046D890
PLAYER = 0x01000000
VTABLE = 0x01100000
STACK = 0x02000000
SET_ACTION = 0x03000000
STOP = 0x03100000
USE_SKILL_BYTES = bytes.fromhex(
    "83 7c 24 08 0a 56 8b f1 7c 07 80 8e ad 04 00 00 08 "
    "8b 4c 24 08 8b 06 8b 50 08 51 8b ce ff d2 8b ce "
    "e8 8a 5d fe ff d9 ee d9 9e 2c 01 00 00 5e c2 08 00"
)


class SkillUseOracle:
    def __init__(self, exe: Path):
        raw = exe.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != REFERENCE_SHA256:
            raise ValueError(f"reference SHA-256 mismatch: {self.sha256}")
        pe = pefile.PE(data=raw)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        actual = pe.get_data(USE_SKILL - self.base, len(USE_SKILL_BYTES))
        if actual != USE_SKILL_BYTES:
            raise ValueError(f"useSkill signature changed: {actual.hex()}")
        image = pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(self.base, (len(image) + 0xFFF) & ~0xFFF)
        self.uc.mem_write(self.base, image)
        for address, size in (
            (PLAYER, 0x1000), (VTABLE, 0x1000), (STACK, 0x10000),
            (SET_ACTION, 0x1000), (STOP, 0x1000),
        ):
            self.uc.mem_map(address, size)
        self.rows: list[dict[str, int]] = []
        self.current: dict[str, int] = {}
        self.execute_reseed = False
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        esp = uc.reg_read(UC_X86_REG_ESP)
        if address == SET_ACTION:
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            action_id = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
            self.current["selected_action"] = action_id
            uc.reg_write(UC_X86_REG_EAX, 1)
            uc.reg_write(UC_X86_REG_ESP, esp + 8)  # thiscall callee returns with ret 4
            uc.reg_write(UC_X86_REG_EIP, ret)
        elif address == RESEED_INPUT:
            self.current["history_reseed_calls"] += 1
            if self.execute_reseed:
                return
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            uc.reg_write(UC_X86_REG_ESP, esp + 4)
            uc.reg_write(UC_X86_REG_EIP, ret)
        elif address == REBUILD_HISTORY:
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            capacity = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
            sample_ptr = struct.unpack("<I", uc.mem_read(esp + 8, 4))[0]
            sample = struct.unpack("<H", uc.mem_read(sample_ptr, 2))[0]
            self.current["history_capacity"] = capacity
            self.current["packed_sample"] = sample
            uc.reg_write(UC_X86_REG_ESP, esp + 12)  # ret 8
            uc.reg_write(UC_X86_REG_EIP, ret)

    def run_case(self, action_id: int, marker: int) -> dict[str, int]:
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(VTABLE, bytes(0x1000))
        uc.mem_write(PLAYER, struct.pack("<I", VTABLE))
        uc.mem_write(VTABLE + 8, struct.pack("<I", SET_ACTION))
        uc.mem_write(PLAYER + 0x4AD, b"\x20")
        uc.mem_write(PLAYER + 0x12C, struct.pack("<f", 10.0))
        self.current = {"selected_action": 0, "history_reseed_calls": 0}

        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<III", STOP, action_id, marker))
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, USE_SKILL)
        uc.emu_start(USE_SKILL, STOP, count=1000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError("useSkill did not return to the stop address")

        flag = uc.mem_read(PLAYER + 0x4AD, 1)[0]
        movement = struct.unpack("<f", uc.mem_read(PLAYER + 0x12C, 4))[0]
        result = {
            "action_argument": action_id,
            "second_argument": marker,
            "selected_action": self.current["selected_action"],
            "flags_before": 0x20,
            "flags_after": flag,
            "history_reseed_calls": self.current["history_reseed_calls"],
            "field_0x12c_bits_after": struct.unpack("<I", struct.pack("<f", movement))[0],
        }
        self.rows.append(result)
        return result

    def run_input_seed_case(self, horizontal: int, vertical: int, buttons: int) -> dict[str, int]:
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(PLAYER + 0x754, struct.pack("<ii", horizontal, vertical))
        for index in range(4):
            uc.mem_write(PLAYER + 0x75C + index * 4, struct.pack("<I", (buttons >> index) & 1))
        self.current = {"history_reseed_calls": 0, "history_capacity": 0, "packed_sample": 0}
        self.execute_reseed = True
        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, RESEED_INPUT)
        uc.emu_start(RESEED_INPUT, STOP, count=1000)
        self.execute_reseed = False
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError("input reseed helper did not return")
        return dict(self.current)


def run(exe: Path, output: Path) -> dict[str, object]:
    oracle = SkillUseOracle(exe)
    cases = [(502, 0), (502, 9), (502, 10), (502, 51), (522, 10)]
    rows = [oracle.run_case(action_id, marker) for action_id, marker in cases]
    for row in rows:
        expected_flag = 0x20 | (0x08 if row["second_argument"] >= 10 else 0)
        if row["selected_action"] != row["action_argument"]:
            raise AssertionError(f"vtable action dispatch mismatch: {row}")
        if row["flags_after"] != expected_flag:
            raise AssertionError(f"skill-use flag mismatch: {row}")
        if row["history_reseed_calls"] != 1:
            raise AssertionError(f"input-history reseed call mismatch: {row}")
        if row["field_0x12c_bits_after"] != 0:
            raise AssertionError(f"field +0x12c was not cleared: {row}")
    seed_cases = 0
    for horizontal in (-1, 0, 1):
        for vertical in (-1, 0, 1):
            for buttons in range(16):
                actual = oracle.run_input_seed_case(horizontal, vertical, buttons)
                expected = (
                    (0x02 if horizontal > 0 else 0x01 if horizontal < 0 else 0)
                    | (0x08 if vertical > 0 else 0x04 if vertical < 0 else 0)
                    | (buttons << 4)
                )
                if actual["history_capacity"] != 90 or actual["packed_sample"] != expected:
                    raise AssertionError(
                        f"input seed mismatch h={horizontal} v={vertical} buttons={buttons:#x}: "
                        f"{actual}, expected sample {expected:#x}"
                    )
                seed_cases += 1
    report: dict[str, object] = {
        "schema": 1,
        "reference_sha256": oracle.sha256,
        "use_skill_va": hex(USE_SKILL),
        "reseed_helper_va": hex(RESEED_INPUT),
        "cases": rows,
        "input_seed_matrix": {
            "cases": seed_cases,
            "passed": seed_cases == 144,
            "horizontal_values": [-1, 0, 1],
            "vertical_values": [-1, 0, 1],
            "button_masks": 16,
            "capacity": 90,
        },
        "passed": True,
        "scope": (
            "Executes original useSkill with the vtable setAction and input reseed calls stubbed; "
            "the reset helper's 90-sample contents and card/cancel prerequisites are outside this probe."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"useSkill x86 cases: {len(rows)}; passed: {sum(1 for _ in rows)}; output={output}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.exe, args.output)


if __name__ == "__main__":
    main()
