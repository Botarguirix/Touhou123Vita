#!/usr/bin/env python3
"""Summarize damaging PAT poses that carry attack flags, with or without boxes."""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path


ROSTER = {
    "reimu", "marisa", "sakuya", "alice", "patchouli", "youmu", "remilia",
    "yuyuko", "yukari", "suika", "udonge", "aya", "komachi", "iku",
    "tenshi", "sanae", "chirno", "meirin", "utsuho", "suwako",
}


def summarize(source: Path) -> str:
    grouped: dict[tuple[str, int, int, int, bool], dict[str, object]] = {}
    with source.open(encoding="cp1252", errors="replace", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"path", "action", "index", "damage", "attack_boxes", "attack_flags"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"missing columns: {sorted(required - set(reader.fieldnames or []))}")
        for row in reader:
            parts = row["path"].replace("\\", "/").split("/")
            if len(parts) < 4 or parts[2] not in ROSTER:
                continue
            damage = int(row["damage"])
            flags = int(row["attack_flags"], 16)
            if damage <= 0 or flags == 0:
                continue
            action, index = int(row["action"]), int(row["index"])
            explicit_boxes = row["attack_boxes"] != "-"
            key = (parts[2], action, index, flags, explicit_boxes)
            entry = grouped.setdefault(key, {"poses": 0, "max_damage": 0})
            entry["poses"] = int(entry["poses"]) + 1
            entry["max_damage"] = max(int(entry["max_damage"]), damage)

    unboxed = [(key, value) for key, value in grouped.items() if not key[4]]
    direct = [(key, value) for key, value in grouped.items() if key[4]]
    unboxed_pose_count = sum(int(value["poses"]) for _, value in unboxed)
    direct_pose_count = sum(int(value["poses"]) for _, value in direct)
    flag_groups: dict[int, list[str]] = defaultdict(list)
    for (character, action, index, flags, _), _value in unboxed:
        flag_groups[flags].append(f"{character} {action}:{index}")

    lines = [
        "# Flags de ataque en poses PAT con daño",
        "",
        "Generado desde `artifacts/pat-detail.tsv`, limitado al roster jugable. Solo cuenta poses con daño y `attack_flags` distinto de cero. `attack_boxes` distingue cajas ofensivas explícitas de poses que requieren resolver colisión por otra ruta; los flags permanecen sin interpretación hasta contrastarlos con el ejecutable x86.",
        "",
        f"- Combinaciones personaje/acción/índice/flags con cajas explícitas: **{len(direct)}** ({direct_pose_count} poses).",
        f"- Combinaciones personaje/acción/índice/flags sin cajas explícitas: **{len(unboxed)}** ({unboxed_pose_count} poses).",
        f"- Combinaciones de flags sin caja explícita: **{len(flag_groups)}**.",
        "",
        "## Poses dañinas con flags pero sin cajas explícitas",
        "",
        "| Personaje | Acción | Índice | Flags | Poses | Daño máximo |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for (character, action, index, flags, _), value in sorted(unboxed):
        lines.append(
            f"| `{character}` | {action} | {index} | `0x{flags:08x}` | "
            f"{value['poses']} | {value['max_damage']} |"
        )
    lines += ["", "## Agrupación de flags sin caja", "", "| Flags | Variantes observadas |", "|---:|---|"]
    for flags, variants in sorted(flag_groups.items()):
        lines.append(f"| `0x{flags:08x}` | {', '.join(sorted(set(variants)))} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: summarize_pat_attack_flags.py pat-detail.tsv output.md", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    report = summarize(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report, encoding="utf-8")
    print(f"wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
