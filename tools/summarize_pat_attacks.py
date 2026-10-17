#!/usr/bin/env python3
"""Summarize damaging action variants by PAT and button family."""
import csv
import sys
from collections import defaultdict
from pathlib import Path


GROUPS = (
    ("A", 300, 400),
    ("B", 400, 410),
    ("C", 410, 420),
    ("Objetos", 420, 500),
    ("Habilidades", 500, 600),
)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: summarize_pat_attacks.py pat-attacks.tsv output.md", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    with source.open(encoding="cp1252", errors="replace", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"path", "action", "sequence", "damaging_poses"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"missing columns: {sorted(required - set(reader.fieldnames or []))}")
        grouped = defaultdict(list)
        for row in reader:
            action = int(row["action"])
            slug = row["path"].split("/")[-2]
            grouped[slug].append((action, int(row["sequence"]), int(row["damaging_poses"])))

    lines = [
        "# Cobertura de acciones dañinas por PAT",
        "",
        "Resumen del catálogo de `resource_probe --pat-attacks`. Cada variante es una pareja acción/índice. "
        "El contenido dañino indica disponibilidad de datos en PAT; no prueba que el motor la active, "
        "renderice correctamente o reproduzca sus objetos y cancelaciones.",
        "",
        f"Se analizaron **{len(grouped)} carpetas PAT**.",
        "",
        "| Carpeta | Grupo | Variantes | Variantes dañinas | Acciones con daño |",
        "|---|---|---:|---:|---|",
    ]
    for slug in sorted(grouped):
        entries = grouped[slug]
        for name, start, end in GROUPS:
            variants = [entry for entry in entries if start <= entry[0] < end]
            damaging = [entry for entry in variants if entry[2] > 0]
            if not variants:
                continue
            actions = sorted({f"{action}:{index}" for action, index, poses in damaging})
            lines.append(
                f"| `{slug}` | {name} | {len(variants)} | {len(damaging)} | "
                f"{', '.join(actions) if actions else '—'} |"
            )
    lines += [
        "",
        "Los huecos de IDs no representan ausencia de contenido por sí solos: varios personajes usan alias, "
        "acciones específicas o instancias de objeto. Clasificar la ejecución requiere input y trazas del juego.",
        "",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {destination}: {len(grouped)} PAT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
