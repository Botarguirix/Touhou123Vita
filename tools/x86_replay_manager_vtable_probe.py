#!/usr/bin/env python3
"""Resolve replay-related callback slots to TH123 battle-manager RTTI classes."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile  # noqa: E402
from capstone import CS_ARCH_X86, CS_MODE_32, Cs  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG  # noqa: E402

ORIGINAL_2009_SHA256 = "24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3"
SLOT_OFFSET = 0x40
MANAGERS = {
    0x008218E4: {
        "name": "CBattleManager",
        "slot5_target": 0x00481690,
        "slot_target": 0x00481040,
        "bases": ("CBattleManager", "CBattleManagerBase", "Environment"),
        "constructors": (0x0043784B,),
    },
    0x0082192C: {
        "name": "CBattleManagerStory",
        "slot5_target": 0x0047F810,
        "slot_target": 0x0047EE10,
        "bases": ("CBattleManagerStory", "CBattleManagerBase", "Environment"),
        "constructors": (0x00437918, 0x0043B488),
    },
    0x00821994: {
        "name": "CBattleManagerArcade",
        "slot5_target": 0x00481690,
        "slot_target": 0x00481040,
        "bases": ("CBattleManagerArcade", "CBattleManager", "CBattleManagerBase", "Environment"),
        "constructors": (0x00438A4E,),
    },
}


def analyze(exe_path: Path) -> dict[str, object]:
    raw = exe_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ORIGINAL_2009_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {digest}")
    pe = pefile.PE(data=raw, fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True

    def u32(va: int) -> int:
        off = pe.get_offset_from_rva(va - image_base)
        return struct.unpack_from("<I", raw, off)[0]

    def type_name(type_descriptor: int) -> str:
        off = pe.get_offset_from_rva(type_descriptor - image_base)
        name = raw[off + 8:off + 8 + 160].split(b"\0", 1)[0]
        if not name.startswith(b".?AV") or not name.endswith(b"@@"):
            raise ValueError(f"unexpected MSVC type descriptor at 0x{type_descriptor:08x}")
        return name[4:-2].decode("ascii")

    def slot16_dispatch(method_va: int) -> str | None:
        code = pe.get_data(method_va - image_base, 0x100)
        instructions = list(decoder.disasm(code, method_va))
        for i in range(len(instructions) - 2):
            load_vtable, load_slot, call_slot = instructions[i:i + 3]
            if (load_vtable.mnemonic != "mov" or len(load_vtable.operands) < 2 or
                    load_vtable.operands[0].type != X86_OP_REG or
                    load_vtable.operands[1].type != X86_OP_MEM):
                continue
            if (load_slot.mnemonic != "mov" or len(load_slot.operands) < 2 or
                    load_slot.operands[0].type != X86_OP_REG or
                    load_slot.operands[1].type != X86_OP_MEM or
                    load_slot.operands[1].mem.disp != SLOT_OFFSET or
                    load_slot.operands[1].mem.base != load_vtable.operands[0].reg):
                continue
            if (call_slot.mnemonic == "call" and call_slot.operands and
                    call_slot.operands[0].type == X86_OP_REG and
                    call_slot.operands[0].reg == load_slot.operands[0].reg):
                return f"0x{load_slot.address:08x}"
        return None

    managers: dict[str, dict[str, object]] = {}
    checks: dict[str, bool] = {}
    for vtable, spec in MANAGERS.items():
        col = u32(vtable - 4)
        col_fields = [u32(col + offset) for offset in (0, 4, 8, 12, 16)]
        descriptor_type = type_name(col_fields[3])
        hierarchy = col_fields[4]
        base_count = u32(hierarchy + 8)
        base_array = u32(hierarchy + 12)
        bases = tuple(type_name(u32(u32(base_array + i * 4))) for i in range(base_count))
        slot_address = vtable + SLOT_OFFSET
        slot_target = u32(slot_address)
        slot5_target = u32(vtable + 5 * 4)
        dispatch_callsite = slot16_dispatch(slot5_target)

        constructor_rows = []
        for address in spec["constructors"]:
            encoded = pe.get_data(address - image_base, 6)
            instructions = list(decoder.disasm(encoded, address))
            valid = (len(instructions) == 1 and instructions[0].mnemonic == "mov" and
                     instructions[0].operands[0].type != X86_OP_IMM and
                     instructions[0].operands[1].type == X86_OP_IMM and
                     (instructions[0].operands[1].imm & 0xFFFFFFFF) == vtable)
            constructor_rows.append({"va": f"0x{address:08x}", "bytes": encoded.hex(" "), "writes_vtable": valid})

        key = f"{descriptor_type}_0x{vtable:08x}"
        checks[f"{key}_rtti_name_matches"] = descriptor_type == spec["name"]
        checks[f"{key}_base_hierarchy_matches"] = bases == spec["bases"]
        checks[f"{key}_slot_5_matches"] = slot5_target == spec["slot5_target"]
        checks[f"{key}_slot_16_matches"] = slot_target == spec["slot_target"]
        checks[f"{key}_slot_5_dispatches_slot_16"] = dispatch_callsite is not None
        checks[f"{key}_constructors_write_vtable"] = all(row["writes_vtable"] for row in constructor_rows)
        managers[key] = {
            "vtable_va": f"0x{vtable:08x}",
            "class": descriptor_type,
            "base_classes": list(bases),
            "slot_5_target": f"0x{slot5_target:08x}",
            "slot_5_dispatches_slot_16_at": dispatch_callsite,
            "slot_index": SLOT_OFFSET // 4,
            "slot_va": f"0x{slot_address:08x}",
            "slot_target": f"0x{slot_target:08x}",
            "constructors": constructor_rows,
        }

    if not all(checks.values()):
        raise RuntimeError(f"battle manager vtable contract mismatch: {checks}")

    return {
        "schema": 1,
        "exe_sha256": digest,
        "profile": "provided-original-2009",
        "managers": managers,
        "checks": checks,
        "finding": {
            "dispatch": "The base and Arcade battle-manager vtables point slot 16 to 0x481040; the Story subclass overrides that same slot with 0x47ee10.",
            "scope": "RTTI, vtable entries, and constructor writes identify class-specific dispatch. They do not prove which manager instance a particular replay session constructs, its update cadence, or that a slot cannot be reached through another object/call path.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True, help="compatible original 2009 th123.exe")
    parser.add_argument("--output", type=Path, help="write JSON report")
    args = parser.parse_args()
    report = analyze(args.exe)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
