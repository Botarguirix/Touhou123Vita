#!/usr/bin/env python3
"""Validate character update jump-table cases that seed Player+0x884."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
sys.path.insert(0, str(ROOT / "local" / "python-deps"))

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

CASES = (
    ("Reimu", 0x490490, 0x4A7854, 0x490795, 16, None),
    ("Marisa", 0x4BD430, 0x4D023C, 0x4BD6F2, 16, None),
    ("Alice", 0x5100B0, 0x51E18C, 0x51026A, 16, None),
    ("Patchouli", 0x541290, 0x553C7C, 0x5414CD, 16, None),
    ("Chirno", 0x6E31A0, 0x6F54CC, 0x6E33CE, 16, None),
    ("Meirin", 0x71A5E0, 0x72C0C0, 0x71A81E, 16, None),
    ("Sanae", 0x73C1B0, 0x74A8A0, 0x73C3DD, 16, None),
    ("Suwako", 0x765AB0, 0x7819E4, 0x765EBB, 16, None),
    ("Utsuho", 0x79F440, 0x7B4F60, 0x79F78B, 16, None),
    # RTTI identifies this additional Player-derived class as Namazu.
    ("Namazu", 0x7D4400, 0x7EA138, 0x7D47B2, 1, 0x85F824),
)


def _register_family(md: Cs, register: int) -> str:
    name = md.reg_name(register)
    aliases = {"ax": "eax", "al": "eax", "ah": "eax",
               "bx": "ebx", "bl": "ebx", "bh": "ebx",
               "cx": "ecx", "cl": "ecx", "ch": "ecx",
               "dx": "edx", "dl": "edx", "dh": "edx",
               "si": "esi", "di": "edi", "bp": "ebp", "sp": "esp"}
    return aliases.get(name, name)


def _constant_register_value(md: Cs, instructions: list, stop: int,
                             register: int) -> int | None:
    values: dict[str, int] = {}
    for instruction in instructions[:stop]:
        if len(instruction.operands) < 2 or instruction.operands[0].type != X86_OP_REG:
            continue
        destination = _register_family(md, instruction.operands[0].reg)
        source = instruction.operands[1]
        if instruction.mnemonic == "mov" and source.type == X86_OP_IMM:
            values[destination] = source.imm
        elif (instruction.mnemonic == "xor" and source.type == X86_OP_REG and
              destination == _register_family(md, source.reg)):
            values[destination] = 0
        elif instruction.mnemonic == "lea" and source.type == X86_OP_MEM:
            base = (_register_family(md, source.mem.base)
                    if source.mem.base else "")
            if base in values and not source.mem.index:
                values[destination] = values[base] + source.mem.disp
        elif (instruction.mnemonic in ("add", "sub") and
              source.type == X86_OP_IMM and destination in values):
            values[destination] += source.imm * (1 if instruction.mnemonic == "add" else -1)
    return values.get(_register_family(md, register))


def scan(exe: Path, roster: Path,
         system_cards: Path | None = None) -> dict[str, object]:
    image = exe.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"reference PE SHA-256 mismatch: {digest}")
    pe = pefile.PE(data=image, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    with roster.open(encoding="utf-8") as roster_file:
        rows = {row["character"]: row for row in csv.DictReader(
            roster_file, delimiter="\t")}
    if system_cards is None:
        system_cards = ROOT / "artifacts/extracted/data/csv/common/spellcard.csv"
    system_cards_digest = hashlib.sha256(system_cards.read_bytes()).hexdigest()
    with system_cards.open(encoding="cp932", newline="") as card_file:
        system_card_ids = sorted({int(row[0]) for row in csv.reader(card_file)
                                  if row and row[0].strip().isdigit() and
                                  len(row) > 2 and row[2] == "0"})
    results = []
    for character, update, jump_table, target, table_size, known_vtable in CASES:
        roster_name = "Meirin" if character == "Meirin" else character
        if known_vtable is None and roster_name not in rows:
            raise ValueError(f"{character} missing from character vtable manifest")
        vtable = (known_vtable if known_vtable is not None else
                  int(rows[roster_name]["vtable_va"], 16))
        slot10 = struct.unpack("<I", pe.get_data(vtable - base + 10 * 4, 4))[0]
        table_targets = struct.unpack("<" + "I" * table_size,
                                      pe.get_data(jump_table - base, table_size * 4))
        if slot10 != update:
            raise ValueError(f"{character} slot10 mismatch: {slot10:#x}")
        if target not in table_targets:
            raise ValueError(f"{character} case {target:#x} is absent from {jump_table:#x}")
        rtti_name = None
        if known_vtable is not None:
            locator = struct.unpack("<I", pe.get_data(vtable - base - 4, 4))[0]
            type_descriptor = struct.unpack("<I", pe.get_data(locator - base + 12, 4))[0]
            rtti_name = pe.get_data(type_descriptor - base + 8, 80).split(b"\0", 1)[0].decode("ascii")
            if rtti_name != ".?AVNamazu@@":
                raise ValueError(f"unexpected RTTI for {character}: {rtti_name}")
        raw = pe.get_data(target - base, 15)
        ins = next(md.disasm(raw, target, count=1), None)
        if (ins is None or ins.mnemonic != "mov" or len(ins.operands) != 2 or
                ins.operands[0].type != X86_OP_MEM or
                ins.operands[0].mem.disp != 0x884 or
                ins.operands[1].type != X86_OP_REG):
            raise ValueError(f"unexpected field-seed instruction at {target:#x}")
        instructions = list(md.disasm(pe.get_data(update - base, target - update), update))
        setup = []
        for prior in instructions:
            if (prior.mnemonic == "mov" and len(prior.operands) == 2 and
                    prior.operands[0].type == X86_OP_REG and
                    prior.operands[1].type == X86_OP_IMM and
                    prior.operands[1].imm == 0x12C):
                setup.append({"address": hex(prior.address),
                              "instruction": f"{prior.mnemonic} {prior.op_str}"})
        if not setup:
            raise ValueError(f"no 300-frame register setup found for {character}")
        jump_index = next((index for index, prior in enumerate(instructions)
                           if prior.mnemonic == "jmp" and prior.operands and
                           prior.operands[0].type == X86_OP_MEM and
                           prior.operands[0].mem.disp == jump_table), None)
        if jump_index is None:
            raise ValueError(f"jump dispatch missing for {character}")
        mode_check = next((prior for prior in instructions[:jump_index]
                           if prior.mnemonic == "cmp" and len(prior.operands) == 2 and
                           prior.operands[0].type == X86_OP_MEM and
                           prior.operands[0].mem.disp == 0x7CC), None)
        hand_count_check = next((prior for prior in instructions[:jump_index]
                                 if prior.mnemonic == "cmp" and len(prior.operands) == 2 and
                                 prior.operands[0].type == X86_OP_MEM and
                                 prior.operands[0].mem.disp == 0x5E6), None)
        deque_get = next((prior for prior in instructions[:jump_index]
                          if prior.mnemonic == "call" and prior.operands and
                          prior.operands[0].type == X86_OP_IMM and
                          prior.operands[0].imm == 0x456C80), None)
        if mode_check is None or hand_count_check is None or deque_get is None:
            raise ValueError(f"card/input-type gates missing for {character}")
        mode_operand = mode_check.operands[1]
        mode_value = (mode_operand.imm if mode_operand.type == X86_OP_IMM else
                      _constant_register_value(md, instructions,
                                              instructions.index(mode_check),
                                              mode_operand.reg)
                      if mode_operand.type == X86_OP_REG else None)
        count_operand = hand_count_check.operands[1]
        if (mode_value != 2 or count_operand.type != X86_OP_IMM or
                count_operand.imm != 1):
            raise ValueError(f"unexpected input-type/card-count gate for {character}")
        mapping_load = next((prior for prior in reversed(instructions[:jump_index])
                             if prior.mnemonic == "movzx" and len(prior.operands) == 2 and
                             prior.operands[1].type == X86_OP_MEM), None)
        bound_index = next((index for index in range(jump_index - 1, -1, -1)
                            if instructions[index].mnemonic == "cmp" and
                            len(instructions[index].operands) == 2 and
                            instructions[index].operands[0].type == X86_OP_REG and
                            _register_family(md, instructions[index].operands[0].reg) == "eax"), None)
        if mapping_load is None or bound_index is None:
            raise ValueError(f"mapping or upper-bound check missing for {character}")
        bound_check = instructions[bound_index]
        bound_operand = bound_check.operands[1]
        if bound_operand.type == X86_OP_IMM:
            maximum_value = bound_operand.imm
        elif bound_operand.type == X86_OP_REG:
            maximum_value = _constant_register_value(md, instructions, bound_index,
                                                     bound_operand.reg)
        else:
            maximum_value = None
        if maximum_value is None or not 0 <= maximum_value <= 31:
            raise ValueError(f"upper-bound register unresolved for {character}")
        mapping_base = mapping_load.operands[1].mem.disp
        if mapping_base != jump_table + 4:
            raise ValueError(f"unexpected mapping table placement for {character}")
        mapping_bytes = list(pe.get_data(mapping_base - base, maximum_value + 1))
        selected_values = [value for value, mapped in enumerate(mapping_bytes)
                           if mapped < len(table_targets) and
                           table_targets[mapped] == target]
        if mapping_bytes != [0] * (maximum_value + 1):
            raise ValueError(f"{character} mapping is not zero through {maximum_value}")
        if table_targets[0] != target or selected_values != list(range(maximum_value + 1)):
            raise ValueError(f"{character} accepted range does not select seed case")
        results.append({
            "character": character,
            "rtti_name": rtti_name,
            "vtable": hex(vtable),
            "slot10_update": hex(slot10),
            "jump_table": hex(jump_table),
            "jump_table_targets": len(table_targets),
            "input_type_gate_instruction": f"{mode_check.mnemonic} {mode_check.op_str}",
            "input_type_gate_value": mode_value,
            "hand_count_gate_instruction": f"{hand_count_check.mnemonic} {hand_count_check.op_str}",
            "deque_element_index": 0,
            "deque_indexer": hex(deque_get.operands[0].imm),
            "mapping_load": hex(mapping_load.address),
            "mapping_base": hex(mapping_base),
            "upper_bound_instruction": f"{bound_check.mnemonic} {bound_check.op_str}",
            "maximum_dequeued_value": maximum_value,
            "mapping_bytes_through_maximum": mapping_bytes,
            "dequeued_values_selecting_seed_case": selected_values,
            "system_card_ids_in_dispatch_range": [value for value in system_card_ids
                                                   if value in selected_values],
            "case_target": hex(target),
            "assignment": f"{ins.mnemonic} {ins.op_str}",
            "seed_register": md.reg_name(ins.operands[1].reg),
            "preparations_of_300": setup,
            "seed_300_register_present": bool(setup),
        })
    # Supplement the known vtable cases with a reproducible linear sweep of
    # executable sections. This finds direct references outside the roster
    # input manifest (including the separate Namazu class). Skip-data mode is
    # used to continue after padding; candidates still need semantic review.
    linear_references = []
    md.skipdata = True
    for section in pe.sections:
        if not section.Characteristics & 0x20000000:
            continue
        section_start = base + section.VirtualAddress
        for instruction in md.disasm(section.get_data(), section_start):
            if instruction.id == 0:
                continue
            for operand in instruction.operands:
                if (operand.type == X86_OP_MEM and
                        (operand.mem.disp & 0xFFFFFFFF) == 0x884):
                    linear_references.append({
                        "address": hex(instruction.address),
                        "mnemonic": instruction.mnemonic,
                        "instruction": instruction.op_str,
                    })
                    break
    return {
        "exe_sha256": digest,
        "field_displacement": "0x884",
        "method_slot": 10,
        "case_count": len(results),
        "cases": results,
        "linear_text_field_references": linear_references,
        "common_type_zero_card_ids": system_card_ids,
        "common_spellcard_csv_sha256": system_cards_digest,
        "scope": "Validates ten slot10 entries (nine roster characters and the RTTI-identified Namazu class), their input-type +0x7cc==2 and hand-count>=1 gates, deque index 0 through 0x456c80, jump-table seed stores, the 0x12c setup, runtime value bounds, and mapping bytes selecting case zero. Includes a linear executable-section sweep of direct 0x884 references; this sweep is candidate evidence, not function-aware disassembly. Cross-checks deque values against type-0 IDs in common/spellcard.csv. It does not prove natural runtime reachability or the timer's full gameplay effect.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--roster", type=Path, default=ROOT / "artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/character-input/vtable-handlers.tsv")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/player-field-884-jumptable-cases.json")
    args = parser.parse_args()
    result = scan(args.exe, args.roster)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": result["case_count"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
