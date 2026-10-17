#!/usr/bin/env python3
"""Probe original Suwako 808 setAction/PAT sequence with a synthetic PAT map.

The original x86 executes action assignment, setSequence, pose selection and
the action initializer. PAT metadata, heap contents, renderer, RNG and trig
helpers are controlled inputs; this is not the game factory or a gameplay run.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
BASE = 0x01000000
MAP = 0x01100000
NIL = 0x01101000
ACTION_NODE = 0x01102000
SEQUENCE_0 = 0x01103000
SEQUENCE_1 = 0x01104000
FRAME_0 = 0x01105000
FRAME_1 = 0x01106000
CUSTOM = 0x01107000
STACK = 0x02000000
STOP = 0x03000000
TEXTURES = 0x01020000
CTOR_HEAP = 0x01200000


def u32(uc: Uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def u16(uc: Uc, address: int) -> int:
    return struct.unpack("<H", uc.mem_read(address, 2))[0]


def f32(uc: Uc, address: int) -> float:
    return struct.unpack("<f", uc.mem_read(address, 4))[0]


class Suwako808ActionProbe:
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
        for address, size in ((BASE, 0x10000), (MAP, 0x10000),
                              (CTOR_HEAP, 0x10000), (STACK, 0x10000), (STOP, 0x1000)):
            self.uc.mem_map(address, size)
        self.uc.mem_map(0, 0x1000)  # x86 FS:[0] exception-chain storage
        self.uc.mem_write(STOP, b"\xf4")
        self.logs: list[dict[str, object]] = []
        self.allocations: list[dict[str, object]] = []
        self.heap_cursor = CTOR_HEAP
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _return(self, esp: int, cleanup: int = 0) -> None:
        uc = self.uc
        target = u32(uc, esp)
        uc.reg_write(UC_X86_REG_ESP, esp + 4 + cleanup)
        uc.reg_write(UC_X86_REG_EIP, target)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address == STOP:
            uc.emu_stop()
            return
        esp = uc.reg_read(UC_X86_REG_ESP)
        if address == 0x0081FBDC:
            # Controlled zeroed storage for the constructor's 12-byte list
            # sentinels. 81fbdc is cdecl; its caller removes the size arg.
            size = u32(uc, esp + 4)
            ptr = (self.heap_cursor + 0xF) & ~0xF
            self.heap_cursor = ptr + size + 0x10
            uc.mem_write(ptr, bytes(size))
            self.allocations.append({"size": size, "address": hex(ptr), "zeroed": True})
            uc.reg_write(UC_X86_REG_EAX, ptr)
            self._return(esp)
        elif address == 0x0043A250:
            obj = uc.reg_read(UC_X86_REG_ECX)
            self.logs.append({
                "event": "PAT_frame_render_setup",
                "action": u16(uc, obj + 0x13C),
                "sequence": u16(uc, obj + 0x13E),
                "pose": u16(uc, obj + 0x140),
                "render_color_hex": bytes(uc.mem_read(obj + 0x110, 4)).hex(),
                "frame_pointer": hex(u32(uc, obj + 0x150)),
            })
            self._return(esp)
        elif address in (0x004095F0, 0x00409580):
            angle = struct.unpack("<f", uc.mem_read(esp + 4, 4))[0]
            value = math.sin(math.radians(angle if address == 0x004095F0 else angle - 90.0))
            stub, output = STOP + 0x100, STOP + 0x200
            uc.mem_write(stub, b"\xd9\x05" + struct.pack("<I", output) + b"\xc3")
            uc.mem_write(output, struct.pack("<f", value))
            uc.reg_write(UC_X86_REG_EIP, stub)
        elif address == 0x004099F0:
            # Deterministic value zero, cdecl: the original caller cleans args.
            uc.reg_write(UC_X86_REG_EAX, 0)
            self._return(esp)

    def run(self, custom_data: tuple[float, float, float] = (-20.0, 12.0, 1.0),
            initial_color: int | None = None) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(BASE, bytes(0x4000))
        self.heap_cursor = CTOR_HEAP
        self.allocations.clear()
        ctor_sp = STACK + 0x7000
        uc.mem_write(ctor_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESP, ctor_sp)
        uc.reg_write(UC_X86_REG_ECX, BASE)
        uc.reg_write(UC_X86_REG_EIP, 0x00783A70)  # original Suwako object constructor
        uc.emu_start(0x00783A70, STOP, count=100000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"Suwako constructor did not return: EIP={uc.reg_read(UC_X86_REG_EIP):#x}")
        constructor_color = bytes(uc.mem_read(BASE + 0x110, 4)).hex()
        uc.mem_write(BASE, struct.pack("<I", 0x0085F22C))  # factory installs derived vtable
        uc.mem_write(BASE + 0x130, struct.pack("<I", TEXTURES))
        uc.mem_write(BASE + 0x160, struct.pack("<I", MAP))
        uc.mem_write(BASE + 0x35C, struct.pack("<I", CUSTOM))
        if initial_color is not None:
            uc.mem_write(BASE + 0x110, struct.pack("<I", initial_color))
        uc.mem_write(BASE + 0x104, b"\x01")
        uc.mem_write(BASE + 0x0EC, struct.pack("<f", 300.0))
        uc.mem_write(BASE + 0x0F0, struct.pack("<f", 400.0))
        uc.mem_write(CUSTOM, struct.pack("<3f", *custom_data))

        # MSVC ordered-map sentinel and one action=808 entry. Each sequence is
        # a linked node with a PAT-like frame vector (stride 0xA8).
        uc.mem_write(MAP + 4, struct.pack("<I", NIL))
        uc.mem_write(MAP + 8, struct.pack("<I", 1))
        uc.mem_write(NIL, struct.pack("<III", ACTION_NODE, ACTION_NODE, ACTION_NODE))
        uc.mem_write(NIL + 0x15, b"\x01")
        uc.mem_write(ACTION_NODE, struct.pack("<III", NIL, NIL, NIL))
        uc.mem_write(ACTION_NODE + 0x0C, struct.pack("<I", 808))
        uc.mem_write(ACTION_NODE + 0x10, struct.pack("<I", SEQUENCE_0))
        for seq, frame, count in ((SEQUENCE_0, FRAME_0, 10), (SEQUENCE_1, FRAME_1, 1)):
            uc.mem_write(seq + 4, struct.pack("<II", frame, frame + count * 0xA8))
            uc.mem_write(seq + 0x10, b"\x01")  # loop flag from PAT
        uc.mem_write(SEQUENCE_0 + 0x18, struct.pack("<I", SEQUENCE_1))
        uc.mem_write(SEQUENCE_0 + 0x1C, struct.pack("<I", SEQUENCE_1))
        uc.mem_write(SEQUENCE_1 + 0x18, struct.pack("<I", SEQUENCE_0))
        uc.mem_write(SEQUENCE_1 + 0x1C, struct.pack("<I", SEQUENCE_0))
        uc.mem_write(FRAME_0 + 8, struct.pack("<H", 2))
        uc.mem_write(FRAME_1 + 8, struct.pack("<H", 10))
        self.logs.clear()

        entry_sp = STACK + 0x8000
        uc.mem_write(entry_sp, struct.pack("<II", STOP, 808))
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_ECX, BASE)
        uc.reg_write(UC_X86_REG_EIP, 0x00464930)  # original GameObject::setAction
        uc.emu_start(0x00464930, STOP, count=100000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"setAction did not return: EIP={uc.reg_read(UC_X86_REG_EIP):#x}")
        return {
            "reference_sha256": self.sha256,
            "action": u16(uc, BASE + 0x13C),
            "sequence": u16(uc, BASE + 0x13E),
            "current_sequence": hex(u32(uc, BASE + 0x15C)),
            "render_color_hex": bytes(uc.mem_read(BASE + 0x110, 4)).hex(),
            "render_alpha": uc.mem_read(BASE + 0x113, 1)[0],
            "velocity": [f32(uc, BASE + 0xF4), f32(uc, BASE + 0xF8)],
            "frame_pointer": hex(u32(uc, BASE + 0x150)),
            "constructor_render_color_hex": constructor_color,
            "frame_logs": self.logs,
            "controlled": {
                "object_storage_zeroed_before_original_constructor": True,
                "object_constructor": "original 0x783a70 executes; allocator 0x81fbdc returns controlled zeroed list sentinels",
                "constructor_allocations": self.allocations,
                "PAT_map": "synthetic action 808 with 10 frames in seq.0 and 1 frame in seq.1",
                "frame_durations": [2, 10],
                "renderer_callback": "skipped at 0x43a250 after recording object/frame state",
                "trig": "math.sin service supplied to original x86 initializer",
                "rng": "returns zero",
                "object_pool_factory_and_lifetime": "not executed",
            },
        }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/x86-suwako-808-action-probe.json")
    args = parser.parse_args()
    result = Suwako808ActionProbe(args.exe).run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Suwako 808 setAction probe: action={result['action']} seq={result['sequence']} alpha={result['render_alpha']}")


if __name__ == "__main__":
    main()
