#!/usr/bin/env python3
"""Execute Reimu's action-505 object-emission branch from the pinned TH123 PE."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_EAX, UC_X86_REG_ESP, UC_X86_REG_ESI

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
CASE_505 = 0x0049985C
CREATE_OBJECT = 0x0046EB30
PLAYER = 0x01000000
STACK = 0x02000000
SCRATCH = 0x03000000
STOP = SCRATCH + 0x100


class Reimu505Oracle:
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
        for address, size in ((PLAYER, 0x2000), (STACK, 0x10000), (SCRATCH, 0x1000)):
            self.uc.mem_map(address, size)
        self.uc.mem_write(SCRATCH, b"\xd9\xe8\xeb\x00")  # fld1; stop before entering the switch.
        self.objects: list[dict[str, object]] = []
        self.stop_after = 0
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address == CREATE_OBJECT:
            esp = uc.reg_read(UC_X86_REG_ESP)
            words = struct.unpack("<8I", uc.mem_read(esp, 32))
            object_id, x, y, facing_byte, factory_arg4, velocity_ptr, flags = words[1:]
            velocity = struct.unpack("<2f", uc.mem_read(velocity_ptr, 8)) if velocity_ptr else (0.0, 0.0)
            self.objects.append({
                "object_id": object_id,
                "x": struct.unpack("<f", struct.pack("<I", x))[0],
                "y": struct.unpack("<f", struct.pack("<I", y))[0],
                "facing_byte": facing_byte,
                "factory_arg4": factory_arg4,
                "velocity": list(velocity),
                "flags": flags,
            })
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            uc.reg_write(UC_X86_REG_EAX, len(self.objects))
            uc.reg_write(UC_X86_REG_ESP, esp + 32)  # thiscall helper consumes seven args.
            uc.reg_write(UC_X86_REG_EIP, ret)
            if len(self.objects) == self.stop_after:
                uc.emu_stop()
            return

        # The surrounding x86 branch uses these engine services for state,
        # collision queries, sound, and animation. Isolate them while retaining
        # the original branches and all arithmetic leading to object creation.
        if address in (0x00487CA0, 0x0047A9E0, 0x00487870, 0x00464980):
            esp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            cleanup = {0x00487CA0: 0, 0x0047A9E0: 8, 0x00487870: 4, 0x00464980: 4}[address]
            uc.reg_write(UC_X86_REG_EAX, 0)
            uc.reg_write(UC_X86_REG_ESP, esp + 4 + cleanup)
            uc.reg_write(UC_X86_REG_EIP, ret)
            return

    def run(self, x: float, y: float, facing: int, route_value: int) -> dict[str, object]:
        uc = self.uc
        self.objects.clear()
        uc.mem_write(PLAYER, bytes(0x2000))
        # The table-selected branch checks action sequence 2, pose 2, frame 0.
        expected_count = {0: 3, 1: 4, 2: 5}[route_value]
        self.stop_after = expected_count
        uc.mem_write(PLAYER + 0x13E, struct.pack("<H", 2))
        uc.mem_write(PLAYER + 0x140, struct.pack("<H", 2))
        uc.mem_write(PLAYER + 0x142, struct.pack("<H", 0))
        uc.mem_write(PLAYER + 0x7D6, struct.pack("<H", route_value))
        uc.mem_write(PLAYER + 0x104, bytes([facing & 0xFF]))
        uc.mem_write(PLAYER + 0x6A8, struct.pack("<b", 0))
        uc.mem_write(PLAYER + 0xEC, struct.pack("<f", x))
        uc.mem_write(PLAYER + 0xF0, struct.pack("<f", y))
        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESI, PLAYER)
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, SCRATCH)
        uc.emu_start(SCRATCH, SCRATCH + 4, count=4)
        uc.reg_write(UC_X86_REG_EIP, CASE_505)
        uc.emu_start(CASE_505, STOP, count=100000)
        if len(self.objects) != expected_count:
            raise RuntimeError(f"expected {expected_count} object-811 emissions for route value {route_value}, got {len(self.objects)}")
        if any(item["object_id"] != 0x32B for item in self.objects):
            raise AssertionError(f"unexpected object ids: {self.objects}")
        return {
            "schema": 1,
            "reference_sha256": self.sha256,
            "character": "Reimu",
            "action": 505,
            "branch_va": hex(CASE_505),
            "sequence": 2,
            "pose": 2,
            "frame": 0,
            "route_value_at_player_7d6": route_value,
            "object_count": len(self.objects),
            "objects": self.objects,
            "scope": "Original action-505 CFG executes; generic engine service calls are stubbed, and object-factory arguments are captured.",
            "passed": True,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/x86-reimu-505-objects.json")
    parser.add_argument("--x", type=float, default=190.0)
    parser.add_argument("--y", type=float, default=0.0)
    parser.add_argument("--facing", type=int, choices=(-1, 1), default=1)
    parser.add_argument("--route-value", type=int, choices=(0, 1, 2), default=0,
                        help="value at Player+0x7D6 selecting a branch of the original pattern")
    args = parser.parse_args()
    result = Reimu505Oracle(args.exe).run(args.x, args.y, args.facing, args.route_value)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Reimu action 505: captured {result['object_count']} object-811 emissions; output={args.output}")


if __name__ == "__main__":
    main()
