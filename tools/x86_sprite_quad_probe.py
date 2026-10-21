#!/usr/bin/env python3
"""Recover the pinned PE's PAT-frame to sprite-quad field mapping."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
FIELD_READ_SITES = {
    0x0C: 0x00468134,
    0x0E: 0x00468145,
    0x10: 0x00468156,
    0x12: 0x00468167,
    0x04: 0x00468178,
    0x06: 0x00468189,
    0x08: 0x0046819A,
    0x14: 0x004681AB,
}


def probe(path: Path) -> dict[str, object]:
    image = path.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected PE SHA-256: {digest}")
    pe = pefile.PE(data=image, fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = False

    def window(address: int, size: int) -> dict[int, tuple[str, str]]:
        data = pe.get_data(address - pe.OPTIONAL_HEADER.ImageBase, size)
        return {ins.address: (ins.mnemonic, ins.op_str)
                for ins in decoder.disasm(data, address)}

    loader = window(0x00468100, 0xB8)
    for field, address in FIELD_READ_SITES.items():
        mnemonic, operands = loader.get(address, (None, ""))
        expected_operand = f"[esi + {field}]" if field < 10 else f"[esi + 0x{field:x}]"
        if mnemonic != "lea" or expected_operand not in operands:
            raise ValueError(f"PAT loader field +{field:x} no longer matches its pinned read site")
    init = window(0x00466720, 0x80)
    if init.get(0x00466766) != ("movsx", "eax, word ptr [esi + 4]"):
        raise ValueError("Sprite initialization no longer sign-extends frame +4")
    if init.get(0x0046677E) != ("movsx", "edx, word ptr [esi + 6]"):
        raise ValueError("Sprite initialization no longer sign-extends frame +6")
    if init.get(0x00466778) != ("fstp", "dword ptr [ecx + 0xf0]"):
        raise ValueError("Frame +4 is no longer copied to component +0xf0")
    if init.get(0x00466790) != ("fstp", "dword ptr [eax + 0xf4]"):
        raise ValueError("Frame +6 is no longer copied to component +0xf4")
    geometry = window(0x00406D30, 0x40)
    if geometry.get(0x00406D40) != ("fdiv", "dword ptr [ecx + 0x78]"):
        raise ValueError("Source rectangle right edge is no longer normalized by texture width")
    if geometry.get(0x00406D53) != ("fdiv", "dword ptr [ecx + 0x7c]"):
        raise ValueError("Source rectangle bottom edge is no longer normalized by texture height")

    return {
        "sha256": digest,
        "disk_frame_fields": {
            "image": "+0x00 (word within the initial 4-byte selector field)",
            "tx": "+0x04", "ty": "+0x06", "tw": "+0x08", "th": "+0x0a",
            "ox": "+0x0c", "oy": "+0x0e", "duration": "+0x10", "flags": "+0x12",
        },
        "runtime_frame_offsets_read_by_loader": {
            f"+0x{field:02x}": f"0x{address:08x}" for field, address in FIELD_READ_SITES.items()
        },
        "resolved_semantics": {
            "runtime_plus_0x04_plus_0x06": "PAT ox/oy; sign-extended into sprite component +0xf0/+0xf4",
            "runtime_plus_0x0c_through_0x12": "PAT tx/ty/tw/th; source rectangle passed to texture-quad setup",
            "draw_origin": "x = world_x - facing*ox; y = -world_y - oy; camera transform follows",
        },
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original" / "th123.exe")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = probe(args.exe)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
