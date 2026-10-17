#!/usr/bin/env python3
"""Execute Suwako's original 418 spawn arithmetic in the pinned TH123 PE."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_EAX, UC_X86_REG_ESP, UC_X86_REG_ESI

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
HANDLER_418 = 0x0076F3B4
CREATE_OBJECT = 0x0046EB30
PLAYER = 0x01000000
STACK = 0x02000000
RECORD = 0x03000000
STOP = RECORD + 0x800


class Suwako418Oracle:
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
        for address, size in ((PLAYER, 0x2000), (STACK, 0x10000), (RECORD, 0x1000)):
            self.uc.mem_map(address, size)
        self.objects: list[dict[str, object]] = []
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address == CREATE_OBJECT:
            esp = uc.reg_read(UC_X86_REG_ESP)
            words = struct.unpack("<8I", uc.mem_read(esp, 32))
            object_id, x, y, facing, arg4, custom, flags = words[1:]
            self.objects.append({
                "object_id": object_id,
                "x": struct.unpack("<f", struct.pack("<I", x))[0],
                "y": struct.unpack("<f", struct.pack("<I", y))[0],
                "facing": facing,
                "arg4": arg4,
                "custom_data": list(struct.unpack("<3I", uc.mem_read(custom, 12))) if custom else [],
                "flags": flags,
            })
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            uc.reg_write(UC_X86_REG_EAX, len(self.objects))
            uc.reg_write(UC_X86_REG_ESP, esp + 32)
            uc.reg_write(UC_X86_REG_EIP, ret)
            uc.emu_stop()
            return

        # Keep the original handler and spawn arithmetic; replace only engine
        # services whose state is outside this isolated creation-path probe.
        if address == 0x00487CA0:
            esp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            uc.reg_write(UC_X86_REG_ESP, esp + 4)
            uc.reg_write(UC_X86_REG_EIP, ret)
        elif address == 0x004099F0:
            esp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            uc.reg_write(UC_X86_REG_EAX, 0)
            uc.reg_write(UC_X86_REG_ESP, esp + 8)  # return address and caller's one argument
            uc.reg_write(UC_X86_REG_EIP, ret)

    def run(self, x: float, y: float, facing: int, offset_x: int, offset_y: int) -> dict[str, object]:
        uc = self.uc
        self.objects.clear()
        uc.mem_write(PLAYER, bytes(0x2000))
        uc.mem_write(RECORD, bytes(0x1000))
        uc.mem_write(PLAYER + 0x158, struct.pack("<I", RECORD))
        uc.mem_write(RECORD + 0x98, struct.pack("<i", offset_x))
        uc.mem_write(RECORD + 0x9C, struct.pack("<i", offset_y))
        uc.mem_write(PLAYER + 0x104, struct.pack("<b", facing))
        uc.mem_write(PLAYER + 0xEC, struct.pack("<f", x))
        uc.mem_write(PLAYER + 0xF0, struct.pack("<f", y))
        uc.mem_write(PLAYER + 0x7F0, struct.pack("<f", x))
        uc.mem_write(PLAYER + 0x7D0, struct.pack("<H", 1))
        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESI, PLAYER)
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, HANDLER_418)
        uc.emu_start(HANDLER_418, STOP, count=100000)
        if len(self.objects) != 1:
            raise RuntimeError(f"expected one object-808 spawn, got {len(self.objects)}")
        item = self.objects[0]
        if item["object_id"] != 0x328:
            raise AssertionError(f"unexpected object id: {item}")
        return {
            "schema": 1,
            "reference_sha256": self.sha256,
            "character": "Suwako",
            "action": 418,
            "handler_va": hex(HANDLER_418),
            "input": {"x": x, "y": y, "facing": facing, "record_98": offset_x, "record_9c": offset_y},
            "objects": self.objects,
            "scope": "Original 418 handler and spawn arithmetic execute; floor query and animation service are stubbed; no action-time record producer is asserted.",
            "passed": True,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/x86-suwako-418-spawn.json")
    parser.add_argument("--x", type=float, default=190.0)
    parser.add_argument("--y", type=float, default=420.0)
    parser.add_argument("--facing", type=int, choices=(-1, 1), default=1)
    parser.add_argument("--offset-x", type=int, default=37)
    parser.add_argument("--offset-y", type=int, default=24)
    args = parser.parse_args()
    result = Suwako418Oracle(args.exe).run(args.x, args.y, args.facing, args.offset_x, args.offset_y)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Suwako action 418: captured object 808 spawn; output={args.output}")


if __name__ == "__main__":
    main()
