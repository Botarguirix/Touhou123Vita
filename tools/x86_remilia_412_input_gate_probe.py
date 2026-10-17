#!/usr/bin/env python3
"""Execute Remilia's 2C move-lock gate through the original setter chain."""
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
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
                               UC_X86_REG_EDI, UC_X86_REG_EIP, UC_X86_REG_ESI,
                               UC_X86_REG_ESP)
from tools.x86_remilia_412_box_sync_probe import ACTION, SEQUENCE, effective_pat
from tools.x86_suwako_808_factory_probe import (
    LIST, OWNER, PAT_MAP, STACK, STOP, Suwako808FactoryProbe,
)

EXE = ROOT / "original/th123.exe"
OBJECT = LIST + 0x8000
VTABLE = OWNER
PAT_RESULT = PAT_MAP + 0x1000
PAT_OBJECT = PAT_MAP + 0x2000
PAT_NODE = PAT_MAP + 0x3000
SEQUENCE_NODE = PAT_MAP + 0x4000
FRAME_DATA = PAT_MAP + 0x5000
LOCK_RESULT = PAT_MAP + 0x8000
LOCK_OBJECT = PAT_MAP + 0x9000
LOCK_NODE = PAT_MAP + 0xA000
LOCK_END = PAT_MAP + 0xA100
LOCK_VALUE = PAT_MAP + 0xB000

INPUT_GATE = 0x0059DD97
MOVE_LOCK_LOOKUP = 0x00489610
PAT_LOOKUP = 0x0043F2F0
ACTION_SETTER = 0x00464930
ACTION_WRITE = 0x00438CA0
RESET_SEQUENCE = 0x00465370
INITIALIZE_ACTION = 0x0059AAA0
INITIALIZER_BODY = 0x0059AD64
ZERO_MOTION = 0x004636B0
POSE_CAPTURE = STOP + 0x100
MOVE_LOCK_RETURN = 0x0059DDAC


