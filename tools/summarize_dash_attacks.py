#!/usr/bin/env python3
"""Report PAT frame data for dash B, air back B, and dash C action families."""
import csv
import sys
from collections import defaultdict
from pathlib import Path


NAMES = {408: "66B", 409: "j4B", 418: "66C"}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: summarize_dash_attacks.py pat-detail.tsv output.md", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    required = {"path", "action", "index", "loop", "move_lock", "action_lock", "pose", "duration", "damage", "attack_boxes"}
    groups = defaultdict(list)
    with source.open(encoding="cp1252", errors="replace", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"missing columns: {sorted(required - set(reader.fieldnames or []))}")
        for row in reader:
            action = int(row["action"])
            if action not in NAMES:
                continue
            key = (row["path"].split("/")[-2], action, int(row["index"]))
            groups[key].append(row)

    lines = [
        "# Referencia PAT de ataques de dash",
        "",
        "Generado desde las poses de los DAT locales. 408/409/418 corresponden a `66B`, `j4B` y `66C` "
        "en el enum SokuLib. Cada fila resume una variante de índice; los cuadros listados conservan daño, "
        "duración y cajas ofensivas. Esta evidencia describe los datos, no el input que selecciona cada índice.",
        "",
        "| Carpeta | Acción | Índice | Loop | Move/action lock | Cuadros | Daño | Poses dañinas (pose:daño/duración/cajas) |",
        "|---|---:|---:|---:|---|---:|---:|---|",
    ]
    for (slug, action, index), poses in sorted(groups.items()):
        damaging = [row for row in poses if int(row["damage"]) > 0 and row["attack_boxes"] != "-"]
        if not poses:
            continue
        first = poses[0]
        detail = "; ".join(
            f"{row['pose']}:{row['damage']}/{row['duration']}/{row['attack_boxes'].count(';') + 1}"
            for row in damaging
        ) or "—"
        damage = ", ".join(sorted({row["damage"] for row in damaging}, key=int)) or "—"
        lines.append(
            f"| `{slug}` | {NAMES[action]} ({action}) | {index} | {first['loop']} | "
            f"{first['move_lock']}/{first['action_lock']} | {len(poses)} | {damage} | {detail} |"
        )
    lines += [
        "",
        "Para reconstruir controles también se requieren `handleGroundBE`, `handleAirBE` y el buffer de "
        "comandos del ejecutable. No se infiere transición automática entre índices a partir de esta tabla.",
        "",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {destination}: {len(groups)} move variants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
