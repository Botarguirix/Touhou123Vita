#!/usr/bin/env python3
"""Find direct field references reachable from PE32 vtable methods.

This lightweight CFG walker follows direct branches and direct calls. It does
not resolve jump tables, virtual calls, or computed field addresses; findings
are candidates that still need code/data and semantic review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
sys.path.insert(0, str(ROOT / "local" / "python-deps"))

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_JUMP, CS_GRP_RET
from capstone.x86 import X86_OP_IMM, X86_OP_MEM


def scan(exe: Path, vtable: int, slots: int, displacement: int) -> dict[str, object]:
    image = exe.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"reference PE SHA-256 mismatch: {digest}")
    pe = pefile.PE(data=image, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    def executable(va: int) -> bool:
        if va < base:
            return False
        section = pe.get_section_by_rva(va - base)
        return bool(section and section.Characteristics & 0x20000000)

    table = pe.get_data(vtable - base, slots * 4)
    roots = list(struct.unpack("<" + "I" * slots, table))
    queue = deque((entry, slot, (f"slot{slot}@{entry:08x}",))
                  for slot, entry in enumerate(roots) if executable(entry))
    visited_functions: set[int] = set()
    references: dict[tuple[int, int, str, str], list[str]] = {}
    decoded = 0

    while queue and len(visited_functions) < 10000:
        entry, slot, chain = queue.popleft()
        if entry in visited_functions:
            continue
        visited_functions.add(entry)
        pending_blocks = [entry]
        visited_in_function: set[int] = set()
        while pending_blocks and decoded < 500000:
            pc = pending_blocks.pop()
            while pc not in visited_in_function and executable(pc):
                instruction_bytes = pe.get_data(pc - base, 15)
                instruction = next(md.disasm(instruction_bytes, pc, count=1), None)
                if instruction is None:
                    break
                visited_in_function.add(pc)
                decoded += 1
                for operand in instruction.operands:
                    if operand.type == X86_OP_MEM and (operand.mem.disp & 0xFFFFFFFF) == displacement:
                        key = (entry, instruction.address, instruction.mnemonic, instruction.op_str)
                        references.setdefault(key, list(chain))

                if instruction.mnemonic == "call":
                    if instruction.operands and instruction.operands[0].type == X86_OP_IMM:
                        target = instruction.operands[0].imm & 0xFFFFFFFF
                        if executable(target) and target not in visited_functions:
                            queue.append((target, slot, chain + (f"call@{instruction.address:08x}",)))
                    pc = instruction.address + instruction.size
                    continue
                if instruction.group(CS_GRP_RET):
                    break
                if instruction.mnemonic == "jmp":
                    if instruction.operands and instruction.operands[0].type == X86_OP_IMM:
                        pending_blocks.append(instruction.operands[0].imm & 0xFFFFFFFF)
                    break
                if instruction.group(CS_GRP_JUMP) and instruction.operands and instruction.operands[0].type == X86_OP_IMM:
                    pending_blocks.append(instruction.operands[0].imm & 0xFFFFFFFF)
                pc = instruction.address + instruction.size

    return {
        "exe_sha256": digest,
        "vtable": f"0x{vtable:08x}",
        "slots_requested": slots,
        "executable_roots": sum(executable(value) for value in roots),
        "direct_call_reachable_functions": len(visited_functions),
        "decoded_instructions": decoded,
        "field_displacement": f"0x{displacement:x}",
        "references": [
            {"entry": f"0x{entry:08x}", "pc": f"0x{pc:08x}",
             "mnemonic": mnemonic, "instruction": op_str, "call_chain": chain}
            for (entry, pc, mnemonic, op_str), chain in sorted(references.items())
        ],
        "limitations": ["direct branches and direct calls only", "does not resolve jump tables or indirect calls/jumps",
                        "does not detect computed addresses or prove field semantics"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original" / "th123.exe")
    parser.add_argument("--vtable", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--slots", type=int, default=48)
    parser.add_argument("--field", type=lambda value: int(value, 0), required=True,
                        help="memory displacement to search, e.g. 0x884")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = scan(args.exe, args.vtable, args.slots, args.field)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
