#!/usr/bin/env python3
"""Summarize the user's local three-DAT resource manifest as Markdown."""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: summarize_manifest.py resource-manifest.tsv output.md", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    # DAT paths are byte strings from a legacy Windows game, commonly CP1252.
    with source.open(encoding="cp1252", errors="replace", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))

    categories = Counter()
    extensions = Counter()
    characters = defaultdict(Counter)
    stages = Counter()
    total_bytes = 0
    for row in rows:
        path = PurePosixPath(row["path"])
        parts = path.parts
        size = int(row["size"])
        total_bytes += size
        categories[parts[1] if len(parts) > 1 and parts[0] == "data" else "root"] += 1
        extensions[path.suffix.lower() or "[none]"] += 1
        if len(parts) > 2 and parts[:2] == ("data", "character"):
            characters[parts[2]][path.suffix.lower() or "[none]"] += 1
        if len(parts) > 2 and parts[:2] == ("data", "background"):
            stages[parts[2]] += 1

    lines = [
        "# Inventario local de recursos",
        "",
        "Generado a partir del índice de `th123a.dat`, `th123b.dat` y `th123c.dat` "
        "instalados en el VitaFS local. Los DAT comerciales permanecen fuera del repositorio y del VPK.",
        "",
        f"El índice reúne **{len(rows):,} archivos** y **{total_bytes:,} bytes** sin comprimir.",
        "",
        "## Categorías principales",
        "",
        "| Ruta bajo `data/` | Archivos |",
        "|---|---:|",
    ]
    lines.extend(f"| `{name}` | {count:,} |" for name, count in sorted(categories.items()))
    lines += ["", "## Carpetas de personaje", "", "| Carpeta | PAT | CV2 | Otros archivos |", "|---|---:|---:|---:|"]
    for name, ext_counts in sorted(characters.items()):
        pat = ext_counts[".pat"]
        cv2 = ext_counts[".cv2"]
        other = sum(ext_counts.values()) - pat - cv2
        lines.append(f"| `{name}` | {pat:,} | {cv2:,} | {other:,} |")
    lines += ["", "## Carpetas de escenario", "", "| Carpeta | Archivos |", "|---|---:|"]
    lines.extend(f"| `{name}` | {count:,} |" for name, count in sorted(stages.items()))
    lines += [
        "",
        "## Tipos de archivo",
        "",
        "| Extensión | Archivos |",
        "|---|---:|",
    ]
    lines.extend(f"| `{name}` | {count:,} |" for name, count in sorted(extensions.items()))
    lines += [
        "",
        "## Límite de esta primera pasada",
        "",
        "El manifiesto prueba qué recursos están presentes; todavía no indica cuáles se usan en cada "
        "estado, escena, clima o efecto. `common` y `namazu` aparecen como carpetas de personaje en "
        "los DAT y requieren clasificarse como recursos compartidos o contenido especial antes de "
        "fijar el número de personajes jugables. La siguiente fase resolverá referencias desde PAT, "
        "CSV, scripts de escena y despachadores del ejecutable de referencia exportados con Ghidra.",
        "",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {destination}: {len(rows)} entries, {len(characters)} character folders, {len(stages)} background folders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
