#!/usr/bin/env python3
"""Resolve rare PAT crop frames to real CV2 dimensions and run the PE quad constructor."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from extract_pat_pose_metadata import action_sequence_metadata, entries_from_dat
from x86_sprite_component_probe import EXPECTED_SHA256, execute

ROSTER = ("reimu", "marisa", "sakuya", "alice", "patchouli", "youmu", "remilia",
          "yuyuko", "yukari", "suika", "udonge", "aya", "komachi", "iku",
          "tenshi", "sanae", "chirno", "meirin", "utsuho", "suwako")
ARCHIVES = ("th105a.dat", "th105b.dat", "th123a.dat", "th123b.dat", "th123c.dat")


def _read_entry(dat_dir: Path, archive: str, entry: tuple[int, int]) -> bytes:
    offset, size = entry
    with (dat_dir / archive).open("rb") as stream:
        stream.seek(offset)
        data = bytearray(stream.read(size))
    if len(data) != size:
        raise ValueError(f"Truncated DAT entry: {archive}@0x{offset:x}")
    key = ((offset >> 1) | 0x23) & 0xFF
    for index in range(size):
        data[index] ^= key
    return bytes(data)


def _effective_resource(dat_dir: Path, indices: dict[str, dict[str, tuple[int, int]]], name: str):
    folded = name.casefold()
    for archive in reversed(ARCHIVES):
        if archive in indices and folded in indices[archive]:
            return archive, _read_entry(dat_dir, archive, indices[archive][folded])
    return None, None


def probe(dat_dir: Path, exe: Path) -> dict[str, object]:
    indices = {archive: entries_from_dat(dat_dir / archive)
               for archive in ARCHIVES if (dat_dir / archive).is_file()}
    if not any(name.startswith("th123") for name in indices):
        raise ValueError(f"No TH123 DAT archives found under {dat_dir}")
    resolved: list[dict[str, object]] = []
    sequence_count = 0
    missing_pat: list[str] = []
    for character in ROSTER:
        pat_name = f"data/character/{character}/{character}.pat"
        pat_archive, pat = _effective_resource(dat_dir, indices, pat_name)
        if pat is None:
            missing_pat.append(character)
            continue
        sequences = action_sequence_metadata(pat, None)
        sequence_count += len(sequences)
        pat_sha256 = hashlib.sha256(pat).hexdigest()
        for sequence in sequences:
            for frame in sequence["frames"]:
                if not frame["tx"] and not frame["ty"]:
                    continue
                image_stem = frame["image"].rsplit(".", 1)[0]
                bitmap_name = f"data/character/{character}/{image_stem}.cv2"
                cv2_archive, cv2 = _effective_resource(dat_dir, indices, bitmap_name)
                row: dict[str, object] = {
                    "character": character, "pat_archive": pat_archive,
                    "pat_sha256": pat_sha256, "action": sequence["action"],
                    "sequence": sequence["sequence"], "frame": frame["frame"],
                    "image": frame["image"],
                    "pose": {key: frame[key] for key in
                             ("tx", "ty", "width", "height", "ox", "oy", "duration", "flags", "special_data")},
                    "cv2_archive": cv2_archive,
                }
                if cv2 is None or len(cv2) < 17:
                    row["cv2"] = None
                    row["x86_component"] = None
                else:
                    bpp = cv2[0]
                    texture_width, texture_height, pitch, alt = struct.unpack_from("<4I", cv2, 1)
                    if not texture_width or not texture_height or texture_width > 2048 or texture_height > 2048:
                        raise ValueError(f"Invalid CV2 dimensions for {bitmap_name}: {texture_width}x{texture_height}")
                    row["cv2"] = {"width": texture_width, "height": texture_height,
                                  "bpp": bpp, "pitch": pitch, "alternate_header": alt,
                                  "stored_bytes": len(cv2)}
                    row["x86_component"] = execute(
                        exe, frame["tx"], frame["ty"], frame["width"], frame["height"],
                        texture_width, texture_height)
                resolved.append(row)
    return {
        "schema": 1,
        "reference_sha256": EXPECTED_SHA256,
        "dat_dir": str(dat_dir),
        "archive_lookup_priority": list(reversed(ARCHIVES)),
        "sequence_count": sequence_count,
        "missing_pat": missing_pat,
        "nonzero_crop_frame_count": len(resolved),
        "frames": resolved,
    }


if __name__ == "__main__":
    default_dat_dir = ROOT / "artifacts" / "vitafs" / "ux0" / "data" / "touhou123vita"
    if not (default_dat_dir / "th105a.dat").is_file():
        default_dat_dir = ROOT / "original"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dat-dir", type=Path, default=default_dat_dir)
    parser.add_argument("--exe", type=Path, default=ROOT / "original" / "th123.exe")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = probe(args.dat_dir, args.exe)
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
