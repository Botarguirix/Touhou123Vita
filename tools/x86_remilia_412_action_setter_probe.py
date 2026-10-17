#!/usr/bin/env python3
"""Execute Remilia's original action setter/reset/initializer chain for 2C."""
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
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESI,
                               UC_X86_REG_ESP)
from tools.extract_pat_pose_metadata import action_sequence_metadata
from tools.x86_remilia_412_box_sync_probe import ACTION, SEQUENCE, effective_pat
from tools.x86_suwako_808_factory_probe import (
    LIST, OWNER, PAT_MAP, STACK, STOP, Suwako808FactoryProbe,
)

EXE = ROOT / "original/th123.exe"
OBJECT = LIST + 0x8000
VTABLE = OWNER
MAP_RESULT = PAT_MAP + 0x1000
MAP_OBJECT = PAT_MAP + 0x2000
MAP_NODE = PAT_MAP + 0x3000
SEQUENCE_NODE = PAT_MAP + 0x4000
FRAME_DATA = PAT_MAP + 0x5000
PAT_LOOKUP = 0x0043F2F0
ACTION_SETTER = 0x00464930
ACTION_WRITE = 0x00438CA0
RESET_SEQUENCE = 0x00465370
INITIALIZE_ACTION = 0x0059AAA0
INITIALIZER_BODY = 0x0059AD64
ZERO_MOTION = 0x004636B0
SET_POSE_CAPTURE = STOP + 0x100


def run(dat_dir: Path) -> dict[str, object]:
    _archive, _digest, frames = effective_pat(dat_dir)
    if not frames:
        raise ValueError("Remilia action 412/sequence 0 has no PAT frames")

    probe = Suwako808FactoryProbe(EXE, dat_dir)
    uc = probe.uc
    uc.mem_write(OBJECT, bytes(0x1000))
    uc.mem_write(VTABLE, bytes(0x100))
    uc.mem_write(MAP_RESULT, bytes(0x100))
    uc.mem_write(MAP_OBJECT, bytes(0x100))
    uc.mem_write(MAP_NODE, bytes(0x100))
    uc.mem_write(SEQUENCE_NODE, bytes(0x100))
    uc.mem_write(FRAME_DATA, bytes(len(frames) * 0xA8))

    # Install only the PAT map and pose callback boundary. Original setter,
    # sequence reset, and action initializer remain executable PE code.
    uc.mem_write(OBJECT, struct.pack("<I", VTABLE))
    uc.mem_write(VTABLE + 2 * 4, struct.pack("<I", ACTION_SETTER))
    uc.mem_write(VTABLE + 4 * 4, struct.pack("<I", RESET_SEQUENCE))
    uc.mem_write(VTABLE + 7 * 4, struct.pack("<I", SET_POSE_CAPTURE))
    uc.mem_write(VTABLE + 15 * 4, struct.pack("<I", INITIALIZE_ACTION))
    uc.mem_write(OBJECT + 0x160, struct.pack("<I", PAT_MAP + 0x7000))
    uc.mem_write(MAP_RESULT, struct.pack("<II", MAP_OBJECT, MAP_NODE))
    uc.mem_write(MAP_OBJECT + 4, struct.pack("<I", MAP_NODE + 0x100))
    uc.mem_write(MAP_NODE + 0x10, struct.pack("<I", SEQUENCE_NODE))
    uc.mem_write(SEQUENCE_NODE + 4,
                 struct.pack("<II", FRAME_DATA, FRAME_DATA + len(frames) * 0xA8))
    uc.mem_write(SEQUENCE_NODE + 0x14, b"\x00")  # action 412 seq.0 loop mode
    uc.mem_write(SEQUENCE_NODE + 0x1C, struct.pack("<I", SEQUENCE_NODE))

    reached: list[str] = []
    pose_requests: list[int] = []

    def hook(machine, address: int, _size: int, _user: object) -> None:
        if address in (ACTION_SETTER, ACTION_WRITE, RESET_SEQUENCE, INITIALIZE_ACTION,
                       INITIALIZER_BODY, ZERO_MOTION):
            reached.append(hex(address))
        esp = machine.reg_read(UC_X86_REG_ESP)
        if address == PAT_LOOKUP:
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, MAP_RESULT)
            machine.reg_write(UC_X86_REG_ESP, esp + 12)  # thiscall, ret 8
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == SET_POSE_CAPTURE:
            ret, pose = struct.unpack("<II", machine.mem_read(esp, 8))
            pose_requests.append(pose)
            machine.mem_write(OBJECT + 0x140, struct.pack("<H", pose))
            machine.reg_write(UC_X86_REG_ESP, esp + 8)
            machine.reg_write(UC_X86_REG_EIP, ret)

    uc.hook_add(UC_HOOK_CODE, hook)
    entry_sp = STACK + 0xEFF0
    uc.mem_write(entry_sp, struct.pack("<II", STOP, ACTION))
    uc.reg_write(UC_X86_REG_ECX, OBJECT)
    uc.reg_write(UC_X86_REG_ESI, OBJECT)
    uc.reg_write(UC_X86_REG_ESP, entry_sp)
    uc.reg_write(UC_X86_REG_EIP, ACTION_SETTER)
    uc.emu_start(ACTION_SETTER, STOP, count=100000)
    if uc.reg_read(UC_X86_REG_EIP) != STOP:
        raise RuntimeError(f"action setter chain failed at {uc.reg_read(UC_X86_REG_EIP):#x}")

    result = {
        "action": struct.unpack("<H", uc.mem_read(OBJECT + 0x13C, 2))[0],
        "sequence": struct.unpack("<H", uc.mem_read(OBJECT + 0x13E, 2))[0],
        "pose": struct.unpack("<H", uc.mem_read(OBJECT + 0x140, 2))[0],
        "pose_count": struct.unpack("<H", uc.mem_read(OBJECT + 0x148, 2))[0],
        "sequence_node": hex(struct.unpack("<I", uc.mem_read(OBJECT + 0x15C, 4))[0]),
        "state_190": struct.unpack("<I", uc.mem_read(OBJECT + 0x190, 4))[0],
        "counters_7d0_7d2_7d6_7d8": [
            struct.unpack("<H", uc.mem_read(OBJECT + off, 2))[0]
            for off in (0x7D0, 0x7D2, 0x7D6, 0x7D8)],
        "pose_requests": pose_requests,
        "reached_original_functions": reached,
        "expected_pose_count": len(frames),
    }
    if (result["action"] != ACTION or result["sequence"] != SEQUENCE
            or result["pose"] != 0 or result["pose_count"] != len(frames)
            or result["sequence_node"] != hex(SEQUENCE_NODE)
            or result["state_190"] != 0
            or any(result["counters_7d0_7d2_7d6_7d8"])
            or pose_requests != [0]):
        raise AssertionError(f"unexpected action-setter outputs: {result}")
    return {
        "reference_sha256": probe.sha256,
        "target": "Remilia 2C action 412 / PAT sequence 0",
        "result": result,
        "scope": "The original 0x464930 setter, 0x438ca0 action write, 0x465370 resetSequence, and 0x59aaa0/0x59ad64 action initializer execute. PAT associative-map lookup and virtual pose/render callback are controlled. This starts at the setter after input gates; it does not execute the whole input handler, move-lock lookup, character update, collision manager, or a fight.",
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
