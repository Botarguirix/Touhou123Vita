#!/usr/bin/env python3
"""Disassemble reachable basic blocks for character input handlers in a PE32."""

from __future__ import annotations

import argparse
import csv
import hashlib
import struct
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))

import capstone

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


def disassemble(exe: Path, handler_map: Path, output: Path, max_span: int = 0x4000) -> int:
    image = exe.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected TH123 executable SHA-256: {digest}")
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    sections_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    optional = pe + 24
    if struct.unpack_from("<H", image, optional)[0] != 0x10B:
        raise ValueError("Expected a PE32 image")
    base = struct.unpack_from("<I", image, optional + 28)[0]
    sec_table = optional + optional_size
    sections: list[tuple[int, int, int]] = []
    for i in range(sections_count):
        off = sec_table + i * 40
        name = image[off : off + 8].split(b"\0")[0].decode("ascii", "replace")
        vs, va, rs, rp = struct.unpack_from("<IIII", image, off + 8)
        sections.append((va, min(max(vs, rs), rs), rp))

    def file_offset(va: int) -> int:
        rva = va - base
        for va0, size, raw in sections:
            if va0 <= rva < va0 + size:
                return raw + rva - va0
        raise ValueError(f"VA {va:08x} is not inside initialized section data")

    rows: list[tuple[str, int]] = []
    with handler_map.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if row["sha256"] != digest:
                raise ValueError("Handler map belongs to a different executable")
            rows.append((row["character"], int(row["handleInputs_va"], 16)))

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    output.mkdir(parents=True, exist_ok=True)
    count = 0
    for character, start in rows:
        pending = deque([start])
        visited: set[int] = set()
        instructions: dict[int, str] = {}
        while pending:
            address = pending.popleft()
            if address in visited or abs(address - start) > max_span:
                continue
            visited.add(address)
            off = file_offset(address)
            code = image[off : min(off + 15, len(image))]
            decoded = next(md.disasm(code, address, count=1), None)
            if decoded is None:
                continue
            instructions[address] = f"{address:08x}\t{decoded.mnemonic}\t{decoded.op_str}"
            next_address = address + decoded.size
            if decoded.group(capstone.CS_GRP_RET) or decoded.mnemonic in {"int3", "ud2"}:
                continue
            if decoded.group(capstone.CS_GRP_CALL):
                pending.append(next_address)
                continue
            if decoded.group(capstone.CS_GRP_JUMP):
                target = None
                if decoded.operands and decoded.operands[0].type == capstone.x86.X86_OP_IMM:
                    target = int(decoded.operands[0].imm) & 0xFFFFFFFF
                if decoded.mnemonic != "jmp":
                    pending.append(next_address)
                if target is not None and abs(target - start) <= max_span:
                    pending.append(target)
                continue
            pending.append(next_address)

        path = output / f"{start:08x}.asm.tsv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            stream.write(f"# sha256={digest}\tcharacter={character}\tentry={start:08x}\tmax_span={max_span:x}\n")
            stream.write("address\tmnemonic\toperands\n")
            for address in sorted(instructions):
                stream.write(instructions[address] + "\n")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("handler_map", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--max-span", type=lambda value: int(value, 0), default=0x4000)
    args = parser.parse_args()
    count = disassemble(args.exe, args.handler_map, args.output_dir, args.max_span)
    print(f"handlers={count}; output={args.output_dir}")


if __name__ == "__main__":
    main()
