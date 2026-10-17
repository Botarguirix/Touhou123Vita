#!/usr/bin/env python3
"""Summarize action dispatches and move-lock checks in exported handlers."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

HASH = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


def summarize(map_path: Path, export_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with map_path.open(encoding="utf-8", newline="") as stream:
        for entry in csv.DictReader(stream, delimiter="\t"):
            if entry["sha256"] != HASH:
                raise ValueError(f"Unexpected handler map hash: {entry['sha256']}")
            address = entry["handleInputs_va"]
            path = export_dir / f"{address}.c"
            text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
            actions = defaultdict(int)
            pushed_actions = defaultdict(int)
            locks = set()
            lock_counts = defaultdict(int)
            disassembly = export_dir / "disassembly" / f"{address}.asm.tsv"
            instructions = []
            if disassembly.exists():
                for line in disassembly.read_text(encoding="utf-8").splitlines():
                    columns = line.split("\t")
                    if len(columns) == 3 and re.fullmatch(r"[0-9a-f]{8}", columns[0]):
                        instructions.append((int(columns[0], 16), columns[1], columns[2]))
                for index, (_, mnemonic, operands) in enumerate(instructions):
                    pushed = re.fullmatch(r"(0x[0-9a-f]+|\d+)", operands)
                    if mnemonic == "push" and pushed:
                        value = int(pushed.group(1), 0)
                        if 400 <= value <= 434:
                            pushed_actions[value] += 1
                    if mnemonic == "call" and operands == "0x489610" and index:
                        prior = instructions[max(0, index - 3) : index]
                        for _, prior_mnemonic, prior_operands in reversed(prior):
                            pushed = re.fullmatch(r"(0x[0-9a-f]+|\d+)", prior_operands)
                            if prior_mnemonic == "push" and pushed:
                                lock_id = int(pushed.group(1), 0)
                                locks.add(lock_id)
                                lock_counts[lock_id] += 1
                                break
                    # This pattern is the virtual setAction call: push action;
                    # mov ecx,this; call [vtable + 8].
                    if mnemonic == "call" and operands == "edx" and index >= 2:
                        prior = instructions[index - 2 : index]
                        if prior[-1][1:3] == ("mov", "ecx, esi") and prior[0][1] == "push":
                            pushed = re.fullmatch(r"(0x[0-9a-f]+|\d+)", prior[0][2])
                            if pushed:
                                actions[int(pushed.group(1), 0)] += 1
            candidates = {
                action: max(count - lock_counts[action], actions.get(action, 0))
                for action, count in pushed_actions.items()
                if max(count - lock_counts[action], actions.get(action, 0)) > 0
            }
            dispatches = ",".join(f"{action}:{count}" for action, count in sorted(candidates.items()))
            lock_list = ",".join(str(value) for value in sorted(locks))
            export_status = "capstone-cfg" if disassembly.exists() else ("ghidra-c" if path.exists() else "missing")
            rows.append({
                "character": entry["character"], "handler": address, "export": export_status,
                "instructions": str(len(instructions)), "dispatches": dispatches, "lock_queries": lock_list,
            })
    if len(rows) != 20:
        raise ValueError(f"Expected 20 playable characters, got {len(rows)}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handler_map", type=Path)
    parser.add_argument("export_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = summarize(args.handler_map, args.export_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    exported = sum(row["export"] != "missing" for row in rows)
    print(f"characters={len(rows)}; disassemblies={exported}; output={args.output}")


if __name__ == "__main__":
    main()
