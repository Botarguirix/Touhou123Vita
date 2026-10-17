#!/usr/bin/env python3
"""Run the original x86 PAT box synchronizer on Remilia 412 pose 5.

The PAT descriptor and vectors are installed from the local effective DAT.
The pinned executable's 0x465e10 executes under Unicorn. Box transform helpers
are controlled to copy coordinates, so this verifies descriptor/vector
publication, not a native match or the final world-space collision geometry.
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

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP
from tools.extract_pat_pose_metadata import action_sequence_metadata, read_pat
from tools.x86_suwako_808_factory_probe import (
    LIST, PAT_MAP, STACK, STOP, Suwako808FactoryProbe,
)

EXE = ROOT / "original/th123.exe"
CHARACTER = "remilia"
ACTION = 412
SEQUENCE = 0
POSE = 5
OBJECT = LIST + 0x8000
DEFENDER = LIST + 0x8800
DESCRIPTOR = PAT_MAP + 0x10000
COLLISION_BOX = PAT_MAP + 0x20000
HURT_BOXES = PAT_MAP + 0x21000
ATTACK_BOXES = PAT_MAP + 0x22000
EXTRA_BOXES = PAT_MAP + 0x23000


def effective_pat(dat_dir: Path) -> tuple[str, str, list[dict[str, object]]]:
    resource = f"data/character/{CHARACTER}/{CHARACTER}.pat"
    for archive in ("th123c.dat", "th123b.dat", "th123a.dat"):
        payload = read_pat(dat_dir / archive, resource)
        if payload is None:
            continue
        pat, digest = payload
        sequences = action_sequence_metadata(pat, ACTION)
        selected = next((s for s in sequences if int(s["sequence"]) == SEQUENCE), None)
        if selected is None:
            raise ValueError(f"action {ACTION}/sequence {SEQUENCE} missing in {archive}")
        return archive, digest, selected["frames"]
    raise FileNotFoundError(f"PAT resource not found: {resource}")


def install_vector(uc, vector_address: int, storage_address: int,
                   boxes: list[list[int]]) -> None:
    end = storage_address + len(boxes) * 16
    uc.mem_write(vector_address, struct.pack("<4I", 0, storage_address, end, end))
    if boxes:
        uc.mem_write(storage_address, b"".join(struct.pack("<4i", *box) for box in boxes))


def run_hit_vs_hurt(attacker: int, defender: int, probe: Suwako808FactoryProbe) -> dict[str, object]:
    """Run the reference pair-geometry helper with this synchronized attacker."""
    uc = probe.uc
    # 0x47a5b0 is a thiscall-style helper with two stack arguments and ret 8.
    sp = STACK + 0xB000 - 12
    uc.mem_write(sp, struct.pack("<3I", STOP, attacker, defender))
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_ECX, OBJECT)
    uc.reg_write(UC_X86_REG_EIP, 0x0047A5B0)
    uc.emu_start(0x0047A5B0, STOP, count=100000)
    if uc.reg_read(UC_X86_REG_EIP) != STOP:
        raise RuntimeError(f"0x47a5b0 did not return: EIP={uc.reg_read(UC_X86_REG_EIP):#x}")
    return {"helper": "0x47a5b0", "return_value": uc.reg_read(UC_X86_REG_EAX),
            "attacker_hit_box_count": uc.mem_read(attacker + 0x1CB, 1)[0],
            "defender_hurt_box_count": uc.mem_read(defender + 0x1CC, 1)[0]}


def run(dat_dir: Path) -> dict[str, object]:
    archive, pat_hash, frames = effective_pat(dat_dir)
    if len(frames) <= POSE:
        raise ValueError(f"pose {POSE} missing from Remilia {ACTION}/{SEQUENCE}")
    frame = frames[POSE]
    if frame["image"] != "attackBa002.bmp" or int(frame["damage"]) != 750:
        raise ValueError(f"unexpected target frame metadata: {frame}")

    probe = Suwako808FactoryProbe(EXE, dat_dir, intercept_box_transforms=True)
    uc = probe.uc
    uc.mem_write(OBJECT, bytes(0x3AC))
    uc.mem_write(DESCRIPTOR, bytes(0xA8))
    uc.mem_write(OBJECT + 0x158, struct.pack("<I", DESCRIPTOR))
    uc.mem_write(OBJECT + 0x1C0, struct.pack("<I", 0))  # force a fresh sync
    uc.mem_write(OBJECT + 0xEC, struct.pack("<f", 300.0))
    uc.mem_write(OBJECT + 0xF0, struct.pack("<f", 400.0))
    uc.mem_write(OBJECT + 0x104, b"\x01")

    collision_boxes = frame["collision_boxes"]
    if len(collision_boxes) > 1:
        raise ValueError("probe supports at most one PAT collision box")
    if collision_boxes:
        uc.mem_write(COLLISION_BOX, struct.pack("<4i", *collision_boxes[0]))
        uc.mem_write(DESCRIPTOR + 0x54, struct.pack("<I", COLLISION_BOX))
    install_vector(uc, DESCRIPTOR + 0x58, HURT_BOXES, frame["hurt_boxes"])
    install_vector(uc, DESCRIPTOR + 0x68, ATTACK_BOXES, frame["attack_boxes"])
    install_vector(uc, DESCRIPTOR + 0x78, EXTRA_BOXES, [])

    result = probe._sync_box_data(OBJECT)
    uc.mem_write(DEFENDER, bytes(0x3AC))
    install_vector(uc, DEFENDER + 0x1D0, HURT_BOXES + 0x1000, frame["hurt_boxes"])
    uc.mem_write(DEFENDER + 0x1CC, bytes((len(frame["hurt_boxes"]),)))
    pair_geometry = run_hit_vs_hurt(OBJECT, DEFENDER, probe)
    return {
        "reference_sha256": probe.sha256,
        "archive": archive,
        "pat_sha256": pat_hash,
        "target": {"character": CHARACTER, "action": ACTION,
                   "sequence": SEQUENCE, "pose": POSE,
                   "image": frame["image"], "duration": frame["duration"],
                   "damage": frame["damage"],
                   "collision_boxes": collision_boxes,
                   "hurt_boxes": frame["hurt_boxes"],
                   "attack_boxes": frame["attack_boxes"]},
        "synchronized": result,
        "pair_geometry": pair_geometry,
        "transform_helpers": probe.box_transform_calls,
        "scope": "The original 0x465e10 synchronizer and 0x47a5b0 hit-vs-hurt geometry helper execute on controlled objects with the extracted PAT descriptor/vectors. 0x4640b0/0x464200 transforms are intercepted as coordinate copies. This does not execute Remilia's full update, manager pair resolution, post-contact damage response, or a native game loop.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dat_dir", nargs="?", type=Path, default=ROOT / "original")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.dat_dir)
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
