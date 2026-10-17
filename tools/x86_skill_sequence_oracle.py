#!/usr/bin/env python3
"""Execute the original Reimu PAT sequence reset and initializer under Unicorn."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_EBP,
    UC_X86_REG_ESI, UC_X86_REG_ESP,
)

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
RESET_SEQUENCE = 0x00465370
SET_SEQUENCE = 0x004652A0
REIMU_INITIALIZE_ACTION = 0x004AC670
NEXT_POSE = 0x00464B70
SET_POSE_DATA = 0x0043A250
APPLY_AIR_MECHANICS = 0x00487EA0
GET_GROUND_HEIGHT = 0x004397F0
SKILL_560_AIR_GATE = 0x004A06A0
AIR_GATE_RESULT_TEST = 0x004A06A7
PLAYER_AIR_LANDING_CALLBACK = 0x004636B0
ADVANCE_FRAME = 0x00438C60
SET_SEQUENCE_CAPTURE = 0x03100300
PAT_LOOKUP = 0x0043F2F0
PLAYER = 0x01000000
VTABLE = 0x01100000
STACK = 0x02000000
MAP_RESULT = 0x03000000
SET_POSE = 0x03100000
FPU_STUB = 0x03100100
GROUND_HEIGHT = 0x03100200
STOP = 0x03200000
MAP_OBJECT = 0x03300000
MAP_NODE = 0x03400000
SEQUENCE_LIST = 0x03500000
SEQUENCE_RECORDS = 0x03600000


def read_u16(uc: Uc, address: int) -> int:
    return struct.unpack("<H", uc.mem_read(address, 2))[0]


class SkillSequenceOracle:
    def __init__(self, exe: Path):
        raw = exe.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != REFERENCE_SHA256:
            raise ValueError(f"reference SHA-256 mismatch: {self.sha256}")
        pe = pefile.PE(data=raw)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        image = pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(self.base, (len(image) + 0xFFF) & ~0xFFF)
        self.uc.mem_write(self.base, image)
        for address, size in (
            (PLAYER, 0x1000), (VTABLE, 0x1000), (STACK, 0x10000),
            (MAP_RESULT, 0x1000), (SET_POSE, 0x1000), (STOP, 0x1000),
            (MAP_OBJECT, 0x1000), (MAP_NODE, 0x1000),
            (SEQUENCE_LIST, 0x1000), (SEQUENCE_RECORDS, 0x1000),
        ):
            self.uc.mem_map(address, size)
        self.uc.hook_add(UC_HOOK_CODE, self._hook)
        self.uc.mem_write(FPU_STUB, b"\xdb\xe3\xd9\x05" + struct.pack("<I", GROUND_HEIGHT) + b"\xc3")

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address == GET_GROUND_HEIGHT:
            uc.reg_write(UC_X86_REG_EIP, FPU_STUB)
            return
        if address == PLAYER_AIR_LANDING_CALLBACK:
            esp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            uc.reg_write(UC_X86_REG_EIP, ret)
            uc.reg_write(UC_X86_REG_ESP, esp + 4)
            return
        if address == AIR_GATE_RESULT_TEST:
            self._air_gate_result = uc.reg_read(UC_X86_REG_EAX) & 0xFF
            return
        if address == SET_SEQUENCE_CAPTURE:
            esp = uc.reg_read(UC_X86_REG_ESP)
            self._requested_recovery_sequence = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
            uc.reg_write(UC_X86_REG_EIP, STOP)
            return
        if address == ADVANCE_FRAME and getattr(self, "_stop_at_advance", False):
            uc.emu_stop()
            return
        if address not in (PAT_LOOKUP, SET_POSE, SET_POSE_DATA):
            return
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        if address == PAT_LOOKUP:
            # The map lookup returns the synthetic action-560 node below.
            uc.reg_write(UC_X86_REG_EIP, ret)
            uc.reg_write(UC_X86_REG_ESP, esp + 12)  # thiscall, ret 8
            uc.reg_write(UC_X86_REG_EAX, MAP_RESULT)
        elif address == SET_POSE:
            # Keep resetSequence's real x86 writes while isolating render refresh.
            pose = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
            uc.mem_write(PLAYER + 0x140, struct.pack("<H", pose))
            uc.reg_write(UC_X86_REG_EIP, ret)
            uc.reg_write(UC_X86_REG_ESP, esp + 8)  # ret 4
        else:
            # Isolate frame-data submission after nextPose selects its PAT pose.
            uc.reg_write(UC_X86_REG_EIP, ret)
            uc.reg_write(UC_X86_REG_ESP, esp + 4)

    def run_level(self, level: int) -> dict[str, int]:
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(VTABLE, bytes(0x1000))
        uc.mem_write(MAP_RESULT, bytes(0x1000))
        uc.mem_write(MAP_OBJECT, bytes(0x1000))
        uc.mem_write(MAP_NODE, bytes(0x1000))
        uc.mem_write(SEQUENCE_LIST, bytes(0x1000))
        uc.mem_write(SEQUENCE_RECORDS, bytes(0x1000))

        # Reimu's virtual setPose slot is called by the original reset routine.
        uc.mem_write(PLAYER, struct.pack("<I", VTABLE))
        uc.mem_write(VTABLE + 7 * 4, struct.pack("<I", SET_POSE))
        uc.mem_write(PLAYER + 0x13C, struct.pack("<H", 560))
        uc.mem_write(PLAYER + 0x160, struct.pack("<I", 0x03700000))
        uc.mem_write(PLAYER + 0x6A7, bytes([level]))

        # Match the associative-map iterator reads in resetSequence.
        uc.mem_write(MAP_RESULT, struct.pack("<II", MAP_OBJECT, MAP_NODE))
        uc.mem_write(MAP_OBJECT + 4, struct.pack("<I", MAP_NODE + 0x100))
        uc.mem_write(MAP_NODE + 0x10, struct.pack("<I", SEQUENCE_LIST))
        uc.mem_write(SEQUENCE_LIST + 4, struct.pack("<I", SEQUENCE_RECORDS))
        uc.mem_write(SEQUENCE_LIST + 8, struct.pack("<I", SEQUENCE_RECORDS + 2 * 0xA8))

        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, RESET_SEQUENCE)
        uc.emu_start(RESET_SEQUENCE, STOP, count=1000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError("original resetSequence did not return")
        reset_result = {
            "effective_skill_level": level,
            "sequence_after_reset": read_u16(uc, PLAYER + 0x13E),
            "sequence_count": read_u16(uc, PLAYER + 0x148),
        }

        # Reimu's actual action initializer only sets this marker at level 4;
        # test whether it also changes the selected PAT sequence.
        uc.mem_write(PLAYER + 0x51C, bytes(2))
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, REIMU_INITIALIZE_ACTION)
        uc.emu_start(REIMU_INITIALIZE_ACTION, STOP, count=1000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError("original Reimu action initializer did not return")
        reset_result["sequence_after_character_init"] = read_u16(uc, PLAYER + 0x13E)
        reset_result["level4_action_marker"] = read_u16(uc, PLAYER + 0x51C)
        expected_marker = 2 if level >= 4 else 0
        if (reset_result["sequence_after_reset"] != 0
                or reset_result["sequence_count"] != 2
                or reset_result["sequence_after_character_init"] != 0
                or reset_result["level4_action_marker"] != expected_marker):
            raise AssertionError(f"unexpected original x86 state: {reset_result}")
        return reset_result

    def run_set_sequence(self, sequence: int) -> dict[str, int]:
        """Execute the original virtual sequence setter against a linked PAT map."""
        counts = (4, 7, 2, 3)  # Reimu action 560, PAT variants 0..3.
        if not 0 <= sequence < len(counts):
            raise ValueError("sequence must be between 0 and 3")
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(VTABLE, bytes(0x1000))
        uc.mem_write(MAP_RESULT, bytes(0x1000))
        uc.mem_write(MAP_OBJECT, bytes(0x1000))
        uc.mem_write(MAP_NODE, bytes(0x1000))
        uc.mem_write(SEQUENCE_LIST, bytes(0x1000))
        uc.mem_write(SEQUENCE_RECORDS, bytes(0x1000))

        uc.mem_write(PLAYER, struct.pack("<I", VTABLE))
        uc.mem_write(VTABLE + 7 * 4, struct.pack("<I", SET_POSE))
        uc.mem_write(PLAYER + 0x13C, struct.pack("<H", 560))
        uc.mem_write(PLAYER + 0x160, struct.pack("<I", 0x03700000))
        uc.mem_write(MAP_RESULT, struct.pack("<II", MAP_OBJECT, MAP_NODE))
        uc.mem_write(MAP_OBJECT + 4, struct.pack("<I", MAP_NODE + 0x100))

        nodes = [SEQUENCE_LIST + index * 0x100 for index in range(len(counts))]
        for index, (node, count) in enumerate(zip(nodes, counts)):
            frames = SEQUENCE_RECORDS + index * 0x300
            uc.mem_write(node + 4, struct.pack("<II", frames, frames + count * 0xA8))
            uc.mem_write(node + 0x18, bytes([int(index == 2)]))
            uc.mem_write(node + 0x1C, struct.pack("<I", nodes[index + 1] if index + 1 < len(nodes) else 0))
        uc.mem_write(MAP_NODE + 0x10, struct.pack("<I", nodes[0]))

        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<II", STOP, sequence))
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, SET_SEQUENCE)
        uc.emu_start(SET_SEQUENCE, STOP, count=2000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError("original setSequence did not return")
        if uc.reg_read(UC_X86_REG_ESP) != entry_sp + 8:
            raise RuntimeError("setSequence returned with an unexpected stack position")

        selected_node = struct.unpack("<I", uc.mem_read(PLAYER + 0x15C, 4))[0]
        result = {
            "requested_sequence": sequence,
            "selected_sequence": struct.unpack("<H", uc.mem_read(PLAYER + 0x13E, 2))[0],
            "selected_node": selected_node,
            "expected_node": nodes[sequence],
            "pose_count": struct.unpack("<H", uc.mem_read(PLAYER + 0x148, 2))[0],
            "loop_flag": uc.mem_read(selected_node + 0x18, 1)[0],
        }
        if (result["selected_sequence"] != sequence or selected_node != nodes[sequence]
                or result["pose_count"] != counts[sequence]
                or result["loop_flag"] != int(sequence == 2)):
            raise AssertionError(f"original setSequence mismatch: {result}")
        return result

    def run_next_pose_boundary(self, *, loop: bool, pose_count: int) -> dict[str, int]:
        """Run original nextPose at the final pose of one PAT sequence."""
        if pose_count < 1:
            raise ValueError("pose_count must be positive")
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(MAP_NODE, bytes(0x1000))
        uc.mem_write(SEQUENCE_RECORDS, bytes(0x1000))
        node, frames = MAP_NODE, SEQUENCE_RECORDS
        uc.mem_write(PLAYER + 0x15C, struct.pack("<I", node))
        uc.mem_write(PLAYER + 0x150, struct.pack("<I", frames + (pose_count - 1) * 0xA8))
        uc.mem_write(PLAYER + 0x140, struct.pack("<H", pose_count - 1))
        uc.mem_write(PLAYER + 0x148, struct.pack("<H", pose_count))
        uc.mem_write(PLAYER + 0x142, struct.pack("<H", 3))
        uc.mem_write(node + 4, struct.pack("<II", frames, frames + pose_count * 0xA8))
        uc.mem_write(node + 0x14, bytes([int(loop)]))
        uc.mem_write(frames + (pose_count - 1) * 0xA8 + 8, struct.pack("<H", 4))
        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, NEXT_POSE)
        uc.emu_start(NEXT_POSE, STOP, count=1000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError("original nextPose did not return")
        result = {
            "loop": int(loop), "pose_count": pose_count,
            "pose_after_advance": read_u16(uc, PLAYER + 0x140),
            "subframe_after_advance": read_u16(uc, PLAYER + 0x142),
            "reports_sequence_end": uc.reg_read(UC_X86_REG_EAX) & 0xFF,
        }
        if (result["pose_after_advance"] != 0 or result["subframe_after_advance"] != 0
                or result["reports_sequence_end"] != int(not loop)):
            raise AssertionError(f"original nextPose boundary mismatch: {result}")
        return result

    def run_skill_560_landing_transition(
        self, *, height: float, vertical_velocity: float, ground_height: float,
        collision_flag: int = 0, sequence: int = 2,
    ) -> dict[str, int | float | None]:
        """Execute original air gate and the Reimu-560 recovery branch."""
        uc = self.uc
        uc.mem_write(PLAYER, bytes(0x1000))
        uc.mem_write(VTABLE, bytes(0x1000))
        uc.mem_write(PLAYER, struct.pack("<I", VTABLE))
        uc.mem_write(VTABLE + 3 * 4, struct.pack("<I", SET_SEQUENCE_CAPTURE))
        uc.mem_write(PLAYER + 0x13C, struct.pack("<H", 560))
        uc.mem_write(PLAYER + 0x13E, struct.pack("<H", sequence))
        uc.mem_write(PLAYER + 0xF0, struct.pack("<f", height))
        uc.mem_write(PLAYER + 0xF8, struct.pack("<f", vertical_velocity))
        uc.mem_write(PLAYER + 0x4C4, bytes([collision_flag & 0xFF]))
        uc.mem_write(GROUND_HEIGHT, struct.pack("<f", ground_height))
        self._requested_recovery_sequence = None
        self._air_gate_result = None
        self._stop_at_advance = True
        entry_sp = STACK + 0xEFF0
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESI, PLAYER)
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_EBP, STACK + 0xF000)
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EIP, SKILL_560_AIR_GATE)
        try:
            uc.emu_start(SKILL_560_AIR_GATE, STOP, count=1000)
        finally:
            self._stop_at_advance = False
        result = {
            "height": height, "vertical_velocity": vertical_velocity,
            "ground_height": ground_height, "collision_flag": collision_flag,
            "starting_sequence": sequence,
            "air_mechanics_result": self._air_gate_result,
            "requested_recovery_sequence": self._requested_recovery_sequence,
        }
        expected_gate = int(height <= ground_height and vertical_velocity < 0 and collision_flag == 0)
        expected_sequence = 3 if expected_gate and sequence < 3 else None
        if (result["air_mechanics_result"] != expected_gate
                or result["requested_recovery_sequence"] != expected_sequence):
            raise AssertionError(f"original action-560 landing transition mismatch: {result}")
        return result


def run(exe: Path, output: Path) -> dict[str, object]:
    oracle = SkillSequenceOracle(exe)
    rows = [oracle.run_level(level) for level in range(5)]
    sequence_rows = [oracle.run_set_sequence(sequence) for sequence in range(4)]
    loop_rows = [oracle.run_next_pose_boundary(loop=loop, pose_count=count)
                 for loop, count in ((False, 7), (True, 2))]
    landing_rows = [
        oracle.run_skill_560_landing_transition(height=0.0, vertical_velocity=-1.0, ground_height=0.0),
        oracle.run_skill_560_landing_transition(height=1.0, vertical_velocity=-1.0, ground_height=0.0),
        oracle.run_skill_560_landing_transition(height=0.0, vertical_velocity=0.0, ground_height=0.0),
        oracle.run_skill_560_landing_transition(height=0.0, vertical_velocity=-1.0,
                                                ground_height=0.0, collision_flag=1),
    ]
    report: dict[str, object] = {
        "schema": 1,
        "reference_sha256": oracle.sha256,
        "reset_sequence_va": hex(RESET_SEQUENCE),
        "reimu_initialize_action_va": hex(REIMU_INITIALIZE_ACTION),
        "action_id": 560,
        "cases": rows,
        "set_sequence_va": hex(SET_SEQUENCE),
        "sequence_selection_cases": sequence_rows,
        "next_pose_boundary_cases": loop_rows,
        "skill_560_landing_transition_cases": landing_rows,
        "passed": True,
        "scope": (
            "Executes original resetSequence and Reimu initializeAction for skill 103/action 560. "
            "The PAT lookup and setPose rendering callback are synthetic; x86 selects sequence 0 "
            "at every effective level, while Reimu writes its action marker only at level 4. "
            "The original setSequence is also executed against a synthetic four-node action-560 "
            "PAT list and selects each exact node, pose count, and loop flag. This does not identify "
            "the gameplay input that enters action 560. Original nextPose is also run at "
            "the final pose for loop and non-loop nodes; only the non-loop node reports sequence end. "
            "The pose-data rendering submission is stubbed. Original applyAirMechanics and the "
            "action-560 recovery branch run with ground-height and an unrelated physics callback "
            "isolated; descending ground contact requests setSequence(3)."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"skill sequence x86 cases: {len(rows)}; passed; output={output}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.exe, args.output)


if __name__ == "__main__":
    main()
