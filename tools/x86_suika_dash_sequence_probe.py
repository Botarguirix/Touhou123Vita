#!/usr/bin/env python3
"""Trace Suika's original action-418 PAT sequence through setter and updates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.x86_suika_action_setter_probe import PLAYER, run_action

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


def probe(dat_dir: Path = ROOT / "original") -> dict[str, object]:
    exe = dat_dir / "th123.exe"
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    if digest != REFERENCE_SHA256:
        raise ValueError(f"unexpected reference PE hash: {digest}")
    report = run_action(418, dat_dir)
    update = report["update"]
    sequences = report["pat_fixture"]["sequences"]
    ticks = update["ticks"]
    return {
        "schema": 1,
        "reference_sha256": digest,
        "pat_sha256": report["pat_fixture"]["pat_sha256"],
        "action": 418,
        "setter": {key: report[key] for key in ("action", "sequence", "pose", "pose_count", "error")},
        "effective_sequences": [
            {"index": row["sequence"], "frame_count": len(row["frames"]),
             "attack_frames": [frame["frame"] for frame in row["frames"]
                               if frame["damage"] and frame["attack_boxes"]],
             "damage_values": sorted({frame["damage"] for frame in row["frames"]
                                      if frame["damage"] and frame["attack_boxes"]})}
            for row in sequences],
        "update": {"stop_reason": update["stop_reason"], "error": update["error"],
                   "ticks_completed": update["ticks_completed"],
                   "sequence_setter_calls": update["sequence_setter_calls"],
                   "landing_gate_observations": update["landing_gate_observations"],
                   "sequence_writes": [row for row in update["player_animation_writes"]
                                       if int(row["address"], 16) == PLAYER + 0x13E],
                   "ticks": [{key: tick[key] for key in
                              ("tick", "action", "sequence", "pose", "frame_damage",
                               "frame_attack_box_count", "frame_data_pointer")}
                             for tick in ticks]},
        "active_attack_ticks": [tick["tick"] for tick in ticks
                                if tick["frame_damage"] and tick["frame_attack_box_count"]],
        "scope": "Original Suika action setter and vtable update execute with the local PAT. Action 418 is set directly; no natural dash/input producer, opponent, collision, or gameplay replay is simulated. Player Y is a fixture value (0); the tick-27 landing gate transition is verified from its original vertical-boundary/velocity predicate, not from a natural spatial jump.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dat_dir", nargs="?", type=Path, default=ROOT / "original")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/x86-suika-418-sequence.json")
    args = parser.parse_args()
    result = probe(args.dat_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"action": result["action"], "setter_sequence": result["setter"]["sequence"],
                      "sequence_count": len(result["effective_sequences"]),
                      "active_attack_ticks": result["active_attack_ticks"],
                      "update_stop_reason": result["update"]["stop_reason"],
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
