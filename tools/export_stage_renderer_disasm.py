#!/usr/bin/env python3
"""Export stage renderer instruction windows from the SHA-pinned TH123 PE."""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))
import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

EXPECTED = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
RENDERERS = ((0x4757A0, 0x710, "BG36"),
             (0x4762C0, 0x6D0, "BG37"),
             (0x476D60, 0x5B0, "BG38"))


def main():
    exe = ROOT / "original" / "th123.exe"
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED:
        raise SystemExit(f"Unexpected TH123 PE SHA-256: {digest}")
    pe = pefile.PE(data=data, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    rows = [f"# PE sha256={digest}", "stage\trenderer\tbytes\tmnemonic\toperands"]
    for stage, (va, size, _) in zip(("BG36", "BG37", "BG38"), RENDERERS):
        code = pe.get_data(va - pe.OPTIONAL_HEADER.ImageBase, size)
        for ins in md.disasm(code, va):
            rows.append(f"{stage}\t{ins.address:08x}\t{ins.bytes.hex(' ')}\t{ins.mnemonic}\t{ins.op_str}")
    out = ROOT / "artifacts" / "kernel" / digest / "stage-layout" / "renderers-disasm.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Exported {len(rows)-2} instructions to {out}")


if __name__ == "__main__":
    main()
