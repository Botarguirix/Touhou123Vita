#!/usr/bin/env python3
"""Inspect a known-build TH123 replay using the PE 2009 field-read layout."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))

from replay_layout import parse_replay, summarize  # noqa: E402
from x86_replay_compatibility_probe import analyze  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    compatibility = analyze(args.exe, args.replay)
    if not compatibility["replay"]["compatible_with_exe"]:
        raise SystemExit("replay header is incompatible with the selected executable")
    parsed = parse_replay(args.replay.read_bytes())
    result = {
        "compatibility": compatibility,
        "layout": summarize(parsed),
        "scope": (
            "Bounded decode from the 2009 PE loader. Character selection bytes and input-word "
            "consumption are statically traced; full timing/playback parity remains unverified."
        ),
    }
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
