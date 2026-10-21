#!/usr/bin/env python3
"""Summarize selected action IDs passed to useSkill in pinned per-character PE CFGs."""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


def summarize(handler_map: Path, disassembly_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with handler_map.open(encoding="utf-8", newline="") as stream:
        for handler in csv.DictReader(stream, delimiter="\t"):
            if handler["sha256"] != EXPECTED_SHA256:
                raise ValueError(f"Unexpected PE hash for {handler['character']}")
            address = handler["handleInputs_va"]
            path = disassembly_dir / f"{address}.asm.tsv"
            lines = path.read_text(encoding="utf-8").splitlines()
            if not lines or f"sha256={EXPECTED_SHA256}" not in lines[0]:
                raise ValueError(f"Missing or stale disassembly: {path}")
            instructions = []
            for line in lines[2:]:
                columns = line.split("\t")
                if len(columns) == 3 and re.fullmatch(r"[0-9a-f]{8}", columns[0]):
                    instructions.append((int(columns[0], 16), columns[1], columns[2]))

            action_calls: list[tuple[int, int]] = []
            command_bits: set[int] = set()
            for index, (pc, mnemonic, operands) in enumerate(instructions):
                if mnemonic == "test" and re.search(r"\[esi \+ 0x7c8\]", operands):
                    match = re.search(r",\s*(0x[0-9a-f]+|\d+)\s*$", operands)
                    if match:
                        command_bits.add(int(match.group(1), 0))
                if mnemonic != "call" or operands != "0x487ba0":
                    continue
                action_id = None
                for _, prior_mnemonic, prior_operands in reversed(instructions[max(0, index - 10):index]):
                    if prior_mnemonic != "push":
                        continue
                    number = re.fullmatch(r"(0x[0-9a-f]+|\d+)", prior_operands)
                    if number:
                        candidate = int(number.group(1), 0)
                        if 400 <= candidate < 600:
                            action_id = candidate
                    # cdecl pushes action first and id last. Do not mistake a
                    # preceding immediate action for a register-supplied ID.
                    break
                if action_id is not None:
                    action_calls.append((pc, action_id))

            action_ids = sorted({action_id for _, action_id in action_calls})
            details = ",".join(
                f"{action_id}:{sum(candidate == action_id for _, candidate in action_calls)}"
                for action_id in action_ids
            )
            rows.append({
                "character": handler["character"],
                "handler": address,
                "cfg_instructions": str(len(instructions)),
                "useSkill_action_sites": str(len(action_calls)),
                "selected_action_count": str(len(action_ids)),
                "selected_actions_calls": details,
                "command_bit_tests": ",".join(f"0x{bit:x}" for bit in sorted(command_bits)),
            })
    if len(rows) != 20:
        raise ValueError(f"Expected exactly 20 playable handlers, got {len(rows)}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handler_map", type=Path)
    parser.add_argument("disassembly_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = summarize(args.handler_map, args.disassembly_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"handlers={len(rows)}; identified action call sites={sum(int(r['useSkill_action_sites']) for r in rows)}; output={args.output}")


if __name__ == "__main__":
    main()
