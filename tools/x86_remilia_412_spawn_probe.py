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
    UC_X86_REG_ESP, UC_X86_REG_ESI, UC_X86_REG_EBP, UC_X86_REG_EDI,
)
from tools.x86_remilia_412_box_sync_probe import effective_pat
from tools.x86_remilia_412_action_setter_probe import (
    ACTION_SETTER, ACTION_WRITE, RESET_SEQUENCE, INITIALIZE_ACTION,
    INITIALIZER_BODY, ZERO_MOTION, PAT_LOOKUP, MAP_RESULT, MAP_OBJECT,
    MAP_NODE, SEQUENCE_NODE, FRAME_DATA, SET_POSE_CAPTURE,
)
from tools.x86_suwako_808_factory_probe import LIST, OWNER, PAT_MAP, STACK, STOP, Suwako808FactoryProbe

MAIN_ACTION_COMPARE = 0x00587BAB
CREATE_OBJECT_WRAPPER = 0x0046EB30
CALLBACK_DISPATCH = 0x00401D50
HANDLER_EPILOGUE = 0x0058CDCC
PLAYER = LIST + 0x8000
CALLBACKS = OWNER + 0x100


def initialize_action_412(probe: Suwako808FactoryProbe, dat_dir: Path) -> dict[str, object]:
    """Run the original setter/initializer chain and controlled PAT lookup."""
    _archive, _digest, frames = effective_pat(dat_dir)
    uc = probe.uc
    uc.mem_write(PLAYER, bytes(0x1000))
    uc.mem_write(OWNER, bytes(0x100))
    for address, size in ((MAP_RESULT, 0x100), (MAP_OBJECT, 0x100),
                          (MAP_NODE, 0x100), (SEQUENCE_NODE, 0x100),
                          (FRAME_DATA, len(frames) * 0xA8)):
        uc.mem_write(address, bytes(size))
    uc.mem_write(PLAYER, struct.pack("<I", OWNER))
    uc.mem_write(OWNER + 2 * 4, struct.pack("<I", ACTION_SETTER))
    uc.mem_write(OWNER + 4 * 4, struct.pack("<I", RESET_SEQUENCE))
    uc.mem_write(OWNER + 7 * 4, struct.pack("<I", SET_POSE_CAPTURE))
    uc.mem_write(OWNER + 15 * 4, struct.pack("<I", INITIALIZE_ACTION))
    uc.mem_write(PLAYER + 0x160, struct.pack("<I", PAT_MAP + 0x7000))
    uc.mem_write(MAP_RESULT, struct.pack("<II", MAP_OBJECT, MAP_NODE))
    uc.mem_write(MAP_OBJECT + 4, struct.pack("<I", MAP_NODE + 0x100))
    uc.mem_write(MAP_NODE + 0x10, struct.pack("<I", SEQUENCE_NODE))
    uc.mem_write(SEQUENCE_NODE + 4,
                 struct.pack("<II", FRAME_DATA, FRAME_DATA + len(frames) * 0xA8))
    uc.mem_write(SEQUENCE_NODE + 0x14, b"\x00")
    for index, frame in enumerate(frames):
        uc.mem_write(FRAME_DATA + index * 0xA8 + 8, struct.pack("<H", int(frame["duration"])))
    uc.mem_write(SEQUENCE_NODE + 0x1C, struct.pack("<I", SEQUENCE_NODE))

    reached: list[str] = []
    def setup_hook(machine, address: int, _size: int, _user: object) -> None:
        if address in (ACTION_SETTER, ACTION_WRITE, RESET_SEQUENCE,
                       INITIALIZE_ACTION, INITIALIZER_BODY, ZERO_MOTION):
            reached.append(hex(address))
        esp = machine.reg_read(UC_X86_REG_ESP)
        if address == PAT_LOOKUP:
            ret = u32(machine, esp)
            machine.reg_write(UC_X86_REG_EAX, MAP_RESULT)
            machine.reg_write(UC_X86_REG_ESP, esp + 12)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == SET_POSE_CAPTURE:
            ret, pose = struct.unpack("<II", machine.mem_read(esp, 8))
            machine.mem_write(PLAYER + 0x140, struct.pack("<H", pose))
            machine.reg_write(UC_X86_REG_ESP, esp + 8)
            machine.reg_write(UC_X86_REG_EIP, ret)

    uc.hook_add(UC_HOOK_CODE, setup_hook)
    sp = STACK + 0xB000
    uc.mem_write(sp, struct.pack("<II", STOP, 412))
    uc.reg_write(UC_X86_REG_ECX, PLAYER)
    uc.reg_write(UC_X86_REG_ESI, PLAYER)
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_EIP, ACTION_SETTER)
    uc.emu_start(ACTION_SETTER, STOP, count=100000)
    state = {
        "action": struct.unpack("<H", uc.mem_read(PLAYER + 0x13C, 2))[0],
        "sequence": struct.unpack("<H", uc.mem_read(PLAYER + 0x13E, 2))[0],
        "pose": struct.unpack("<H", uc.mem_read(PLAYER + 0x140, 2))[0],
        "pose_count": struct.unpack("<H", uc.mem_read(PLAYER + 0x148, 2))[0],
        "initializer_chain": reached,
    }
    if (state["action"], state["sequence"], state["pose"], state["pose_count"]) != (412, 0, 0, len(frames)):
        raise AssertionError(f"original action setter did not initialize 412/seq0: {state}")

    advanced: list[int] = []
    for _ in range(4):
        sp = STACK + 0xB100
        uc.mem_write(sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESP, sp)
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_EIP, 0x00464B70)  # Remilia vtable slot 8: advance pose
        uc.emu_start(0x00464B70, STOP, count=10000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"original pose advance failed at {uc.reg_read(UC_X86_REG_EIP):#x}")
        advanced.append(struct.unpack("<H", uc.mem_read(PLAYER + 0x140, 2))[0])
    if advanced != [1, 2, 3, 4]:
        raise AssertionError(f"unexpected original pose progression: {advanced}")
    state["original_pose_advances"] = advanced
    return state


