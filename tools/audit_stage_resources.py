#!/usr/bin/env python3
"""Audit stage tile/resource paths against the current Vita stage loader."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

STAGES = ("bg00", "bg01", "bg02", "bg03", "bg04", "bg05", "bg06",
          "bg10", "bg11", "bg12", "bg13", "bg14", "bg15", "bg16", "bg17",
          "bg18", "bg30", "bg31", "bg32", "bg33", "bg34", "bg35", "bg36", "bg37", "bg38")


def audit(manifests: Path | Iterable[Path]) -> dict[str, object]:
    if isinstance(manifests, Path):
        manifests = (manifests,)
    manifests = tuple(manifests)
    available: dict[str, set[str]] = {stage: set() for stage in STAGES}
    source_archives: dict[str, set[str]] = {stage: set() for stage in STAGES}
    manifest_paths = [str(Path(manifest)) for manifest in manifests]
    for manifest in manifests:
        with Path(manifest).open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                path = row["path"].replace("\\", "/").strip("/")
                parts = path.split("/")
                if len(parts) >= 4 and parts[:2] == ["data", "background"]:
                    stage = parts[2].lower()
                    if stage in available:
                        available[stage].add("/".join(parts[3:]))
                        source_archives[stage].add(row["archive"])

    output = []
    for index, stage in enumerate(STAGES):
        files = available[stage]
        grid = index >= 16
        # A 30-cell renderer grid is a viewer convention, not proof that every
        # source stage contains 30 files. Report expected names separately from
        # resources actually present, and only call names in the folder
        # "unconnected" until the original constructor proves their role.
        # BG33's constructor (PE 0x473af0) allocates and loads exactly 24
        # grid tiles (four rows by six columns); other grid stages use the
        # common 30-slot convention. Keep the PE-backed count explicit so
        # unused row-five names aren't reported as missing assets.
        grid_rows = 4 if stage == "bg33" else 5
        expected_base = ([f"0000[{row:02}][{col:02}].cv2"
                          for row in range(1, grid_rows + 1) for col in range(1, 7)]
                         if grid else [f"0000_{tile:02}.cv2" for tile in range(30)])
        present_base = sorted(set(expected_base) & files)
        missing_base = sorted(set(expected_base) - files)
        used_by_current_viewer = set(expected_base)
        expected_aux: set[str] = set()
        expected_bitmaps: set[str] = set()
        expected_sprites: set[str] = set()
        if stage == "bg02":
            expected_aux |= {f"left/a{number:02}.cv2" for number in range(16)}
            expected_aux |= {f"center/b{number:02}.cv2" for number in range(16)}
            expected_aux |= {f"right/c{number:02}.cv2" for number in range(16)}
        elif stage == "bg04":
            expected_aux.add("cloud2.cv2")
        elif stage == "bg12":
            expected_aux |= {"tori1.cv2", "tori2.cv2"}
        elif stage == "bg33":
            expected_aux |= {"0001.cv2", "0002.cv2"}
        elif stage == "bg36":
            expected_aux |= {"clowd_l.cv2", "clowd_s.cv2", "tori1.cv2", "tori2.cv2"}
        elif stage == "bg37":
            # The pinned PE constructor 0x476990 allocates three auxiliary
            # sprite slots and loads only tori1 + the two cloud CV2s.
            expected_aux |= {"clowd_l.cv2", "clowd_s.cv2", "tori1.cv2"}
        elif stage == "bg38":
            # The pinned PE constructor 0x477310 allocates two slots for clouds.
            expected_aux |= {"clowd_l.cv2", "clowd_s.cv2"}
        if stage == "bg16":
            expected_bitmaps = {f"{number:04}.cv2" for number in range(1, 5)}
        if stage == "bg34":
            expected_aux |= {
                f"0001[{row:02}][{col:02}].cv2"
                for row in range(1, 6) for col in range(1, 7)
            }
            expected_bitmaps = {f"{number:04}.cv2" for number in range(1, 5)}
            expected_sprites = {f"object/objectFa{number:03}.cv2" for number in range(30)}
        expected_aux |= expected_bitmaps | expected_sprites
        present_aux = sorted(expected_aux & files)
        used_by_current_viewer |= expected_aux
        output.append({
            "stage": stage,
            "loader_mode": "grid-5x6" if grid else "flat-30",
            "folder_present": bool(files),
            "folder_files": len(files),
            "source_archives": sorted(source_archives[stage]),
            "expected_base_names": len(expected_base),
            "base_names_present": len(present_base),
            "missing_base_names": missing_base,
            "expected_aux_names": len(expected_aux),
            "aux_names_present": len(present_aux),
            "missing_aux_names": sorted(expected_aux - files),
            "bitmap_names_present": len(expected_bitmaps & files),
            "expected_bitmap_names": len(expected_bitmaps),
            "sprite_names_present": len(expected_sprites & files),
            "expected_sprite_names": len(expected_sprites),
            "unconnected_cv2": sorted(f for f in files if f.lower().endswith(".cv2") and f not in used_by_current_viewer),
            "files": sorted(files),
        })
    return {"source_manifests": manifest_paths, "stage_count": len(output), "stages": output}


def write_tsv(report: dict[str, object], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = ("stage", "loader_mode", "folder_present", "folder_files",
              "base_names_present", "expected_base_names", "missing_base_names",
              "source_archives", "aux_names_present", "expected_aux_names", "missing_aux_names",
              "bitmap_names_present", "expected_bitmap_names", "sprite_names_present",
              "expected_sprite_names", "unconnected_cv2")
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for stage in report["stages"]:
            row = dict(stage)
            row["missing_base_names"] = ",".join(row["missing_base_names"])
            row["missing_aux_names"] = ",".join(row["missing_aux_names"])
            row["source_archives"] = ",".join(row["source_archives"])
            row["unconnected_cv2"] = ",".join(row["unconnected_cv2"])
            writer.writerow({key: row[key] for key in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = audit(args.manifest)
    write_tsv(report, args.output)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"audited {report['stage_count']} stages -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