def run_case(dat_dir: Path, lock_value: int, comparison_value: int) -> dict[str, object]:
    if min(lock_value, comparison_value) < 0 or max(lock_value, comparison_value) > 0x7FFF:
        raise ValueError("lock and comparison fixtures must be signed-positive 16-bit values")
    _archive, _digest, frames = effective_pat(dat_dir)
    probe = Suwako808FactoryProbe(EXE, dat_dir)
    uc = probe.uc
    uc.mem_write(OBJECT, bytes(0x1000))
    uc.mem_write(VTABLE, bytes(0x100))
    uc.mem_write(PAT_RESULT, bytes(0x100))
    uc.mem_write(PAT_OBJECT, bytes(0x100))
    uc.mem_write(PAT_NODE, bytes(0x100))
    uc.mem_write(SEQUENCE_NODE, bytes(0x100))
    uc.mem_write(FRAME_DATA, bytes(len(frames) * 0xA8))
    uc.mem_write(LOCK_RESULT, bytes(0x100))
    uc.mem_write(LOCK_OBJECT, bytes(0x100))
    uc.mem_write(LOCK_NODE, bytes(0x100))
    uc.mem_write(LOCK_END, bytes(0x20))
    uc.mem_write(LOCK_VALUE, bytes(0x20))

    uc.mem_write(OBJECT, struct.pack("<I", VTABLE))
    uc.mem_write(VTABLE + 2 * 4, struct.pack("<I", ACTION_SETTER))
    uc.mem_write(VTABLE + 4 * 4, struct.pack("<I", RESET_SEQUENCE))
    uc.mem_write(VTABLE + 7 * 4, struct.pack("<I", POSE_CAPTURE))
    uc.mem_write(VTABLE + 15 * 4, struct.pack("<I", INITIALIZE_ACTION))
    uc.mem_write(OBJECT + 0x13C, struct.pack("<H", 0))
    uc.mem_write(OBJECT + 0x160, struct.pack("<I", PAT_MAP + 0x7000))
    uc.mem_write(OBJECT + 0x49E, struct.pack("<H", 1000))  # meter satisfies gate
    uc.mem_write(OBJECT + 0x754, struct.pack("<I", 1))
    uc.mem_write(OBJECT + 0x12C, struct.pack("<f", 9.0))

    uc.mem_write(PAT_RESULT, struct.pack("<II", PAT_OBJECT, PAT_NODE))
    uc.mem_write(PAT_OBJECT + 4, struct.pack("<I", PAT_NODE + 0x100))
    uc.mem_write(PAT_NODE + 0x10, struct.pack("<I", SEQUENCE_NODE))
    uc.mem_write(SEQUENCE_NODE + 4,
                 struct.pack("<II", FRAME_DATA, FRAME_DATA + len(frames) * 0xA8))
    uc.mem_write(SEQUENCE_NODE + 0x14, b"\x00")
    uc.mem_write(SEQUENCE_NODE + 0x1C, struct.pack("<I", SEQUENCE_NODE))

    # moveLock(412) -> lock value 0 (unlocked); the game lookup itself executes.
    uc.mem_write(LOCK_RESULT, struct.pack("<II", LOCK_OBJECT, LOCK_NODE))
    uc.mem_write(LOCK_OBJECT + 4, struct.pack("<I", LOCK_END))
    uc.mem_write(LOCK_NODE + 0x10, struct.pack("<I", LOCK_VALUE))
    uc.mem_write(LOCK_VALUE + 0x10, struct.pack("<H", lock_value))

    reached: list[str] = []
    pose_requests: list[int] = []
    lookup_keys: list[dict[str, object]] = []
    lock_actions: list[int] = []
    lock_results: list[int] = []

    def hook(machine, address: int, _size: int, _user: object) -> None:
        if address in (INPUT_GATE, MOVE_LOCK_LOOKUP, ACTION_SETTER,
                       ACTION_WRITE, RESET_SEQUENCE, INITIALIZE_ACTION,
                       INITIALIZER_BODY, ZERO_MOTION):
            reached.append(hex(address))
        if address == MOVE_LOCK_RETURN:
            lock_results.append(machine.reg_read(UC_X86_REG_EAX) & 0xFFFF)
        esp = machine.reg_read(UC_X86_REG_ESP)
        if address == PAT_LOOKUP:
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            arg1, arg2 = struct.unpack("<II", machine.mem_read(esp + 4, 8))
            arg2_value = struct.unpack("<I", machine.mem_read(arg2, 4))[0]
            lookup_keys.append({"caller": hex(ret), "args": [hex(arg1), hex(arg2)],
                                "deref_arg2": hex(arg2_value)})
            if ret == 0x00489632:
                lock_actions.append(arg2_value)
            result_ptr = LOCK_RESULT if ret == 0x00489632 else PAT_RESULT
            machine.reg_write(UC_X86_REG_EAX, result_ptr)
            machine.reg_write(UC_X86_REG_ESP, esp + 12)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == POSE_CAPTURE:
            ret, pose = struct.unpack("<II", machine.mem_read(esp, 8))
            pose_requests.append(pose)
            machine.mem_write(OBJECT + 0x140, struct.pack("<H", pose))
            machine.reg_write(UC_X86_REG_ESP, esp + 8)
            machine.reg_write(UC_X86_REG_EIP, ret)

    uc.hook_add(UC_HOOK_CODE, hook)
    sp = STACK + 0xEFF0
    # Interior handler stack at this block: saved EBP/EDI/ESI/EBX, two locals,
    # then the real caller return address consumed by the shared epilogue.
    uc.mem_write(sp, struct.pack("<7I", 0xAAAA0001, 0, OBJECT, 0,
                                  0x11111111, 0x22222222, STOP))
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_ESI, OBJECT)
    uc.reg_write(UC_X86_REG_ECX, OBJECT)
    uc.reg_write(UC_X86_REG_EBX, comparison_value)
    uc.reg_write(UC_X86_REG_EDI, 0)
    uc.reg_write(UC_X86_REG_EIP, INPUT_GATE)
    uc.emu_start(INPUT_GATE, STOP, count=100000)
    if uc.reg_read(UC_X86_REG_EIP) != STOP:
        raise RuntimeError(f"input gate chain failed at {uc.reg_read(UC_X86_REG_EIP):#x}")

    result = {
        "action": struct.unpack("<H", uc.mem_read(OBJECT + 0x13C, 2))[0],
        "sequence": struct.unpack("<H", uc.mem_read(OBJECT + 0x13E, 2))[0],
        "pose": struct.unpack("<H", uc.mem_read(OBJECT + 0x140, 2))[0],
        "pose_count": struct.unpack("<H", uc.mem_read(OBJECT + 0x148, 2))[0],
        "sequence_node": hex(struct.unpack("<I", uc.mem_read(OBJECT + 0x15C, 4))[0]),
        "lock_lookup_keys": lookup_keys,
        "move_lock_actions": lock_actions,
        "move_lock_results": lock_results,
        "pose_requests": pose_requests,
        "reached_original_functions": reached,
    }
    enters_2c = comparison_value <= lock_value
    expected_2c_values = (result["action"] == ACTION and result["sequence"] == SEQUENCE
                          and result["pose"] == 0 and result["pose_count"] == len(frames)
                          and result["sequence_node"] == hex(SEQUENCE_NODE)
                          and pose_requests == [0])
    rejected_2c = result["action"] != ACTION and hex(ACTION_SETTER) not in reached
    if (not lock_actions or lock_actions[0] != ACTION or lock_results[:1] != [lock_value]
            or hex(MOVE_LOCK_LOOKUP) not in reached
            or (enters_2c and not expected_2c_values)
            or (not enters_2c and not rejected_2c)):
        raise AssertionError(f"unexpected 2C gate result: {result}")
    return {
        "reference_sha256": probe.sha256,
        "action": ACTION,
        "move_lock_fixture": lock_value,
        "comparison_fixture": comparison_value,
        "entered_2c": enters_2c,
        "result": result,
    }


def run(dat_dir: Path) -> dict[str, object]:
    cases = [run_case(dat_dir, lock_value=0, comparison_value=0),
             run_case(dat_dir, lock_value=0, comparison_value=1)]
    return {
        "cases": cases,
        "scope": "Both cases begin at 0x59dd97, bypassing earlier input/ground/resource gates. Original 0x489610, comparison, setter/reset and initializer execute; associative-map and PAT lookup plus pose/render callback are controlled. Case one covers lock 0 with comparison 0 and enters action 412; case two covers comparison 1 > lock 0 and must reject 2C. Neither case runs a frame update, collision response, or native fight.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dat_dir", nargs="?", type=Path, default=ROOT / "original")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run(args.dat_dir)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
