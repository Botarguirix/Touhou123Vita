#!/usr/bin/env python3
"""Resolve and execute Remilia's original action-412 initializer body."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile
from unicorn.x86_const import (UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESI,
                               UC_X86_REG_ESP)
from tools.x86_suwako_808_factory_probe import (
    LIST, STACK, STOP, Suwako808FactoryProbe,
)

EXE = ROOT / "original/th123.exe"
ACTION = 412
ACTION_MAP = 0x0059B380
INIT_JUMP_TABLE = 0x0059B32C
OBJECT = LIST + 0x8000


def read_va(pe: pefile.PE, va: int, size: int) -> bytes:
    return pe.get_data(va - pe.OPTIONAL_HEADER.ImageBase, size)


def initializer_for_action(exe: Path, action: int) -> tuple[int, int, int]:
    pe = pefile.PE(data=exe.read_bytes())
    index = action - 0xD9
    if not 0 <= index <= 0xC9:
        raise ValueError(f"action {action} outside initializer map range")
    group = read_va(pe, ACTION_MAP + index, 1)[0]
    target = struct.unpack("<I", read_va(pe, INIT_JUMP_TABLE + group * 4, 4))[0]
    return index, group, target


def run(exe: Path, dat_dir: Path) -> dict[str, object]:
    index, group, init_va = initializer_for_action(exe, ACTION)
    if init_va != 0x0059AD64:
        raise ValueError(f"action 412 initializer changed: {init_va:#x}")

    probe = Suwako808FactoryProbe(exe, dat_dir)
    uc = probe.uc
    uc.mem_write(OBJECT, bytes(0x1000))
    # Nonzero sentinels prove the initializer changed each documented field.
    fields = {0x190: struct.pack("<I", 0x11223344),
              0x7D0: struct.pack("<H", 0x1111),
              0x7D2: struct.pack("<H", 0x2222),
              0x7D6: struct.pack("<H", 0x3333),
              0x7D8: struct.pack("<H", 0x4444),
              0xF4: struct.pack("<f", 1.0),
              0xF8: struct.pack("<f", 2.0),
              0xFC: struct.pack("<f", 3.0),
              0x100: struct.pack("<f", 4.0)}
    for offset, value in fields.items():
        uc.mem_write(OBJECT + offset, value)

    # The action table jumps into a shared initializer body after its prologue;
    # recreate the saved-register/return stack expected by its epilogue.
    sp = STACK + 0xB000 - 12
    uc.mem_write(sp, struct.pack("<3I", 0xA0A0A0A0, 0xB0B0B0B0, STOP))
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_ECX, OBJECT)
    uc.reg_write(UC_X86_REG_ESI, OBJECT)
    uc.reg_write(UC_X86_REG_EIP, init_va)
    uc.emu_start(init_va, STOP, count=10000)
    if uc.reg_read(UC_X86_REG_EIP) != STOP:
        raise RuntimeError(f"initializer did not return: EIP={uc.reg_read(UC_X86_REG_EIP):#x}")

    values = {
        "state_190": struct.unpack("<I", uc.mem_read(OBJECT + 0x190, 4))[0],
        "counter_7d0": struct.unpack("<H", uc.mem_read(OBJECT + 0x7D0, 2))[0],
        "counter_7d2": struct.unpack("<H", uc.mem_read(OBJECT + 0x7D2, 2))[0],
        "counter_7d6": struct.unpack("<H", uc.mem_read(OBJECT + 0x7D6, 2))[0],
        "counter_7d8": struct.unpack("<H", uc.mem_read(OBJECT + 0x7D8, 2))[0],
        "position_f4_f8_fc_100": [struct.unpack("<f", uc.mem_read(OBJECT + off, 4))[0]
                                  for off in (0xF4, 0xF8, 0xFC, 0x100)],
    }
    expected = {"state_190": 0, "counter_7d0": 0, "counter_7d2": 0,
                "counter_7d6": 0, "counter_7d8": 0,
                "position_f4_f8_fc_100": [0.0, 0.0, 0.0, 0.0]}
    if values != expected:
        raise AssertionError(f"initializer outputs differ: {values}")
    return {
        "action": ACTION, "map_index": index, "dispatch_group": group,
        "initializer_va": hex(init_va), "executed_helpers": ["0x4636b0"],
        "outputs": values,
        "scope": "The PE action map and jump table resolve 412 to 0x59ad64; that original body and its original 0x4636b0 helper execute in Unicorn with controlled object memory. This verifies initializer effects only; it does not execute the full character update or a fight.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dat_dir", nargs="?", type=Path, default=ROOT / "original")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(EXE, args.dat_dir)
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
