#!/usr/bin/env python3
"""Summarize reachable-instruction mnemonic counts for pinned TH123 handlers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


def summarize(handler_map: Path, disassembly_dir: Path) -> dict[str, object]:
    handlers: list[dict[str, object]] = []
    with handler_map.open(encoding="utf-8", newline="") as stream:
        for entry in csv.DictReader(stream, delimiter="\t"):
            if entry.get("sha256") != EXPECTED_SHA256:
                raise ValueError(f"Unexpected handler map hash: {entry.get('sha256')}")
            character = entry["character"]
            address = entry["handleInputs_va"].lower()
            path = disassembly_dir / f"{address}.asm.tsv"
            if not path.is_file():
                raise ValueError(f"Missing disassembly for {character} at {address}")

            lines = path.read_text(encoding="utf-8").splitlines()
            if not lines or f"sha256={EXPECTED_SHA256}" not in lines[0]:
                raise ValueError(f"Disassembly hash mismatch for {character}")
            if f"character={character}" not in lines[0] or f"entry={address}" not in lines[0]:
                raise ValueError(f"Disassembly identity mismatch for {character}")
            if len(lines) < 2 or lines[1] != "address\tmnemonic\toperands":
                raise ValueError(f"Malformed disassembly table for {character}")

            instructions = 0
            malformed = 0
            mnemonics: Counter[str] = Counter()
            previous_address = -1
            for line in lines[2:]:
                columns = line.split("\t", 2)
                if len(columns) != 3:
                    malformed += 1
                    continue
                try:
                    instruction_address = int(columns[0], 16)
                except ValueError:
                    malformed += 1
                    continue
                if instruction_address <= previous_address or not columns[1]:
                    raise ValueError(f"Unsorted or invalid instruction row for {character}")
                previous_address = instruction_address
                instructions += 1
                mnemonics[columns[1].lower()] += 1

            handlers.append({
                "character": character,
                "entry_va": address,
                "instruction_count": instructions,
                "malformed_rows": malformed,
                "mnemonic_counts": dict(sorted(mnemonics.items())),
            })

    characters = [str(row["character"]) for row in handlers]
    if len(handlers) != 20 or len(set(characters)) != 20:
        raise ValueError(f"Expected 20 unique playable handlers, got {len(set(characters))}")

    totals: Counter[str] = Counter()
    for handler in handlers:
        totals.update(handler["mnemonic_counts"])  # type: ignore[arg-type]
    return {
        "schema": 1,
        "executable_sha256": EXPECTED_SHA256,
        "scope": (
            "Unique decoded instructions in the current bounded CFG walk per handleInputs entry; "
            "direct CALL targets are not traversed. Counts are static-analysis inventory, "
            "not semantic support or whole-program opcode coverage."
        ),
        "handler_count": len(handlers),
        "instruction_count": sum(int(row["instruction_count"]) for row in handlers),
        "aggregate_mnemonic_counts": dict(sorted(totals.items())),
        "handlers": handlers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handler_map", type=Path)
    parser.add_argument("disassembly_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = summarize(args.handler_map, args.disassembly_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"handlers={report['handler_count']}; instructions={report['instruction_count']}; "
        f"mnemonics={len(report['aggregate_mnemonic_counts'])}; output={args.output}"
    )


if __name__ == "__main__":
    main()
