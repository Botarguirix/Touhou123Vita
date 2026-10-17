"""Find direct x86 CALL references in an exact PE32 reference image.

Capstone performs a linear sweep over executable PE sections. Results are
instruction-level candidates; embedded code/data interleaving can still cause
false positives, so use Ghidra xrefs to confirm before changing runtime code.
"""
import argparse
import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
sys.path.insert(0, str(ROOT / "local" / "python-deps"))

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=ROOT / "original" / "th123.exe")
    parser.add_argument("--target", action="append", default=None,
                        help="target VA as hex (repeatable; defaults to 0x00489610 and 0x0043f2f0)")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "move-lock-callers.tsv")
    parser.add_argument("--window", help="also print disassembly from VA:LENGTH, both values in hex")
    parser.add_argument("--quiet", action="store_true", help="suppress the list of direct-call references")
    parser.add_argument("--field", action="append", default=None,
                        help="also list instructions with a memory displacement (hex; repeatable)")
    args = parser.parse_args()
    image_sha256 = hashlib.sha256(args.exe.read_bytes()).hexdigest()
    if image_sha256 != EXPECTED_SHA256:
        raise SystemExit(f"Reference SHA256 mismatch: {image_sha256}; expected {EXPECTED_SHA256}")
    targets = {int(value, 16) for value in (args.target or ["00489610", "0043f2f0"])}

    pe = pefile.PE(str(args.exe), fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    rows = []
    field_refs = []
    fields = {int(value, 16) for value in (args.field or [])}
    executable_sections = 0
    for section in pe.sections:
        if not (section.Characteristics & 0x20000000):
            continue
        executable_sections += 1
        start = image_base + section.VirtualAddress
        code = section.get_data()[:section.Misc_VirtualSize or section.SizeOfRawData]
        for insn in md.disasm(code, start):
            if fields and insn.id != 0 and any(op.type == X86_OP_MEM and
                              (op.mem.disp & 0xffffffff) in fields for op in insn.operands):
                field_refs.append(insn)
            if insn.mnemonic != "call" or not insn.operands:
                continue
            op = insn.operands[0]
            if op.type != X86_OP_IMM or op.imm not in targets:
                continue
            rows.append({
                "target": f"{op.imm & 0xffffffff:08X}",
                "callsite": f"{insn.address:08X}",
                "section": section.Name.rstrip(b"\0").decode("ascii", "replace"),
                "file_offset": f"{section.PointerToRawData + insn.address - start:08X}",
                "bytes": insn.bytes.hex(" ").upper(),
                "instruction": f"{insn.mnemonic} {insn.op_str}",
            })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else
                                ["target", "callsite", "section", "file_offset", "bytes", "instruction"],
                                delimiter="\t")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: (row["target"], row["callsite"])))
    print(f"Reference SHA256={image_sha256}; PE32 imagebase=0x{image_base:08X}; executable sections={executable_sections}; "
          f"decoded direct-call candidates={len(rows)}")
    if not args.quiet:
        for row in sorted(rows, key=lambda item: (item["target"], item["callsite"])):
            print(f"{row['target']} <- {row['callsite']} [{row['bytes']}] {row['instruction']}")
    print(f"TSV: {args.output}")
    if args.window:
        address_text, length_text = args.window.split(":", 1)
        address, length = int(address_text, 16), int(length_text, 16)
        data = pe.get_data(address - image_base, length)
        print(f"\nDisassembly window 0x{address:08X} ({len(data)} bytes):")
        for insn in md.disasm(data, address):
            print(f"{insn.address:08X}: {insn.bytes.hex(' ').upper():<30} {insn.mnemonic} {insn.op_str}")
    if fields:
        print("\nField displacement references:")
        for insn in field_refs:
            print(f"{insn.address:08X}: {insn.bytes.hex(' ').upper():<30} {insn.mnemonic} {insn.op_str}")


if __name__ == "__main__":
    main()
