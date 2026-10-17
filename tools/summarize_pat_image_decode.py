#!/usr/bin/env python3
"""Summarize the Vita3K PAT image decoder audit."""
import csv
import io
import re
import sys
from pathlib import Path

PLAYABLE = {
    "reimu", "marisa", "sakuya", "alice", "patchouli", "youmu", "remilia",
    "yuyuko", "yukari", "suika", "udonge", "aya", "komachi", "iku",
    "tenshi", "sanae", "chirno", "meirin", "utsuho", "suwako",
}


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: summarize_pat_image_decode.py audit.tsv [output.md]", file=sys.stderr)
        return 2
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2]) if len(sys.argv) == 3 else None
    # Vita DAT names are byte strings and may contain legacy code-page bytes.
    with source.open(encoding="cp1252", errors="replace", newline="") as stream:
        lines = stream.readlines()
    summary = next((line.rstrip("\r\n") for line in reversed(lines) if line.startswith("# summary ")), None)
    rows_text = "".join(line for line in lines if not line.startswith("# summary "))
    rows = [r for r in csv.DictReader(io.StringIO(rows_text), delimiter="\t") if r.get("character")]
    if not summary:
        print("audit has no terminal summary row", file=sys.stderr)
        return 1
    match = re.fullmatch(
        r"# summary pats=(\d+) images=(\d+) decoded=(\d+) unreferenced=(\d+) "
        r"missing_resource=(\d+) missing_palette=(\d+) unsupported_or_invalid=(\d+)", summary
    )
    if not match:
        print(f"invalid audit summary: {summary}", file=sys.stderr)
        return 1
    pat_count, image_count, decoded, unreferenced, missing, no_palette, unsupported = map(int, match.groups())
    if len(rows) != image_count:
        print(f"summary says {image_count} images but TSV contains {len(rows)}", file=sys.stderr)
        return 1

    lines = [
        "# Cobertura de decodificación de imágenes PAT",
        "",
        "Resultado de `resource_probe --pat-image-decode` ejecutado dentro de Vita3K con el decodificador ARM real y prioridad de DAT del runtime. Se examina cada entrada de imagen de los PAT seleccionados; `unreferenced` significa que ninguna pose decodificada usa esa entrada (incluye nombres de paleta presentes en PAT).",
        "",
        f"- PAT examinados: **{pat_count}** (20 candidatos jugables, `common` y `namazu`).",
        f"- Entradas de imagen PAT: **{image_count:,}**; decodificadas: **{decoded:,}**; sin uso por poses: **{unreferenced:,}**.",
        f"- Fallos: recurso ausente **{missing}**, paleta ausente **{no_palette}**, CV2 inválida/no soportada **{unsupported}**.",
        "",
        "## Personajes candidatos del roster",
        "",
        "| Personaje | Imágenes referenciadas | Decodificadas | Fallos referenciados | Imágenes ofensivas referenciadas | Fallos ofensivos |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    playable = [r for r in rows if r["character"] in PLAYABLE]
    for character in sorted(PLAYABLE):
        group = [r for r in playable if r["character"] == character]
        used = [r for r in group if int(r["pose_refs"]) > 0]
        damaging = [r for r in used if int(r["damaging_pose_refs"]) > 0]
        used_fail = [r for r in used if r["status"] != "decoded"]
        damage_fail = [r for r in damaging if r["status"] != "decoded"]
        lines.append(
            f"| {character} | {len(used)} | {sum(r['status'] == 'decoded' for r in used)} | "
            f"{len(used_fail)} | {len(damaging)} | {len(damage_fail)} |"
        )

    failures = [r for r in rows if r["status"] not in ("decoded", "unreferenced")]
    lines += ["", "## Referencias utilizadas con fallo", ""]
    if not failures:
        lines.append("No hay referencias usadas con fallo.")
    else:
        lines += ["| Personaje/PAT | Índice | Imagen | Poses | Poses ofensivas | Estado |", "|---|---:|---|---:|---:|---|"]
        for row in failures:
            lines.append(
                f"| {row['character']} / `{row['pat']}` | {row['image_index']} | `{row['image_name']}` | "
                f"{row['pose_refs']} | {row['damaging_pose_refs']} | `{row['status']}` |"
            )
    lines += [
        "",
        "Las 20 carpetas candidatas no presentan imágenes de poses ofensivas ausentes o no decodificables en esta pasada. El PAT compartido `common` conserva una referencia no ofensiva que no resolvió el loader (`000 hikakuyou.bmp`); requiere rastrear su consumidor/recurso de otra versión. `namazu` se audita aparte y no se cuenta como personaje jugable.",
        "",
        "Esta prueba confirma decodificación de las imágenes referenciadas por las secuencias PAT cargadas, no que todos los movimientos sean alcanzables ni que la composición visual sea idéntica a PC. Las imágenes sin referencias desde poses no se contaron como fallos de sprite.",
        "",
        f"Fuente local ignorada por Git: `{source.as_posix()}`.",
    ]
    result = "\n".join(lines) + "\n"
    if destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(result, encoding="utf-8")
        print(f"wrote {destination}")
    else:
        print(result, end="")
    print(
        f"summary: pats={pat_count} images={image_count} decoded={decoded} "
        f"unreferenced={unreferenced} failures={missing + no_palette + unsupported} "
        f"referenced_failures={len(failures)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
