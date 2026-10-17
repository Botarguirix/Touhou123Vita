#!/usr/bin/env python3
"""Disassemble selected VA windows from the hash-pinned TH123 PE32 image."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--window", action="append", required=True,
                        help="VA:length in hex; repeat for multiple windows")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.exe.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"reference SHA256 mismatch: {digest}")
    pe = pefile.PE(data=raw)
    base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    rows = [f"# sha256={digest}", "address\tbytes\tmnemonic\toperands"]
    for spec in args.window:
        start_text, length_text = spec.split(":", 1)
        start, length = int(start_text, 16), int(length_text, 16)
        rows.append(f"# window={start:08x}:{length:x}")
        code = pe.get_data(start - base, length)
        rows.extend(f"{ins.address:08x}\t{ins.bytes.hex(' ')}\t{ins.mnemonic}\t{ins.op_str}"
                    for ins in md.disasm(code, start))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({digest})")


if __name__ == "__main__":
    main()
