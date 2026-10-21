#!/usr/bin/env python3
"""Execute the pinned PE's sprite-component constructor on controlled crops."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local" / "python-deps"))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
CTOR = 0x00406C60
TEXTURE_SIZE_LOOKUP = 0x00405200
STOP = 0x03000000
COMPONENT = 0x01000000
TEXTURE = 0x01100000
STACK = 0x02000000


def execute(exe: Path, tx: int, ty: int, width: int, height: int,
            texture_width: int, texture_height: int) -> dict[str, object]:
    raw = exe.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected PE SHA-256: {digest}")
    pe = pefile.PE(data=raw)
    base = pe.OPTIONAL_HEADER.ImageBase
    image = pe.get_memory_mapped_image()
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(base, (len(image) + 4095) & ~4095)
    uc.mem_write(base, image)
    for address, size in ((COMPONENT, 0x1000), (STACK, 0x10000), (STOP, 0x1000)):
        uc.mem_map(address, size)

    def intercept_texture_size(machine: Uc, address: int, _size: int, _user: object) -> None:
        if address != TEXTURE_SIZE_LOOKUP:
            return
        sp = machine.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", machine.mem_read(sp, 4))[0]
        width_ptr, height_ptr = struct.unpack("<II", machine.mem_read(sp + 8, 8))
        machine.mem_write(width_ptr, struct.pack("<I", texture_width))
        machine.mem_write(height_ptr, struct.pack("<I", texture_height))
        machine.reg_write(UC_X86_REG_ESP, sp + 16)  # callee pops three arguments
        machine.reg_write(UC_X86_REG_EIP, ret)

    uc.hook_add(UC_HOOK_CODE, intercept_texture_size)
    args = (STOP, TEXTURE, tx & 0xFFFFFFFF, ty & 0xFFFFFFFF,
            width & 0xFFFFFFFF, height & 0xFFFFFFFF, 0, 0)
    for index, value in enumerate(args):
        uc.mem_write(STACK + 0xFF00 + index * 4, struct.pack("<I", value))
    uc.reg_write(UC_X86_REG_ECX, COMPONENT)
    uc.reg_write(UC_X86_REG_ESP, STACK + 0xFF00)
    uc.emu_start(CTOR, STOP, count=10000)
    if uc.reg_read(UC_X86_REG_EIP) != STOP:
        raise RuntimeError("Original sprite-component constructor did not return")

    def f32(offset: int) -> float:
        return struct.unpack("<f", uc.mem_read(COMPONENT + offset, 4))[0]

    return {
        "input": {"tx": tx, "ty": ty, "width": width, "height": height,
                  "texture_width": texture_width, "texture_height": texture_height},
        "uv_edges": {"left": f32(0x1C), "top": f32(0x20),
                     "right": f32(0x38), "bottom": f32(0x74)},
        "local_quad": {"top_left": [f32(0x80), f32(0x84)],
                       "top_right": [f32(0x8C), f32(0x90)],
                       "bottom_left": [f32(0x98), f32(0x9C)],
                       "bottom_right": [f32(0xA4), f32(0xA8)]},
    }


def probe(exe: Path) -> dict[str, object]:
    samples = [
        execute(exe, 0, 0, 128, 128, 256, 256),
        execute(exe, 12, 24, 64, 32, 256, 256),
        execute(exe, 100, 90, 32, 48, 512, 256),
    ]
    for sample in samples:
        i, q, uv = sample["input"], sample["local_quad"], sample["uv_edges"]
        if q["top_right"] != [float(i["width"]), 0.0] or q["bottom_left"] != [0.0, float(i["height"])]:
            raise ValueError(f"PE quad dimensions do not match PAT width/height: {sample}")
        expected_uv = [i["tx"] / i["texture_width"], i["ty"] / i["texture_height"],
                       (i["tx"] + i["width"]) / i["texture_width"],
                       (i["ty"] + i["height"]) / i["texture_height"]]
        observed_uv = [uv["left"], uv["top"], uv["right"], uv["bottom"]]
        if any(abs(a - b) > 1e-6 for a, b in zip(observed_uv, expected_uv)):
            raise ValueError(f"PE UV edges do not match origin + dimensions: {sample}")
    return {
        "schema": 1,
        "reference_sha256": EXPECTED_SHA256,
        "constructor": "0x00406c60",
        "external_texture_size_lookup": "0x00405200 intercepted with controlled dimensions",
        "conclusion": "PAT tw/th are quad width/height; UV end is (tx+tw, ty+th) normalized by texture dimensions",
        "samples": samples,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path("original/th123.exe"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = probe(args.exe)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