def u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def run_case(dat_dir: Path, x: float, y: float, facing: int, callback_index: int) -> dict[str, object]:
    probe = Suwako808FactoryProbe(ROOT / "original/th123.exe", dat_dir)
    uc = probe.uc
    initialized_action = initialize_action_412(probe, dat_dir)
    uc.mem_write(CALLBACKS, bytes(0x500))
    uc.mem_write(PLAYER + 0x164, struct.pack("<I", CALLBACKS))
    # The original vtable pose-advance method has already reached pose 4.
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
    original_helpers: list[str] = []
    dispatch_trace: list[str] = []

    def hook(machine, address: int, _size: int, _user: object) -> None:
        esp = machine.reg_read(UC_X86_REG_ESP)
        if address in (MAIN_ACTION_COMPARE, 0x0058A3A1, 0x0058CCE7):
            dispatch_trace.append(hex(address))
        if address in (0x0047A9E0, 0x00487870, 0x00820230):
            original_helpers.append(hex(address))
        if address in (0x00487CA0, 0x00438C60):
            ret = u32(machine, esp)
            if address == 0x00438C60:
                machine.reg_write(UC_X86_REG_EAX, 0)  # external status query: false
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
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
                "index": machine.reg_read(UC_X86_REG_EBX),
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

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.mem_write(entry_sp, struct.pack("<I", STOP))
    uc.reg_write(UC_X86_REG_ESP, entry_sp)
    uc.reg_write(UC_X86_REG_EBX, 1)  # established at 0x5879cf in the main update prologue
    uc.reg_write(UC_X86_REG_EBP, 0)
    uc.reg_write(UC_X86_REG_EDI, 0)
    uc.reg_write(UC_X86_REG_ECX, PLAYER)
    uc.reg_write(UC_X86_REG_ESI, PLAYER)
    uc.reg_write(UC_X86_REG_EIP, MAIN_ACTION_COMPARE)
    try:
        uc.emu_start(MAIN_ACTION_COMPARE, STOP, count=10000)
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}")
    if not spawn:
        raise RuntimeError(f"original handler block did not request object 801: {errors}")
    if not callback:
        raise RuntimeError(f"original indexed callback did not dispatch: {errors}")
    return {
        "initialized_action": initialized_action,
        "input_fixture": {"position": [x, y], "facing": facing,
                          "pose_after_original_advances": initialized_action["original_pose_advances"][-1],
                          "main_update_ebx": 1, "callback_slot_fixture": callback_index},
        "spawn_call": spawn,
        "callback_dispatch": callback,
        "main_update_dispatch_trace": dispatch_trace,
        "original_helpers_reached": original_helpers,
        "post_spawn_fields": {
            "meter_49e": struct.unpack("<H", uc.mem_read(PLAYER + 0x49E, 2))[0],
            "gauge_5e4": struct.unpack("<H", uc.mem_read(PLAYER + 0x5E4, 2))[0],
        },
        "error": errors or None,
        "scope": "Original action setter/initializer chain 0x464930..0x59ad64 runs to produce action 412/seq.0/pose 0; four original Remilia vtable pose-advance calls then reach pose 4. The original main-update action comparison 0x587bab, dispatch 0x58a3a1, handler 0x58cce7, 0x47a9e0/0x487870 helpers, spawn callsite, and 0x464980 callback-table lookup execute. EBX=1 is seeded to match the value loaded by the skipped prologue at 0x5879cf; callback table, manager return, and external 0x401d50 dispatcher are controlled; 0x487ca0/0x438c60 status services are fixtures. Does not execute full 0x5879a0 update, instantiate/update 801, run collision, or apply damage.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dat-dir", type=Path, default=ROOT / "original")
    parser.add_argument("--x", type=float, default=320.0)
    parser.add_argument("--y", type=float, default=180.0)
    parser.add_argument("--facing", type=int, choices=(-1, 1), default=1)
    parser.add_argument("--callback-index", type=int, choices=(0, 1, 2, 3), default=1,
                        help="callback table slot preloaded with the fixture function pointer")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/x86-remilia-412-spawn-probe.json")
    args = parser.parse_args()
    result = run_case(args.dat_dir, args.x, args.y, args.facing, args.callback_index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
