#!/usr/bin/env python3
"""Render a concise per-character coverage table from resource_probe output."""
import csv
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: summarize_pat_inventory.py pat-inventory.tsv output.md", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    with source.open(encoding="cp1252", errors="replace", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    lines = [
        "# Cobertura inicial de PAT",
        "",
        "Catálogo generado al decodificar los PAT instalados localmente. `bloques` incluye acciones y "
        "secuencias según el formato; `poses con daño` cuenta cuadros que traen daño y caja/flag de ataque. "
        "Esta tabla mide contenido cargable, no acciones ya reproducidas por el motor.",
        "",
        f"Se decodificaron **{len(rows)} PAT**.",
        "",
        "| Personaje/carpeta | Imágenes | Bloques | Aliases | Poses | Poses con daño |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda item: item["path"]):
        name = row["path"].split("/")[-2]
        if row.get("moves") == "ERROR":
            lines.append(f"| `{name}` | — | ERROR | — | — | — |")
            continue
        lines.append(
            f"| `{name}` | {int(row['images']):,} | {int(row['moves']):,} | "
            f"{int(row['aliases']):,} | {int(row['poses']):,} | {int(row['damaging_poses']):,} |"
        )
    lines += [
        "",
        "Las carpetas `common` y `namazu` se reportan por separado; el inventario general contiene 20 carpetas "
        "de personajes jugables candidatas, además de contenido común y Namazu. La clasificación final debe "
        "confirmarse con selección de personaje, guion y ejecutable original.",
        "",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {destination}: {len(rows)} PAT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
