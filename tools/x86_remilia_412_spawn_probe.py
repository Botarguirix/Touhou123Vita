#!/usr/bin/env python3
"""Capture the original Remilia 412 state-4 spawn callsite under Unicorn.

The callsite instructions and callback-table lookup execute from the pinned PE.
Entry into the state-4 basic block, player state, callback table, and external
object manager are controlled fixtures; this is not a natural fight trace.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "local/python-deps"))

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EIP,
    UC_X86_REG_ESP, UC_X86_REG_ESI,
)
from tools.x86_suwako_808_factory_probe import LIST, OWNER, STACK, STOP, Suwako808FactoryProbe

HANDLER_STATE4 = 0x0058CD2B
CREATE_OBJECT_WRAPPER = 0x0046EB30
CALLBACK_LOOKUP = 0x00464980
CALLBACK_DISPATCH = 0x00401D50
HANDLER_EPILOGUE = 0x0058CDCC
PLAYER = LIST + 0x8000
CALLBACKS = OWNER + 0x100
CALLBACK_INDEX = 3
SPAWN_RETURN = STOP + 0x100
CALLBACK_RETURN = STOP + 0x110


def u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def f32(uc, address: int) -> float:
    return struct.unpack("<f", uc.mem_read(address, 4))[0]


def run_case(dat_dir: Path, x: float, y: float, facing: int, callback_index: int) -> dict[str, object]:
    probe = Suwako808FactoryProbe(ROOT / "original/th123.exe", dat_dir)
    uc = probe.uc
    uc.mem_write(PLAYER, bytes(0x1000))
    uc.mem_write(CALLBACKS, bytes(0x500))
    uc.mem_write(PLAYER + 0x164, struct.pack("<I", CALLBACKS))
    uc.mem_write(PLAYER + 0x13C, struct.pack("<H", 412))
    uc.mem_write(PLAYER + 0x13E, struct.pack("<H", 0))
    uc.mem_write(PLAYER + 0x140, struct.pack("<H", 4))
    uc.mem_write(PLAYER + 0x142, struct.pack("<H", 0))
    uc.mem_write(PLAYER + 0x104, struct.pack("<b", facing))
    uc.mem_write(PLAYER + 0xEC, struct.pack("<f", x))
    uc.mem_write(PLAYER + 0xF0, struct.pack("<f", y))
    uc.mem_write(PLAYER + 0x49E, struct.pack("<H", 1000))
    uc.mem_write(PLAYER + 0x4C8, struct.pack("<I", 0))
    uc.mem_write(PLAYER + 0x54C, struct.pack("<f", 1.0))
    uc.mem_write(PLAYER + 0x5E4, struct.pack("<H", 0))
    uc.mem_write(CALLBACKS + callback_index * 4, struct.pack("<I", 0x12345678))

    # State-4 block has a 0x288-byte local frame. We stop at its epilogue so
    # the harness need not invent the parent dispatcher's saved-register frame.
    entry_sp = STACK + 0xC000
    spawn: dict[str, object] = {}
    callback: dict[str, object] = {}
    errors: list[str] = []

    def hook(machine, address: int, _size: int, _user: object) -> None:
        esp = machine.reg_read(UC_X86_REG_ESP)
        if address == CREATE_OBJECT_WRAPPER:
            words = struct.unpack("<8I", machine.mem_read(esp, 32))
            ptr = words[6]
            spawn.update({
                "return_address": hex(words[0]),
                "arguments_raw": [hex(v) for v in words[1:]],
                "object_id": words[1],
                "x": struct.unpack("<f", struct.pack("<I", words[2]))[0],
                "y": struct.unpack("<f", struct.pack("<I", words[3]))[0],
                "facing": words[4],
                "callback_index_argument": words[5],
                "temporary_float_block": list(struct.unpack("<3f", machine.mem_read(ptr, 12))),
                "temporary_float_count": words[7],
            })
            machine.reg_write(UC_X86_REG_EAX, 0x0BADF00D)  # controlled manager result
            machine.reg_write(UC_X86_REG_ESP, esp + 32)  # ret 0x1c
            machine.reg_write(UC_X86_REG_EIP, words[0])
        elif address == CALLBACK_DISPATCH:
            callback_pointer = u32(machine, esp + 4)
            callback.update({
                "dispatcher": hex(address),
                "index": callback_index,
                "table_pointer": hex(u32(machine, PLAYER + 0x164)),
                "selected_function_pointer": hex(callback_pointer),
                "action": struct.unpack("<H", machine.mem_read(PLAYER + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", machine.mem_read(PLAYER + 0x13E, 2))[0],
                "substate": struct.unpack("<H", machine.mem_read(PLAYER + 0x140, 2))[0],
            })
            ret = u32(machine, esp)
            machine.reg_write(UC_X86_REG_ESP, esp + 8)  # callback dispatch ret 4
            machine.reg_write(UC_X86_REG_EAX, 0)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == HANDLER_EPILOGUE:
            machine.emu_stop()
        elif address == 0x0047A9E0:
            # Preserve state setup and arithmetic while skipping the real
            # resource/meter side effect outside this isolated spawn probe.
            ret = u32(machine, esp)
            machine.reg_write(UC_X86_REG_ESP, esp + 12)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == 0x00487870:
            ret = u32(machine, esp)
            machine.reg_write(UC_X86_REG_ESP, esp + 8)
            machine.reg_write(UC_X86_REG_EIP, ret)

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.mem_write(entry_sp, struct.pack("<I", STOP))
    uc.reg_write(UC_X86_REG_ESP, entry_sp)
    uc.reg_write(UC_X86_REG_EBX, callback_index)
    uc.reg_write(UC_X86_REG_ECX, PLAYER)
    uc.reg_write(UC_X86_REG_ESI, PLAYER)
    uc.reg_write(UC_X86_REG_EIP, HANDLER_STATE4)
    try:
        uc.emu_start(HANDLER_STATE4, STOP, count=10000)
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}")
    if not spawn:
        raise RuntimeError(f"original handler block did not request object 801: {errors}")
    if not callback:
        raise RuntimeError(f"original indexed callback did not dispatch: {errors}")
    return {
        "input_fixture": {"position": [x, y], "facing": facing,
                          "action": 412, "sequence": 0, "substate": 4,
                          "callback_index_fixture": callback_index},
        "spawn_call": spawn,
        "callback_dispatch": callback,
        "error": errors or None,
        "scope": "Original state-4 callsite instructions and original 0x464980 callback-table lookup execute from the hash-pinned PE. Entry state and EBX are fixtures; the object manager return and callback dispatcher are controlled boundaries. Does not prove natural reachability, instantiate/update 801, run collision, or apply damage.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dat-dir", type=Path, default=ROOT / "original")
    parser.add_argument("--x", type=float, default=320.0)
    parser.add_argument("--y", type=float, default=180.0)
    parser.add_argument("--facing", type=int, choices=(-1, 1), default=1)
    parser.add_argument("--callback-index", type=int, choices=(0, 1, 2, 3), default=CALLBACK_INDEX)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/x86-remilia-412-spawn-probe.json")
    args = parser.parse_args()
    result = run_case(args.dat_dir, args.x, args.y, args.facing, args.callback_index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
