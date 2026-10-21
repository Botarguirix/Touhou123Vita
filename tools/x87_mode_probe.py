#!/usr/bin/env python3
"""Inventario reproducible del modo x87 y flags D3D9 del PE fijado."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
sys.path.insert(0, str(ROOT / "local/python-deps"))
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX,
                              UC_X86_REG_EDI, UC_X86_REG_ESI,
                              UC_X86_REG_ESP, UC_X86_REG_EIP,
                              UC_X86_REG_FPCW, UC_X86_REG_MXCSR)


def load_pe(path):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"reference SHA256 mismatch: {digest}")
    return pefile.PE(data=raw)


def cw_fields(word):
    return {"word": word, "pc": (word >> 8) & 3,
            "significand_bits": {0: 24, 2: 53, 3: 64}.get((word >> 8) & 3),
            "rc": (word >> 10) & 3}


def device_case(pe, failures=0, boolean_argument=True):
    """Ejecuta las tres rutas originales; solo sustituye el COM externo.

    No carga D3D9 ni simula su cambio del control word. Se observan argumentos,
    no el estado efectivo de la FPU de un proceso Windows.
    """
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    base = pe.OPTIONAL_HEADER.ImageBase
    uc.mem_map(base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
    uc.mem_write(base, pe.get_memory_mapped_image())
    iface, table, callback, stack = 0x1000000, 0x1001000, 0x1002000, 0x2000000
    uc.mem_map(iface, 0x3000)
    uc.mem_map(stack, 0x10000)
    uc.mem_write(iface, struct.pack("<I", table))
    uc.mem_write(table + 0x40, struct.pack("<I", callback))
    uc.mem_write(0x8A0E2C, struct.pack("<I", iface))
    uc.reg_write(UC_X86_REG_ESP, stack + 0x8000)
    uc.reg_write(UC_X86_REG_EAX, 480)
    uc.reg_write(UC_X86_REG_ESI, 0x1234)
    uc.reg_write(UC_X86_REG_EDI, 640)
    uc.reg_write(UC_X86_REG_EBX, int(boolean_argument))
    calls = []

    def hook(machine, address, size, data):
        if address in (0x41508F, 0x415071):
            machine.emu_stop()
        elif address == callback:
            sp = machine.reg_read(UC_X86_REG_ESP)
            words = struct.unpack("<8I", machine.mem_read(sp, 32))
            ret, this, adapter, device_type, hwnd, flags, params, output = words
            if this != iface or params != 0x8A0F68 or output != 0x8A0E30:
                raise ValueError("unexpected CreateDevice ABI")
            calls.append({"call_va": ret - 2, "return_va": ret,
                          "adapter": adapter, "device_type": device_type,
                          "hwnd": hwnd, "behavior_flags": flags,
                          "fpu_preserve": bool(flags & 2),
                          "windowed": struct.unpack("<I", machine.mem_read(params + 32, 4))[0]})
            machine.reg_write(UC_X86_REG_EAX,
                              0x80004005 if len(calls) <= failures else 0)
            machine.reg_write(UC_X86_REG_ESP, sp + 32)
            machine.reg_write(UC_X86_REG_EIP, ret)

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.emu_start(0x414FA2, 0x415090, count=500)
    stop = uc.reg_read(UC_X86_REG_EIP)
    expected = 0x415071 if failures == 3 else 0x41508F
    if stop != expected or len(calls) != min(failures + 1, 3):
        raise RuntimeError(f"incomplete device fragment: {stop:#x}")
    return {"failures": failures, "boolean_argument": boolean_argument,
            "stop_va": stop, "calls": calls}


def controlfp_case(pe, initial_cw, new, mask):
    """Ejecuta _controlfp_s y su CRT real con SSE desactivado explícitamente."""
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    base = pe.OPTIONAL_HEADER.ImageBase
    uc.mem_map(base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
    uc.mem_write(base, pe.get_memory_mapped_image())
    arena = 0x2000000
    uc.mem_map(arena, 0x10000)
    stop, output, sp = arena + 0x1000, arena + 0x2000, arena + 0x8000
    uc.mem_write(sp, struct.pack("<4I", stop, output, new, mask))
    uc.mem_write(0x8A1144, struct.pack("<II", 0, 0))
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_FPCW, initial_cw)
    uc.reg_write(UC_X86_REG_MXCSR, 0x1F80)
    uc.emu_start(0x82198E, stop, count=10000)
    if uc.reg_read(UC_X86_REG_EIP) != stop:
        raise RuntimeError("incomplete CRT controlfp probe")
    return {"initial_cw": initial_cw, "new": new, "mask": mask,
            "final_cw": uc.reg_read(UC_X86_REG_FPCW),
            "errno_result": uc.reg_read(UC_X86_REG_EAX),
            "abstract_output": struct.unpack("<I", uc.mem_read(output, 4))[0],
            "sse_enabled": False}


def canonical(operand):
    return re.sub(r"^(?:byte|word|dword|qword|xword) ptr ", "", operand)


def trace_word(ins, index, operand, depth=0):
    """Slice local conservador: no es un análisis de flujo entre bloques.

    Devuelve la procedencia de un slot o registro solo para escrituras simples.
    Las ramas se conservan en el contexto; la clasificación es una inferencia.
    """
    if depth > 8:
        return {"kind": "unresolved"}
    operand = canonical(operand)
    if re.fullmatch(r"(?:0x[0-9a-f]+|[0-9]+)", operand):
        return {"kind": "constant", "word": int(operand, 0) & 0xFFFF}
    for j in range(index - 1, max(-1, index - 160), -1):
        a, _, mnemonic, op = ins[j]
        if mnemonic == "int3":
            break
        parts = op.split(", ", 1)
        dest = canonical(parts[0])
        if dest != operand:
            continue
        if mnemonic == "fnstcw":
            return {"kind": "saved_cw", "save_va": a}
        if mnemonic in ("mov", "movzx") and len(parts) == 2:
            return trace_word(ins, j, parts[1], depth + 1)
        if mnemonic in ("or", "and") and len(parts) == 2:
            try:
                mask = int(parts[1], 0) & 0xFFFF
            except ValueError:
                return {"kind": "unresolved"}
            source = trace_word(ins, j, operand, depth + 1)
            return {"kind": "masked", "operation": mnemonic, "mask": mask,
                    "operation_va": a, "source": source}
        # Reads do not overwrite a source. Unsupported writes stay unresolved.
        if mnemonic in ("cmp", "test", "fldcw", "fld", "fild", "push"):
            continue
        return {"kind": "unresolved", "write_va": a}
    return {"kind": "unresolved"}


def classify(source):
    if source["kind"] == "saved_cw":
        return "restore_saved"
    if source["kind"] == "constant":
        return "constant"
    if source["kind"] == "masked" and source["source"]["kind"] == "saved_cw":
        mask = source["mask"]
        if source["operation"] == "or":
            if mask == 0xC00:
                return "round_toward_zero_pc_preserved"
            if mask in (0x300, 0x33F):
                return "extended_precision_64"
    return "unresolved"


def inventory(pe, functions_path=None):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    functions = []
    if functions_path and Path(functions_path).is_file():
        with Path(functions_path).open(encoding="utf-8") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                functions.append((int(row["entry"], 16), row["name"], int(row["bytes"])))
    rows, crt_refs, reset_rows = [], [], []
    crt_entries = {0x82198E: "_controlfp_s", 0x82C962: "_control87",
                   0x82D67C: "_ctrlfp (raw CW helper)"}
    for section in pe.sections:
        if not section.Characteristics & 0x20000000:
            continue
        ins = list(md.disasm_lite(section.get_data(),
                                 pe.OPTIONAL_HEADER.ImageBase + section.VirtualAddress))
        for i, (address, _, mnemonic, op) in enumerate(ins):
            if mnemonic in ("call", "jmp"):
                try:
                    target = int(op, 0)
                except ValueError:
                    target = None
                if target in crt_entries:
                    crt_refs.append({"va": address, "kind": mnemonic,
                                     "target_va": target, "target": crt_entries[target],
                                     "context": ins[max(0, i-8):i]})
            if mnemonic in ("finit", "fninit", "frstor", "fxrstor"):
                reset_rows.append({"va": address, "instruction": mnemonic, "operand": op})
            if mnemonic != "fldcw":
                continue
            source = trace_word(ins, i, op)
            absolute = re.fullmatch(r"word ptr \[(0x[0-9a-f]+)\]", op)
            if absolute:
                va = int(absolute[1], 16)
                source = {"kind": "constant", "source_va": va,
                          "word": struct.unpack("<H", pe.get_data(va - pe.OPTIONAL_HEADER.ImageBase, 2))[0]}
            owners = [{"entry": a, "name": name} for a, name, size in functions
                      if a <= address < a + size]
            rows.append({"va": address, "operand": op, "source": source,
                         "classification": classify(source),
                         "ghidra_range_candidates": owners,
                         "confidence": "local_static_slice_not_cfg_proof",
                         "context": ins[max(0, i-10):i+2]})
    return {"linear_fldcw_count": len(rows),
            "classification_counts": dict(sorted(Counter(r["classification"] for r in rows).items())),
            "fldcw": rows, "crt_control_references": crt_refs,
            "other_state_loads": reset_rows,
            "scope": "Linear census includes embedded data; local slices and Ghidra byte ranges are not function/CFG proof."}


def report(exe=ROOT / "original/th123.exe"):
    pe = load_pe(exe)
    functions = ROOT / "artifacts/pe-inventory" / EXPECTED_SHA256 / "functions.tsv"
    result = {"schema": 1, "sha256": EXPECTED_SHA256,
              "direct3d_create9": {"iat_va": 0x8572A0, "thunk_va": 0x81F6B8,
                                    "call_va": 0x414EF0, "interface_global_va": 0x8A0E2C,
                                    "device_global_va": 0x8A0E30},
              "device_cases": [device_case(pe, n, mode)
                               for mode in (False, True) for n in range(4)],
              "controlfp_cases": [controlfp_case(pe, cw, new, mask)
                                  for cw in (0x7F, 0x27F, 0x37F)
                                  for new, mask in ((0, 0), (0x200, 0x300), (0x20000, 0x30000))],
              "d3d_runtime_control_word_measured": False,
              "recommendation": "mixed: per-thread CW and rounding; D3D default 24-bit is insufficient: game controlfp sets RC up, CRT uses 53/64-bit paths; validate replay equivalence"}
    result.update(inventory(pe, functions))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "artifacts/pe-inventory" / EXPECTED_SHA256 / "x87-mode.json")
    args = parser.parse_args()
    result = report(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    print(json.dumps(result["classification_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
