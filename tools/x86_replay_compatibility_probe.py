#!/usr/bin/env python3
"""Check whether a TH123 .rep header matches a known executable version."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
ORIGINAL_2009_SHA256 = "24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3"
IMAGE_BASE = 0x00400000
REPLAY_VERSION_READER = 0x0042BF60
REPLAY_VERSION_COMPARE = 0x0042C861
CURRENT_VERSION_HELPER = 0x0043DC20
READFILE_IAT = 0x00857098

VERSION_HELPER_BYTES = bytes.fromhex(
    "a0 1c 29 88 00 f6 d8 1b c0 25 00 00 01 00 05 d2 00 00 00 c3")
VERSION_COMPARE_BYTES = bytes.fromhex(
    "e8 fa f6 ff ff 8b f8 e8 a3 13 01 00 84 c0 75 06 "
    "81 e7 ff ff 00 00 e8 a4 13 01 00 3b f8 74 3e")
READFILE_U32_BYTES = bytes.fromhex(
    "53 8d 4c 24 18 51 6a 04 8d 54 24 24 52 50 ff 15 98 70 85 00")
ORIGINAL_VERSION_HELPER = 0x0043CA50
ORIGINAL_VERSION_HELPER_BYTES = bytes.fromhex(
    "a0 1c 89 84 00 f6 d8 1b c0 25 00 00 01 00 05 c8 00 00 00 c3")
ORIGINAL_VERSION_COMPARE = 0x0042BDD8
ORIGINAL_VERSION_COMPARE_BYTES = bytes.fromhex(
    "e8 63 0c 01 00 84 c0 75 06 81 e7 ff ff 00 00 "
    "e8 64 0c 01 00 3b f8 74 3e")


def _read_va(pe: pefile.PE, va: int, size: int) -> bytes:
    return pe.get_data(va - pe.OPTIONAL_HEADER.ImageBase, size)


def analyze(exe_path: Path, replay_path: Path) -> dict[str, object]:
    exe_bytes = exe_path.read_bytes()
    exe_sha = hashlib.sha256(exe_bytes).hexdigest()
    if exe_sha not in (REFERENCE_SHA256, ORIGINAL_2009_SHA256):
        raise ValueError(f"unrecognized PE SHA-256: {exe_sha}")
    pe = pefile.PE(data=exe_bytes)
    if pe.OPTIONAL_HEADER.ImageBase != IMAGE_BASE:
        raise ValueError(f"unexpected image base: {pe.OPTIONAL_HEADER.ImageBase:#x}")

    if exe_sha == REFERENCE_SHA256:
        profile = "pinned-current"
        version_helper_va = CURRENT_VERSION_HELPER
        compare_va = REPLAY_VERSION_COMPARE
        version_helper_bytes = VERSION_HELPER_BYTES
        compare_bytes = VERSION_COMPARE_BYTES
        if _read_va(pe, REPLAY_VERSION_READER + 0xD5, len(READFILE_U32_BYTES)) != READFILE_U32_BYTES:
            raise ValueError("replay header is no longer read as a 4-byte value")
        helper_result = (0x000000D2, 0x000100D2)
    else:
        profile = "provided-original-2009"
        version_helper_va = ORIGINAL_VERSION_HELPER
        compare_va = ORIGINAL_VERSION_COMPARE
        version_helper_bytes = ORIGINAL_VERSION_HELPER_BYTES
        compare_bytes = ORIGINAL_VERSION_COMPARE_BYTES
        helper_result = (0x000000C8, 0x000100C8)

    if _read_va(pe, version_helper_va, len(version_helper_bytes)) != version_helper_bytes:
        raise ValueError(f"{profile} replay-version helper bytes changed")
    if _read_va(pe, compare_va, len(compare_bytes)) != compare_bytes:
        raise ValueError(f"{profile} replay-version comparison bytes changed")

    replay_bytes = replay_path.read_bytes()
    if len(replay_bytes) < 4:
        raise ValueError("replay is shorter than its 4-byte version field")
    replay_version = struct.unpack_from("<I", replay_bytes)[0]
    # Both known helpers return a base version or add 0x10000 when mode is set.
    accepted_versions = helper_result
    return {
        "exe": {"path": str(exe_path), "sha256": exe_sha, "profile": profile,
                "replay_version_helper": hex(version_helper_va),
                "replay_version_compare": hex(compare_va),
                "accepted_versions": [hex(value) for value in accepted_versions]},
        "replay": {"path": str(replay_path), "size": len(replay_bytes),
                   "sha256": hashlib.sha256(replay_bytes).hexdigest(),
                   "header_version": hex(replay_version),
                   "compatible_with_exe": replay_version in accepted_versions},
        "scope": "Static compatibility check only; does not decode replay frames or prove playback behavior.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path, help="TH123 .rep file")
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--output", type=Path,
                        help="optional JSON report path (default: print to stdout)")
    args = parser.parse_args()
    result = json.dumps(analyze(args.exe, args.replay), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
