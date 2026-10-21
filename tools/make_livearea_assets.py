#!/usr/bin/env python3
"""Generate indexed-PNG LiveArea placeholders required to install the VPK."""
from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

TEMPLATE = '''<?xml version="1.0" encoding="utf-8"?>

<livearea style="a1" format-ver="01.00" content-rev="1">
\t<livearea-background>
\t\t<image>bg.png</image>
\t</livearea-background>
\n+\t<gate>
\t\t<startup-image>startup.png</startup-image>
\t</gate>
</livearea>
'''


def _chunk(tag: bytes, data: bytes) -> bytes:
    body = tag + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))


def write_indexed_png(path: Path, width: int, height: int,
                      start: tuple[int, int, int], end: tuple[int, int, int]) -> None:
    palette = b"".join(bytes(int(start[k] + (end[k] - start[k]) * i / 63)
                             for k in range(3)) for i in range(64))
    rows = []
    for y in range(height):
        index = min(63, y * 64 // height)
        rows.append(b"\0" + bytes([index]) * width)
    header = struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", header) +
           _chunk(b"PLTE", palette) +
           _chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) +
           _chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def generate(root: Path) -> None:
    images = (
        (root / "icon0.png", 128, 128, (30, 60, 120), (10, 20, 50)),
        (root / "livearea/contents/bg.png", 840, 500, (20, 40, 90), (5, 10, 30)),
        (root / "livearea/contents/startup.png", 280, 158, (70, 110, 200), (30, 50, 120)),
    )
    for path, width, height, start, end in images:
        write_indexed_png(path, width, height, start, end)
    template = root / "livearea/contents/template.xml"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(TEMPLATE, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sce_sys", type=Path)
    args = parser.parse_args()
    generate(args.sce_sys)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
