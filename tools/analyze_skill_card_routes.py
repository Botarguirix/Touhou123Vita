#!/usr/bin/env python3
"""Cross-check Reimu skill-card IDs, input-handler actions, and PAT variants."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
CARD_ACTION = re.compile(r"FUN_00487ba0\((0x[0-9a-fA-F]+|\d+),")
CASE = re.compile(r"^\s*case\s+(0x[0-9a-fA-F]+|\d+):")


def extract_skill_switches(source: str) -> list[dict[str, object]]:
    lines = source.splitlines()
    switches: list[dict[str, object]] = []
    for start, line in enumerate(lines):
        if "switch(*puVar8)" not in line:
            continue
        depth = 0
        opened = False
        current_case: int | None = None
        cases: dict[int, list[int]] = defaultdict(list)
        for index in range(start, len(lines)):
            current = lines[index]
            match = CASE.match(current) if depth == 1 else None
            if match:
                current_case = int(match.group(1), 0)
            if current_case is not None:
                for call in CARD_ACTION.finditer(current):
                    action = int(call.group(1), 0)
                    if 500 <= action < 600:
                        cases[current_case].append(action)
            for char in current:
                if char == "{":
                    depth += 1
                    opened = True
                elif char == "}":
                    depth -= 1
            if opened and depth == 0:
                break
        switches.append({
            "line": start + 1,
            "card_actions": {str(key): values for key, values in sorted(cases.items())
                              if 100 <= key <= 111 and values},
        })
    return switches


def classify_ground_context(source: str, switches: list[dict[str, object]]) -> None:
    """Tie card switches to the true/false branches of Player::isGrounded()."""
    call = source.find("cVar3 = FUN_00463530();")
    if call < 0:
        raise ValueError("Reimu handler no longer calls the pinned isGrounded helper")
    condition = source.find("if (cVar3 == '\\0') {", call)
    if condition < 0:
        raise ValueError("Could not locate the isGrounded branch in Reimu handler")
    opening = source.find("{", condition)
    depth = 0
    closing = -1
    for position in range(opening, len(source)):
        if source[position] == "{":
            depth += 1
        elif source[position] == "}":
            depth -= 1
            if depth == 0:
                closing = position
                break
    if closing < 0:
        raise ValueError("Unbalanced isGrounded branch in Reimu handler")
    else_start = source.find("else {", closing, closing + 16)
    if else_start < 0:
        raise ValueError("Could not locate the grounded else branch")
    false_opening = source.find("{", else_start)
    depth = 0
    true_closing = -1
    for position in range(false_opening, len(source)):
        if source[position] == "{":
            depth += 1
        elif source[position] == "}":
            depth -= 1
            if depth == 0:
                true_closing = position
                break
    if true_closing < 0:
        raise ValueError("Unbalanced grounded branch in Reimu handler")

    false_branch = (opening, closing)
    true_branch = (false_opening, true_closing)
    for switch in switches:
        line_offset = sum(len(line) + 1 for line in source.splitlines()[:switch["line"] - 1])
        if false_branch[0] < line_offset < false_branch[1]:
            switch["context"] = "airborne"
            switch["context_evidence"] = "isGrounded() == false branch"
        elif true_branch[0] < line_offset < true_branch[1]:
            switch["context"] = "grounded"
            switch["context_evidence"] = "isGrounded() true branch"
        else:
            raise ValueError(f"Skill switch at line {switch['line']} is outside grounded/air branches")


def activation_gate(handler: str, project_root: Path) -> dict[str, object]:
    required_handler_fragments = (
        "sVar1 = *(short *)(param_1[0x57] + 0x12);",
        "uVar6 = *(uint *)(param_1[0x56] + 0x4c) & 0x200000;",
        "uVar10 = *(uint *)(param_1[0x56] + 0x4c) & 0x20;",
        "if ((short)param_1[0x213] != 0)",
        "if ((short)param_1[0x149] == 0)",
        "if (uVar10 == 0)",
        "FUN_00468e80(0)",
        "*(char *)((int)param_1 + 0x836) == '\\0'",
        "(sVar1 < 0x33)",
        "FUN_00456c80(0)",
        "FUN_00487ba0(500,iVar11)",
    )
    missing = [fragment for fragment in required_handler_fragments if fragment not in handler]
    if missing:
        raise ValueError(f"Pinned handler no longer matches the skill activation gate: {missing}")

    sources = {
        "player_hpp": project_root / "local/SokuLib/src/Player.hpp",
        "gameobject_hpp": project_root / "local/SokuLib/src/GameObject.hpp",
        "animationobject_hpp": project_root / "local/SokuLib/src/AnimationObject.hpp",
        "framedata_hpp": project_root / "local/SokuLib/src/FrameData.hpp",
        "inputmanager_hpp": project_root / "local/SokuLib/src/InputManager.hpp",
        "cards_hpp": project_root / "local/SokuLib/src/Cards.hpp",
    }
    metadata = {name: path.read_text(encoding="utf-8") for name, path in sources.items()}
    expected_definitions = {
        "player_hpp": ("short confusionDebuffTimer", "short stopwatchTimeLeft",
                       "bool isGrounded()", "bool canActivateCard(int slot)"),
        "gameobject_hpp": ("CharacterFrameData* frameData;",
                           "CharacterSequenceData* sequenceData;",
                           "CollisionType collisionType"),
        "animationobject_hpp": ("FrameData* frameData;", "} frameState;"),
        "framedata_hpp": ("bool cancellable: 1;", "short actionLock;"),
        "inputmanager_hpp": ("int spellcard;",),
        "cards_hpp": ("unsigned short id;", "unsigned short cost;"),
    }
    for name, fragments in expected_definitions.items():
        absent = [fragment for fragment in fragments if fragment not in metadata[name]]
        if absent:
            raise ValueError(f"SokuLib structure reference changed in {name}: {absent}")

    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest()
              for name, path in sources.items()}
    return {
        "skill_frame_requirement": {
            "frame_data_pointer_offset": "0x158",
            "frame_flags_offset": "0x4c",
            "cancellable_mask": "0x20",
            "high_jump_cancellable_mask": "0x200000",
            "gate": "requires cancellable (0x20); highJumpCancellable alone is insufficient",
        },
        "sequence_cancel_window": {
            "sequence_data_pointer_offset": "0x15c",
            "action_lock_offset": "0x12",
            "maximum_exclusive": 51,
            "passed_as_use_skill_second_argument": True,
        },
        "input": {
            "current_spellcard_key_offset": "0x770",
            "buffered_spellcard_key_offset": "0x790",
            "condition": "current spellcard key is 1 or 2, or buffered spellcard key is nonzero",
        },
        "status_gates": {
            "confusion_debuff_timer_offset": "0x524",
            "stopwatch_time_left_offset": "0x84c",
            "both_must_be_zero": True,
            "unidentified_player_byte_offset": "0x836",
            "unidentified_player_byte_must_be_zero": True,
        },
        "current_move_gate": {
            "action_id_offset": "0x13c",
            "collision_type_offset": "0x190",
            "condition": "action < 300 OR (collisionType != 0 AND collisionType != 3)",
        },
        "card_gate": {
            "hand_first_card_id_range": [100, 199],
            "can_activate_card_helper": "00468e80(slot=0)",
            "ground_routes": "all 12 skill cards",
            "air_routes": "8 explicit skill cards; four IDs have no air switch case",
        },
        "source_sha256": hashes,
    }


def load_skill_cards(path: Path) -> dict[int, dict[str, int]]:
    cards: dict[int, dict[str, int]] = {}
    with path.open(encoding="cp932", newline="") as stream:
        for row in csv.reader(stream):
            if len(row) < 4 or not row[0].isdigit():
                continue
            card_id = int(row[0])
            if 100 <= card_id <= 111:
                if row[2] != "1" or not row[3].isdigit():
                    raise ValueError(f"Card {card_id} is not a valid skill card row")
                cards[card_id] = {"type": int(row[2]), "skill_slot": int(row[3])}
    if set(cards) != set(range(100, 112)):
        raise ValueError(f"Expected skill-card metadata for IDs 100..111, found {sorted(cards)}")
    return cards


def load_deck(path: Path) -> list[int]:
    text = path.read_text(encoding="ascii").strip()
    deck = [int(value) for value in text.split(",") if value]
    return deck


def load_pat_actions(path: Path) -> dict[int, dict[str, object]]:
    stats: dict[int, dict[str, object]] = {}
    with path.open(encoding="cp932", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if row["path"].lower() != "data/character/reimu/reimu.pat":
                continue
            action = int(row["action"])
            if not 500 <= action < 600:
                continue
            stat = stats.setdefault(action, {"indices": set(), "poses": 0, "damaging_poses": 0})
            stat["indices"].add(int(row["index"]))
            stat["poses"] = int(stat["poses"]) + 1
            if int(row["damage"]) > 0 and row["attack_boxes"] != "-":
                stat["damaging_poses"] = int(stat["damaging_poses"]) + 1
    for stat in stats.values():
        stat["indices"] = sorted(stat["indices"])
    return stats


def analyze(exe: Path, handler_source: Path, spellcard_csv: Path, deck_csv: Path,
            pat_detail: Path, ghidra_manifest: Path) -> dict[str, object]:
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected reference executable SHA-256: {digest}")
    manifest = ghidra_manifest.read_text(encoding="utf-8", errors="replace")
    if not re.search(r"^vtable\t0085bf4c\t20\t004ae670$", manifest, re.MULTILINE):
        raise ValueError("Ghidra manifest does not tie Reimu slot 20 to 004ae670")
    if not re.search(r"^function\t004ae670\t.*\ttrue$", manifest, re.MULTILINE):
        raise ValueError("Ghidra manifest does not confirm a successful Reimu handler decompile")

    handler_text = handler_source.read_text(encoding="utf-8")
    switches = extract_skill_switches(handler_text)
    classify_ground_context(handler_text, switches)
    gate = activation_gate(handler_text, exe.resolve().parent.parent)
    card_switches = [s for s in switches if s["card_actions"]]
    if not card_switches:
        raise ValueError("No skill-card action switch found in Reimu handler")
    primary = max(card_switches, key=lambda item: len(item["card_actions"]))
    actions_by_card = {int(key): values for key, values in primary["card_actions"].items()}
    if set(actions_by_card) != set(range(100, 112)):
        raise ValueError(
            f"Primary skill switch must map all 12 skill cards; found {sorted(actions_by_card)}"
        )
    cards = load_skill_cards(spellcard_csv)
    deck = load_deck(deck_csv)
    pat = load_pat_actions(pat_detail)

    # SokuLib's CardInfo labels this field costOrSlot; preserve that local name.
    # The game handler supplies the action ID, while this table confirms the
    # card's slot and the PAT sequence(s) available to execute it.
    rows = []
    for card_id in range(100, 112):
        action_ids = actions_by_card[card_id]
        if len(action_ids) != 1:
            raise ValueError(f"Card {card_id} has ambiguous primary actions: {action_ids}")
        action = action_ids[0]
        if action not in pat:
            raise ValueError(f"Card {card_id} selects action {action}, absent from Reimu PAT")
        rows.append({
            "card_id": card_id,
            "card_type": cards[card_id]["type"],
            "cost_or_slot": cards[card_id]["skill_slot"],
            "in_default_deck": card_id in deck,
            "action_id": action,
            "pat_indices": pat[action]["indices"],
            "pat_poses": pat[action]["poses"],
            "pat_damaging_poses": pat[action]["damaging_poses"],
        })

    return {
        "schema": 3,
        "reference_sha256": digest,
        "character": "Reimu",
        "handler_va": "004ae670",
        "ghidra_handler_switches": card_switches,
        "complete_skill_card_switch_line": primary["line"],
        "complete_skill_card_switch_context": primary["context"],
        "activation_gate": gate,
        "skill_card_count": len(rows),
        "default_skill_cards": [card for card in deck if 100 <= card <= 111],
        "routes": rows,
        "input_sha256": {
            "handler_c": hashlib.sha256(handler_source.read_bytes()).hexdigest(),
            "spellcard_csv": hashlib.sha256(spellcard_csv.read_bytes()).hexdigest(),
            "deck_csv": hashlib.sha256(deck_csv.read_bytes()).hexdigest(),
            "pat_detail": hashlib.sha256(pat_detail.read_bytes()).hexdigest(),
            "ghidra_manifest": hashlib.sha256(ghidra_manifest.read_bytes()).hexdigest(),
        },
        "scope": (
            "Static Reimu skill-card-to-action cross-reference. The 12-case switch is in the "
            "grounded branch; the distinct eight-case switch is in the airborne branch. This "
            "does not recover all frame guards, card consumption, effects, or other characters."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path("original/th123.exe"))
    parser.add_argument("--handler", type=Path, default=Path(
        "artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/004ae670.c"))
    parser.add_argument("--spellcard", type=Path, default=Path("artifacts/extracted/data/csv/reimu/spellcard.csv"))
    parser.add_argument("--deck", type=Path, default=Path("artifacts/extracted/data/csv/reimu/deck.csv"))
    parser.add_argument("--pat-detail", type=Path, default=Path("artifacts/pat-detail.tsv"))
    parser.add_argument("--ghidra-manifest", type=Path, default=Path(
        "artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/manifest.tsv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/reimu-skill-card-routes.json"))
    args = parser.parse_args()
    report = analyze(args.exe, args.handler, args.spellcard, args.deck, args.pat_detail, args.ghidra_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"character=Reimu; skill_cards={report['skill_card_count']}; output={args.output}")


if __name__ == "__main__":
    main()
