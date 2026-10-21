#!/usr/bin/env python3
"""Extract replay dispatch, word-consumption, and frame-sync evidence from TH123 PE32."""
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
from capstone.x86 import X86_OP_IMM  # noqa: E402

ORIGINAL_2009_SHA256 = "24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3"
INPUT_DECODER = 0x0042A410
PEEK_WORD = 0x0045BC50
CONSUME_WORD = 0x0042A3A0
WORD_AT_INDEX = 0x0042EA50
INPUT_SETTER = 0x0043CC80
MODE_GETTER = 0x0043CED0
REPLAY_CURSOR_GLOBAL = 0x0085D748
SYNC_METHOD = 0x0045FE96
UPDATE_METHODS = (0x0047EE10, 0x00481040)
VTABLE_SLOTS = (0x00821924, 0x0082196C, 0x008219D4)


def analyze(exe_path: Path) -> dict[str, object]:
    raw = exe_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ORIGINAL_2009_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {digest}")
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True

    def instructions(start: int, length: int) -> list[dict[str, object]]:
        code = pe.get_data(start - base, length)
        result = []
        for ins in decoder.disasm(code, start):
            immediate = None
            if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
                immediate = ins.operands[0].imm & 0xFFFFFFFF
            result.append({"va": f"0x{ins.address:08x}", "mnemonic": ins.mnemonic,
                           "operands": ins.op_str, "call_target":
                           f"0x{immediate:08x}" if immediate is not None else None})
        return result

    method_windows = {f"0x{va:08x}": instructions(va, 0x200) for va in UPDATE_METHODS}
    sync_method = instructions(SYNC_METHOD, 0x300)
    method_calls = {
        name: [ins["call_target"] for ins in rows if ins["call_target"]]
        for name, rows in method_windows.items()
    }
    sync_calls = [ins["call_target"] for ins in sync_method if ins["call_target"]]
    sync_text = "\n".join(f"{ins['va']}: {ins['mnemonic']} {ins['operands']}"
                           for ins in sync_method).lower()

    # Locate data pointers by VA, not by raw file offset. These are table slots
    # in the PE data section and distinguish callback entries, not runtime calls.
    vtable_refs: dict[str, list[str]] = {}
    expected_vtable_targets = (0x00481040, 0x0047EE10, 0x00481040)
    for slot, expected in zip(VTABLE_SLOTS, expected_vtable_targets):
        off = pe.get_offset_from_rva(slot - base)
        value = struct.unpack_from("<I", raw, off)[0]
        vtable_refs[f"0x{slot:08x}"] = [f"0x{value:08x}"]

    # Verify the original method's indexed read, two setter IDs, and one-step
    # cursor increment in the relevant local code region.
    method = method_windows["0x00481040"]
    compact = [(str(ins["mnemonic"]), str(ins["operands"])) for ins in method]
    relevant = [ins for ins in method if int(str(ins["va"]), 16) >= 0x00481065]
    method_targets = {ins["call_target"] for ins in relevant}
    method_operands = "\n".join(f"{mn} {ops}" for mn, ops in compact)
    checks = {
        "both_methods_call_decoder_in_mode_2": all(
            INPUT_DECODER in [int(t, 16) for t in calls if t]
            for calls in method_calls.values()),
        "indexed_reader_reached_by_481040": f"0x{WORD_AT_INDEX:08x}" in method_targets,
        "setter_reached_by_481040": f"0x{INPUT_SETTER:08x}" in method_targets,
        "cursor_index_increment_present": "add dword ptr [eax + 0x14], 1" in method_operands,
        "setter_ids_0x3c_and_0x3d_present": "push 0x3c" in method_operands and "push 0x3d" in method_operands,
        "frame_sync_peeks_and_consumes": PEEK_WORD in [int(t, 16) for t in sync_calls if t]
        and CONSUME_WORD in [int(t, 16) for t in sync_calls if t],
        "frame_sync_compares_against_global_word": "cmp word ptr [0x85eb58], si" in sync_text,
        "frame_sync_returns_on_counter_mismatch": "0045ff3c: jne 0x45fe70" in sync_text,
        "vtable_slots_reference_the_two_methods": all(
            struct.unpack_from("<I", raw, pe.get_offset_from_rva(slot - base))[0] == expected
            for slot, expected in zip(VTABLE_SLOTS, expected_vtable_targets)),
    }
    if not all(checks.values()):
        raise RuntimeError(f"PE replay dispatch contract mismatch: {checks}")
    return {
        "schema": 1,
        "exe_sha256": digest,
        "profile": "provided-original-2009",
        "mode_getter_va": f"0x{MODE_GETTER:08x}",
        "decoder_va": f"0x{INPUT_DECODER:08x}",
        "methods": method_windows,
        "frame_sync_method": sync_method,
        "vtable_slots": vtable_refs,
        "checks": checks,
        "finding": {
            "per_invocation": "0x481040 reads one uint16 at replay-cursor index +0x14, maps flags 0x4000/0x2000 to input IDs 0x3c/0x3d, and increments the index once on its guarded path.",
            "frame_sync": "The Story update path peeks the current word in its packed vector and compares it with [0x85eb58]. On mismatch it branches to the method epilogue without consuming; on equality it consumes one word and updates input state. This is conditional synchronization, not a busy wait.",
            "limit": "Static control flow establishes conditional per-invocation advancement, not how often the sync method runs per simulation/rendered frame or which active branch every match mode reaches.",
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
