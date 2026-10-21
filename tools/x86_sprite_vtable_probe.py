#!/usr/bin/env python3
"""Verify the player/object sprite draw slot in the pinned TH123 PE."""
import hashlib
import json
import struct
from pathlib import Path

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
IMAGE_BASE = 0x00400000
TABLES = {
    "reimu_player": 0x0085BF4C,
    "base_object": 0x0085F1D4,
    "suwako_object": 0x0085F22C,
}
RENDER_SLOT = 11
RENDER_TARGET = 0x00438D20


def probe(path: Path) -> dict[str, object]:
    image = path.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected PE SHA-256: {digest}")
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    if image[pe:pe + 4] != b"PE\0\0":
        raise ValueError("Invalid PE signature")
    section_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    base = struct.unpack_from("<I", image, pe + 24 + 28)[0]
    section_table = pe + 24 + optional_size
    sections = []
    for index in range(section_count):
        offset = section_table + index * 40
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", image, offset + 8
        )
        sections.append((virtual_address, min(max(virtual_size, raw_size), raw_size), raw_offset))

    def read_va(address: int, size: int) -> bytes:
        rva = address - base
        for virtual_address, raw_size, raw_offset in sections:
            if virtual_address <= rva and rva + size <= virtual_address + raw_size:
                start = raw_offset + rva - virtual_address
                return image[start:start + size]
        raise ValueError(f"Address is not backed by PE data: {address:#x}")

    results = {}
    for name, table in TABLES.items():
        target = struct.unpack("<I", read_va(table + RENDER_SLOT * 4, 4))[0]
        results[name] = {"vtable": f"0x{table:08x}", "slot": RENDER_SLOT,
                         "target": f"0x{target:08x}"}
        if target != RENDER_TARGET:
            raise ValueError(f"{name} render slot points to {target:#x}")
    return {"sha256": digest, "render_target": f"0x{RENDER_TARGET:08x}",
            "shared_render_slot": True, "tables": results}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path,
                        default=Path(__file__).resolve().parents[1] / "original" / "th123.exe")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = probe(args.exe)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
