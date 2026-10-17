#!/usr/bin/env python3
"""Extract character input virtual targets from the pinned TH123 PE image."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import struct
from pathlib import Path

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
PLAYABLE = (
    "Reimu", "Marisa", "Sakuya", "Alice", "Patchouli", "Youmu", "Remilia",
    "Yuyuko", "Yukari", "Suika", "Udonge", "Aya", "Komachi", "Iku",
    "Tenshi", "Sanae", "Chirno", "Meirin", "Utsuho", "Suwako",
)
KNOWN_HANDLERS = {"Reimu": 0x004AE670, "Chirno": 0x006FB8B0, "Remilia": 0x0059C010}


def extract(exe: Path, player_cpp: Path) -> tuple[str, list[dict[str, str]]]:
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected TH123 executable SHA-256: {digest}")

    source = player_cpp.read_text(encoding="utf-8")
    entries = re.findall(
        r"const int _vtable_info<v2::Player(\w+)>::baseAddr\s*=\s*(0x[0-9a-fA-F]+);",
        source,
    )
    tables = dict(entries)
    if len(tables) != len(entries):
        raise ValueError("Duplicate vtable names in SokuLib Player.cpp")
    missing = sorted(set(PLAYABLE) - tables.keys())
    if missing:
        raise ValueError(f"Missing playable vtables: {', '.join(missing)}")

    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    section_count = struct.unpack_from("<H", data, pe_offset + 6)[0]
    optional_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    optional = pe_offset + 24
    if struct.unpack_from("<H", data, optional)[0] != 0x10B:
        raise ValueError("Expected a PE32 image")
    image_base = struct.unpack_from("<I", data, optional + 28)[0]

    sections: list[tuple[int, int, int]] = []
    section_table = optional + optional_size
    for index in range(section_count):
        offset = section_table + index * 40
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from(
            "<IIII", data, offset + 8
        )
        backed_size = min(max(virtual_size, raw_size), raw_size)
        sections.append((virtual_address, backed_size, raw_pointer))

    def read_va(address: int, size: int) -> bytes:
        rva = address - image_base
        for virtual_address, backed_size, raw_pointer in sections:
            if virtual_address <= rva and rva + size <= virtual_address + backed_size:
                start = raw_pointer + rva - virtual_address
                if start + size <= len(data):
                    return data[start : start + size]
        raise ValueError(f"VA {address:08x} is not backed by PE section bytes")

    rows: list[dict[str, str]] = []
    for character in PLAYABLE:
        table = int(tables[character], 16)
        handler = struct.unpack("<I", read_va(table + 20 * 4, 4))[0]
        motion = struct.unpack("<I", read_va(table + 21 * 4, 4))[0]
        if not 0x00401000 <= handler < 0x00857000:
            raise ValueError(f"{character}: slot-20 target {handler:08x} is outside .text")
        if character in KNOWN_HANDLERS and handler != KNOWN_HANDLERS[character]:
            raise ValueError(
                f"{character}: expected handler {KNOWN_HANDLERS[character]:08x}, got {handler:08x}"
            )
        rows.append(
            {
                "sha256": digest,
                "character": character,
                "vtable_va": f"{table:08x}",
                "slot": "20",
                "handleInputs_va": f"{handler:08x}",
                "checkAllMotionInputs_va": f"{motion:08x}",
                "status": "ok",
            }
        )
    if len({row["handleInputs_va"] for row in rows}) != len(PLAYABLE):
        raise ValueError("Playable characters do not have unique slot-20 handlers")
    return digest, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path, help="Local th123.exe matching the pinned hash")
    parser.add_argument("player_cpp", type=Path, help="SokuLib Player.cpp with vtable addresses")
    parser.add_argument("output", type=Path, help="Output TSV path")
    args = parser.parse_args()

    digest, rows = extract(args.exe, args.player_cpp)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"sha256={digest}; playable_handlers={len(rows)}; output={args.output}")


if __name__ == "__main__":
    main()
