#!/usr/bin/env python3
"""Summarize PAT action/lock/attack coverage for the playable roster."""
import csv
import sys
from collections import defaultdict
from pathlib import Path


ROSTER = [
    "reimu", "marisa", "sakuya", "alice", "patchouli", "youmu", "remilia",
    "yuyuko", "yukari", "suika", "udonge", "aya", "komachi", "iku",
    "tenshi", "sanae", "chirno", "meirin", "utsuho", "suwako",
]
ACTION_NAMES = {200: "dash frontal", 408: "66B", 412: "2C", 418: "66C"}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: summarize_dash_dispatch.py pat-detail.tsv output.md", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    required = {"path", "action", "index", "move_lock", "action_lock", "pose", "damage", "attack_flags", "attack_boxes"}
    moves = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    with source.open(encoding="cp1252", errors="replace", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"missing columns: {sorted(required - set(reader.fieldnames or []))}")
        for row in reader:
            action = int(row["action"])
            if action not in ACTION_NAMES:
                continue
            slug = row["path"].split("/")[-2]
            index = int(row["index"])
            move = moves[slug][action].setdefault(index, {
                "move_lock": set(), "action_lock": set(), "poses": 0,
                "damage_poses": 0, "flagged_damage_poses": 0, "damage_flags": set(),
            })
            move["move_lock"].add(int(row["move_lock"]))
            move["action_lock"].add(int(row["action_lock"]))
            move["poses"] += 1
            if int(row["damage"]) > 0 and row["attack_boxes"] != "-":
                move["damage_poses"] += 1
            if int(row["damage"]) > 0 and int(row["attack_flags"], 16):
                move["flagged_damage_poses"] += 1
                move["damage_flags"].add(int(row["attack_flags"], 16))

    def describe(slug: str, action: int) -> str:
        variants = moves[slug][action]
        if not variants:
            return "—"
        parts = []
        for index, move in sorted(variants.items()):
            ml = "/".join(map(str, sorted(move["move_lock"])))
            al = "/".join(map(str, sorted(move["action_lock"])))
            hit = "hit" if move["damage_poses"] else "sin hitbox dañina"
            parts.append(f"{index}:{ml}/{al} ({hit})")
        return ", ".join(parts)

    lines = [
        "# Cobertura de dispatcher dash/B/C por roster",
        "",
        "Generado desde `artifacts/pat-detail.tsv` con `tools/summarize_dash_dispatch.py`. Se muestran las acciones PAT explícitas (no aliases) y sus pares `move_lock/action_lock`; `hit` significa que al menos una pose tiene daño y caja ofensiva. El campo se repite por pose, por lo que se consolida por variante.",
        "",
        "| Personaje | 200 dash | 408 66B (índice: move/action lock) | 418 66C (índice: move/action lock) |",
        "|---|---|---|---|",
    ]
    for slug in ROSTER:
        lines.append(f"| `{slug}` | {describe(slug, 200)} | {describe(slug, 408)} | {describe(slug, 418)} |")
    remilia_2c = moves["remilia"][412]
    remilia_2c_evidence = "; ".join(
        f"índice {index}: move/action lock {min(move['move_lock'])}/{min(move['action_lock'])}, "
        f"{move['flagged_damage_poses']} poses con daño y flags, {move['damage_poses']} con caja ofensiva explícita, "
        f"flags {', '.join(f'0x{flag:08x}' for flag in sorted(move['damage_flags'])) or 'ninguno'}"
        for index, move in sorted(remilia_2c.items())
    ) or "sin definición PAT"
    lines += [
        "",
        "## Lectura y límites",
        "",
        "Los 20 PAT tienen una definición explícita de acción 200. Diecinueve tienen 408 y 418; Remilia no define esas dos acciones y no debe recibir este dispatcher genérico por inferencia. Sí contiene 412 (2C): " + remilia_2c_evidence + ". Las locks de 408 no son uniformes: el índice 0 toma 20 en Yuyuko, 40 en Alice y 50 en la mayoría. Las variantes también pueden diferir entre sí, por ejemplo 418 de Reimu e Iku. Por eso, usar un único lock o asumir que toda variante tiene el mismo comportamiento no cubre el roster.",
        "",
        "Este cruce prueba disponibilidad y valores del PAT, no que el handler x86 de Reimu/Cirno sea compartido por los otros 18 personajes ni cómo se seleccionan sus variantes. La transición 200→408/418 se observó en Ghidra para Reimu (`004ae670`) y Cirno (`006fb8b0`); el resto requiere handlers propios o una prueba dinámica por personaje. La acción 2C de Remilia tiene daño/flags, pero cero cajas ofensivas explícitas en el PAT; su ruta de impactos/objetos sigue por recuperar. Los datos vienen de la copia local de recursos del usuario; el juego no forma parte de Git.",
        "",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {destination}: {len(ROSTER)} roster entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
