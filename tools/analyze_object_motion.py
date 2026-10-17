#!/usr/bin/env python3
"""Verify selected object-update dispatches and spawn transforms in th123.exe."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local/python-deps"))
import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, CS_GRP_JUMP, Cs
from capstone.x86 import X86_OP_IMM

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


def reachable_direct_calls(pe: pefile.PE, start_va: int) -> tuple[set[int], list[dict[str, str]]]:
    """Walk direct control flow from a handler; callees and indirect jumps are boundaries."""
    base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    pending, seen, calls = [start_va], set(), set()
    while pending and len(seen) < 20000:
        va = pending.pop()
        if va in seen:
            continue
        try:
            raw = pe.get_data(va - base, 15)
        except pefile.PEFormatError:
            continue
        instruction = next(decoder.disasm(raw, va, count=1), None)
        if instruction is None:
            continue
        seen.add(va)
        next_va = va + instruction.size
        if instruction.mnemonic == "call":
            if instruction.operands and instruction.operands[0].type == X86_OP_IMM:
                calls.add((va, instruction.operands[0].imm & 0xFFFFFFFF))
            pending.append(next_va)
        elif instruction.group(CS_GRP_JUMP):
            if instruction.operands and instruction.operands[0].type == X86_OP_IMM:
                pending.append(instruction.operands[0].imm & 0xFFFFFFFF)
            if instruction.mnemonic != "jmp":
                pending.append(next_va)
        elif instruction.mnemonic.startswith("ret") or instruction.mnemonic in ("int3", "ud2", "hlt"):
            continue
        else:
            pending.append(next_va)
    return seen, [{"callsite": hex(site), "target": hex(target)}
                  for site, target in sorted(calls)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exe", nargs="?", type=Path, default=Path("original/th123.exe"))
    args = parser.parse_args()
    raw = args.exe.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"unexpected executable SHA-256: {digest}")
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase

    def u32(va: int) -> int:
        offset = pe.get_offset_from_rva(va - base)
        return struct.unpack_from("<I", raw, offset)[0]

    def f64(va: int) -> float:
        offset = pe.get_offset_from_rva(va - base)
        return struct.unpack_from("<d", raw, offset)[0]

    def code(va: int, size: int) -> bytes:
        return pe.get_data(va - base, size)

    # FUN_007876d0 dispatches action IDs in [0x320, ...): first map the
    # action index to a group byte, then index the handler pointer table.
    # Reading the pointer table with the raw action index silently selected
    # unrelated callbacks in earlier versions of this report.
    object_actions = {
        "suwako_808_update": (0x328, 0x788D3E),
        "suwako_989_update": (0x320 + 189, 0x797884),
    }
    update_dispatch = {}
    for name, (action_id, expected) in object_actions.items():
        index = action_id - 0x320
        group = code(0x798B70 + index, 1)[0]
        actual = u32(0x798AA4 + group * 4)
        if actual != expected:
            raise SystemExit(f"{name} dispatch changed: action={action_id:#x}, group={group}, handler={actual:#x} != {expected:#x}")
        update_dispatch[name] = {"action_id": hex(action_id), "group": group, "handler": hex(actual)}
    suwako_808_entry = int(update_dispatch["suwako_808_update"]["handler"], 16)
    suwako_808_cfg, suwako_808_calls = reachable_direct_calls(pe, suwako_808_entry)
    suwako_808_reachable_calls = {
        "entry": update_dispatch["suwako_808_update"]["handler"],
        "reachable_instruction_count": len(suwako_808_cfg),
        "direct_calls": suwako_808_calls,
        "geometry_adapter_0x438fc0_reachable": any(call["target"] == "0x438fc0" for call in suwako_808_calls),
    }
    # The manager's virtual update slot calls one callback per linked object,
    # then removes the entry and its handle when the callback leaves +0x34c=0.
    # Pin the whole contract so future probes do not manually tick a dead item.
    manager_vtable = 0x85F28C
    manager_slots = {slot: u32(manager_vtable + slot * 4) for slot in (0, 1, 2, 4, 9)}
    expected_manager_slots = {0: 0x784170, 1: 0x784020, 2: 0x633E00,
                             4: 0x633CE0, 9: 0x4D2600}
    if manager_slots != expected_manager_slots:
        raise SystemExit(f"unexpected GameObject manager vtable: {manager_slots}")
    manager_update = code(0x633CE0, 0x25)
    if manager_update != bytes.fromhex(
        "8b 41 64 8b 90 70 01 00 00 66 83 ba a8 04 00 00 00 75 11 "
        "33 d2 b8 80 e3 4a 00 52 50 83 c1 04 e8 0c ff ff ff c3"):
        raise SystemExit("GameObject manager update wrapper changed")
    manager_iteration = code(0x633C10, 0xCD)
    if (bytes.fromhex("8b 4e 08 03 4c 24 24 ff 54 24 20") not in manager_iteration
            or bytes.fromhex("8b 4e 08 83 b9 4c 03 00 00 00 74 0e") not in manager_iteration):
        raise SystemExit("GameObject manager callback/+0x34c removal gate changed")
    if bytes.fromhex("e8 71 b0 e2 ff") not in manager_iteration:
        raise SystemExit("GameObject manager no longer removes the dead object's handle")
    manager_lifecycle = {
        "vtable": hex(manager_vtable),
        "update_slot": {"index": 4, "method": hex(manager_slots[4]),
                        "object_callback": "0x004ae380"},
        "iteration": "0x00633c10",
        "callback_then_termination_check": True,
        "termination_field": "object+0x34c",
        "zero_behavior": "unlink node, remove generational handle via 0x0045ed10, delete list node, decrement count",
        "evidence_level": "pinned disassembly contract; dynamic manager/factory loop not yet integrated into the harness",
    }
    # The action initializer uses a separate two-level table. Base object
    # initialization zeros vx/vy; Suwako 808's action-specific constructor
    # does not override either field.
    initializer_index = 0x328 - 0x320
    initializer_group = code(0x79ECD8 + initializer_index, 1)[0]
    initializer_handler = u32(0x79EC10 + initializer_group * 4)
    if initializer_group != 5 or initializer_handler != 0x7997AE:
        raise SystemExit(f"unexpected Suwako 808 initializer dispatch: group={initializer_group}, handler={initializer_handler:#x}")
    velocity_init = code(0x799000, 0x80)
    if bytes.fromhex("d9 ee 83 ec 20 53 55 56 8b f1 0f bf 86 3c 01 00 00 d9 96 f4 00 00 00 d9 96 f8 00 00 00") not in velocity_init:
        raise SystemExit("base initializer no longer zeros object horizontal/vertical velocity")
    suwako_808_sequence_zero = 0x788DCA  # sequence-zero branch inside 0x788d3e
    # Generic setPose only changes the selected PAT descriptor and refreshes
    # rendering. It does not itself publish CharacterFrameData box arrays.
    frame_selection_signatures = {
        "set_pose_stores_pose_and_selects_descriptor": (0x464B50, bytes.fromhex(
            "66 8b 44 24 04 66 89 81 40 01 00 00 e8 7f ff ff ff c2 04 00")),
        "descriptor_selector_publishes_render_frame": (0x464AE0, bytes.fromhex(
            "53 56 8b f1 8b 9e 5c 01 00 00 8b 43 04 85 c0 57 0f bf be 40")),
        "descriptor_selector_stride_and_frame_pointer": (0x464B18, bytes.fromhex(
            "8b 43 04 69 ff a8 00 00 00 03 c7 8b c8 89 86 58 01 00 00 89 86 50 01 00 00")),
        "descriptor_selector_duration_and_render_callback": (0x464B31, bytes.fromhex(
            "66 c7 86 42 01 00 00 00 00 66 8b 51 08 5f 66 89 96 4c 01 00 00 8b ce 5e 5b e9")),
    }
    for name, (address, expected) in frame_selection_signatures.items():
        actual = code(address, len(expected))
        if actual != expected:
            raise SystemExit(f"{name} changed: {actual.hex()} != {expected.hex()}")
    box_sync_signatures = {
        "box_sync_entry_and_previous_state": (0x465E10, bytes.fromhex(
            "83 ec 3c 53 55 56 8b f1 0f b7 86 84 01 00 00 8b 8e 90 01 00 00")),
        "box_sync_publishes_frame_and_sequence": (0x465E40, bytes.fromhex(
            "8b 86 58 01 00 00 39 86 c0 01 00 00 89 8e b8 01 00 00")),
        "box_sync_counts_attack_and_hurt_vectors": (0x465E7D, bytes.fromhex(
            "8b 50 6c 85 d2 75 04 33 c9 eb 08 8b 48 70 2b ca c1 f9 04 88 8e cb 01 00 00")),
        "box_sync_writes_hurt_and_hit_boxes": (0x465F7B, bytes.fromhex(
            "33 d2 bb e0 fc ff ff 8d 8e 20 02 00 00 8d 86 20 03 00 00")),
    }
    for name, (address, expected) in box_sync_signatures.items():
        actual = code(address, len(expected))
        if actual != expected:
            raise SystemExit(f"{name} changed: {actual.hex()} != {expected.hex()}")
    if code(0x47D1A7, 5) != bytes.fromhex("e8 64 8c fe ff"):
        raise SystemExit("object-manager path no longer calls 0x465e10 at 0x47d1a7")
    box_sync_contract = {
        "function": "0x465e10",
        "frame_source": "object+0x158 PAT descriptor; published to boxData.frameData +0x1c0 when changed",
        "sequence_source": "object+0x15c; published to boxData.sequenceData +0x1c4",
        "counts": {"hit_boxes": "descriptor+0x6c vector -> object+0x1cb",
                   "hurt_boxes": "descriptor+0x5c vector -> object+0x1cc"},
        "arrays": {"hurt": "object+0x1d0", "hit": "object+0x220",
                   "rotated_buffers": "object+0x270", "rotation_pointers": "object+0x320"},
        "known_object_manager_callsite": "0x47d1a7",
        "callsite_role": "object-manager update/setup path; collision resolution not established",
        "evidence_level": "pinned function and callsite bytes; original sync executed in the Unicorn factory probe",
    }
    collision_pipeline_signatures = {
        "manager_runs_projectile_pair_phase": (0x47D5C9, bytes.fromhex("e8 a2 f5 ff ff")),
        "manager_runs_character_pair_phase": (0x47D5D0, bytes.fromhex("e8 4b f8 ff ff")),
        "hit_count_gate": (0x47A5BE, bytes.fromhex("38 82 cb 01 00 00")),
        "hit_boxes_array": (0x47A608, bytes.fromhex("8d ac 10 20 02 00 00")),
        "hit_hurt_rotated_box_test": (0x47A637, bytes.fromhex("e8 d4 fa ff ff")),
        "hit_hurt_aabb_test": (0x47A651, bytes.fromhex("e8 ba f7 ff ff")),
        "hurt_count_gate": (0x47A74E, bytes.fromhex("38 82 cc 01 00 00")),
        "hurt_hurt_rotated_box_test": (0x47A7C7, bytes.fromhex("e8 44 f9 ff ff")),
        "hurt_hurt_aabb_test": (0x47A7E1, bytes.fromhex("e8 2a f6 ff ff")),
        "projectile_pair_dispatch": (0x47CEFF, bytes.fromhex("e8 6c fb ff ff")),
        "character_pair_dispatch": (0x47CF28, bytes.fromhex("e8 63 fa ff ff")),
    }
    for name, (address, expected) in collision_pipeline_signatures.items():
        actual = code(address, len(expected))
        if actual != expected:
            raise SystemExit(f"collision pipeline {name} changed: {actual.hex()} != {expected.hex()}")
    collision_pipeline = {
        "manager_pair_phases": {"projectile": "0x47cb70", "character": "0x47ce20"},
        "hitbox_vs_hurtbox": {
            "function": "0x47a5b0", "hit_count": "attacker+0x1cb",
            "hit_array": "attacker+0x220", "hurt_count": "target+0x1cc",
            "hurt_array": "target+0x1d0", "rotated_hit_pointers": "attacker+0x320",
            "rotated_hurt_pointers": "target+0x334",
            "tests": {"rotated": "0x47a110", "axis_aligned": "0x479e10"},
        },
        "hurtbox_vs_hurtbox": {
            "function": "0x47a740", "counts": "objectA/+0x1cc and objectB/+0x1cc",
            "arrays": "objectA/+0x1d0 and objectB/+0x1d0",
            "tests": {"rotated": "0x47a110", "axis_aligned": "0x479e10"},
        },
        "pair_dispatch": {"projectile": "0x47ca70", "character": "0x47c990"},
        "evidence_level": "pinned PE bytes show manager pair phases and hit/hurt rectangle traversal; exact damage/guard/priority response still needs dynamic pair trace",
    }
    frame_selection_contract = {
        "set_pose": "0x464b50 stores pose at object+0x140 and calls 0x464ae0",
        "selector": "0x464ae0 selects the current 0xa8-byte PAT descriptor and publishes it at object+0x158 and +0x150",
        "descriptor_side_effects": "resets subframe at +0x142, copies duration from descriptor+8 to +0x14c, then calls render setup 0x43a250",
        "copies_collision_boxes": False,
        "evidence_level": "pinned function-body bytes; collision boxData at +0x1c0 and box arrays are not written by these functions",
    }
    gravity = f64(0x857F78)
    if gravity != 0.20000000298023224:
        raise SystemExit(f"unexpected Suwako 808 gravity constant: {gravity}")
    split_signatures = {
        "sequence_zero_branch": (0x788D4B, bytes.fromhex("0f bf 86 3e 01 00 00 83 e8 00 74 73")),
        "split_guard": (0x788DCA, bytes.fromhex("66 83 be 6c 03 00 00 00 0f 85 cc 01 00 00")),
        "owner_action_gate_call": (0x788DD8, bytes.fromhex("6a 03 6a 00 6a 00 e8 ad 40 d0 ff 84 c0")),
        "child_one_action_808": (0x788EE2, bytes.fromhex("68 28 03 00 00 ff d0")),
        "child_two_action_808": (0x788F6C, bytes.fromhex("68 28 03 00 00 ff d2")),
        "split_latch": (0x788F73, bytes.fromhex("66 c7 86 6c 03 00 00 01 00")),
        "post_split_zero_velocity": (0x788FA4, bytes.fromhex("d9 ee d9 96 f4 00 00 00 d9 9e f8 00 00 00")),
        "sequence_one_gravity": (0x788D60, bytes.fromhex("d9 86 f8 00 00 00 dc 25 78 7f 85 00 d9 9e f8 00 00 00")),
        "bounded_random_helper": (0x4099F0, bytes.fromhex("56 e8 da fe ff ff 8b c8 83 c8 ff 33 d2 f7 74 24 08 33 d2 8b f0 8b c1 f7 f6 5e c3")),
        "floor_query_uses_object_x": (0x4397F0, bytes.fromhex("51 d9 81 ec 00 00 00 d9 1c 24 d9 ee d9 04 24 d8 d1 df e0 dd d9")),
        "808_initializer_passes_custom_angle_and_magnitude": (0x7997FE, bytes.fromhex("d9 40 04 d9 5c 24 04 d9 00 d9 1c 24 e8 f1 f3 c9 ff")),
        "808_initializer_targets_motion_subobject": (0x7997EF, bytes.fromhex("8d 4e 04 d9 96 1c 01 00 00 d9 9e 20 01 00 00 d9 40 04")),
        "transform_helper_stores_first_component": (0x438C00, bytes.fromhex("d9 44 24 04 56 51 d9 1c 24 8b f1 e8 e0 09 fd ff d8 4c 24 10 d9 9e f0 00 00 00")),
        "transform_helper_stores_second_component": (0x438C1A, bytes.fromhex("d9 44 24 0c d9 1c 24 e8 5a 09 fd ff d9 e0 83 c4 04 d8 4c 24 0c d9 9e f4 00 00 00")),
        "angle_lookup_scales_tenths_degrees": (0x4095F9, bytes.fromhex("d9 45 08 83 ec 08 d8 0d 2c 78 86 00")),
        "cosine_lookup_shifts_900_tenths": (0x40958F, bytes.fromhex("d8 0d 2c 78 86 00 d8 25 4c 15 87 00")),
    }
    for name, (address, expected) in split_signatures.items():
        actual = code(address, len(expected))
        if actual != expected:
            raise SystemExit(f"Suwako 808 {name} changed: {actual.hex()} != {expected.hex()}")
    owner_action_gate = code(0x48CE90, 0xC6)
    if bytes.fromhex("8b 86 64 03 00 00 0f b7 80 3c 01 00 00 66 3d 31 00 7e 06 66 3d 96 00 7c 24") not in owner_action_gate:
        raise SystemExit("owner action gate no longer checks the owning player's action range")
    if (bytes.fromhex("68 c8 00 00 00 e8 d3 bd fa ff") not in owner_action_gate
            or bytes.fromhex("68 c9 00 00 00 e8 94 bd fa ff") not in owner_action_gate):
        raise SystemExit("owner action gate effect-object routes changed")
    split_acceleration = f64(0x85B928)
    sequence_one_acceleration = f64(0x85AAF8)

    # FUN_00438fc0 adapts dynamic object bounds and signed metadata into the
    # generic transform setter FUN_00406d30. Its known callsites belong to the
    # 808 object's own update callback; they do not establish Player spawn data.
    geometry_signatures = {"geometry_adapter_call": (0x43900F, bytes.fromhex("e8 1c dd fc ff"))}
    for name, (address, expected) in geometry_signatures.items():
        actual = code(address, len(expected))
        if actual != expected:
            raise SystemExit(f"{name} changed: {actual.hex()} != {expected.hex()}")

    # Suwako's 418 handler at 0x76f3b4 applies a frame-dependent movement
    # adjustment, then creates object 808 through a separate odd-counter gate.
    # Pin both paths so the report does not conflate the frame window with the
    # projectile creation condition.
    suwako_418_signatures = {
        "frame_lower_bound_5": (0x76F3BD, bytes.fromhex("66 83 be 40 01 00 00 05")),
        "frame_upper_bound_17": (0x76F3E1, bytes.fromhex("66 83 be 40 01 00 00 11")),
        "counter_lower_bound_1": (0x76F43C, bytes.fromhex("0f b7 86 d0 07 00 00 66 3b c3")),
        "counter_upper_bound_19": (0x76F44C, bytes.fromhex("66 3d 13 00")),
        "counter_odd_gate": (0x76F456, bytes.fromhex("0f bf c8 81 e1 01 00 00 80")),
        "counter_increment": (0x76F51E, bytes.fromhex("66 01 9e d0 07 00 00")),
        "phase_seed_sequence_field_matches_di": (0x76F40A, bytes.fromhex("66 39 be 3e 01 00 00")),
        "phase_seed_substate_field_matches_di": (0x76F418, bytes.fromhex("66 39 be 42 01 00 00")),
        "phase_seed_frame_constant_10": (0x76F411, bytes.fromhex("bd 0a 00 00 00")),
        "phase_seed_frame_compare": (0x76F421, bytes.fromhex("66 39 ae 40 01 00 00")),
        "phase_seed_sequence_6": (0x76F561, bytes.fromhex("6a 06 8b ce e8 16 54 cf ff")),
        "phase_seed_timer_30": (0x76F56A, bytes.fromhex("6a 1e 8b ce e8 fd 82 d1 ff")),
        "counter_reset_to_one": (0x76F579, bytes.fromhex("66 89 9e d0 07 00 00")),
        # createObject(0x328) uses Player+0x158 as an integer spawn-offset
        # record: signed facing byte * record+0x98 for X and record+0x9c
        # subtracted from Player+0xf0 for Y.
        "spawn_offset_pointer": (0x76F4D3, bytes.fromhex("8b 8e 58 01 00 00")),
        "spawn_y_subtracts_record_9c": (0x76F4DD, bytes.fromhex("da a1 9c 00 00 00")),
        "spawn_x_scales_facing_by_record_98": (0x76F4E3, bytes.fromhex("0f af 81 98 00 00 00")),
        "create_object_808": (0x76F514, bytes.fromhex("68 28 03 00 00 e8 12 f6 cf ff")),
        # FUN_00464ae0 selects the current pose descriptor from the sequence
        # object at Player+0x15c and publishes it at Player+0x158.
        "pose_descriptor_sequence_pointer": (0x464AE4, bytes.fromhex("8b 9e 5c 01 00 00")),
        "pose_descriptor_index": (0x464AF0, bytes.fromhex("0f bf be 40 01 00 00")),
        "pose_descriptor_stride_0xa8": (0x464B1B, bytes.fromhex("69 ff a8 00 00 00")),
        "pose_descriptor_selected_pointer": (0x464B25, bytes.fromhex("89 86 58 01 00 00")),
    }
    for name, (address, expected) in suwako_418_signatures.items():
        actual = code(address, len(expected))
        if actual != expected:
            raise SystemExit(f"Suwako 418 {name} changed: {actual.hex()} != {expected.hex()}")

    phase_helpers = {
        "indexed_callback_lookup": (0x464980, bytes.fromhex(
            "8b 44 24 04 3d ff 00 00 00 77 17 8b 89 64 01 00 00 "
            "8b 14 81 89 54 24 04 b9 f8 f9 89 00 e9 ae d3 f9 ff")),
        "scaled_tick_accumulator": (0x487870, bytes.fromhex(
            "56 8b f1 d9 86 4c 05 00 00 da 4c 24 08 e8 ae 89 39 00 "
            "66 01 86 e4 05 00 00 5e c2 04 00")),
    }
    for name, (address, expected) in phase_helpers.items():
        actual = code(address, len(expected))
        if actual != expected:
            raise SystemExit(f"Suwako 418 phase helper {name} changed: {actual.hex()} != {expected.hex()}")

    offsets = {
        "alice_408_x_facing": f64(0x858EF0),
        "alice_408_y": f64(0x857B20),
        "alice_418_x": f64(0x8677B0),
        "alice_418_y": f64(0x857990),
    }
    expected_offsets = {
        "alice_408_x_facing": 60.0,
        "alice_408_y": 100.0,
        "alice_418_x": 0.0,
        "alice_418_y": 50.0,
    }
    if offsets != expected_offsets:
        raise SystemExit(f"unexpected Alice spawn constants: {offsets}")

    print(json.dumps({
        "sha256": digest,
        "update_dispatch": update_dispatch,
        "suwako_808_seq0_update": hex(suwako_808_sequence_zero),
        "generic_pat_frame_selection": frame_selection_contract,
        "gameobject_box_sync": box_sync_contract,
        "gameobject_collision_pipeline": collision_pipeline,
        "suwako_808_reachable_calls": suwako_808_reachable_calls,
        "suwako_gameobject_manager_lifecycle": manager_lifecycle,
        "suwako_808_motion_evidence": {
            "action_update_handler": "0x00788d3e",
            "action_initializer_handler": hex(initializer_handler),
            "sequence_zero_branch": hex(suwako_808_sequence_zero),
            "gravity_subtracted_from_vertical_velocity_per_tick": gravity,
            "sequence_zero_object_11c_scalar_delta": split_acceleration,
            "sequence_one_object_11c_scalar_delta": sequence_one_acceleration,
            "vertical_velocity_rule": "vy -= 0.2 in both sequence 0 and sequence 1 branches",
            "sequence_zero_split_guard": "object+0x36c == 0 and owner-action gate 0x48ce90 returns false",
            "owner_action_gate_0x48ce90": {
                "owner_action_range_when_first_argument_zero": [0x32, 0x95],
                "effect_ids": {"second_argument_count": "0xc8", "third_argument_count": "0xc9"},
                "action_808_call_arguments": [0, 0, 3],
                "effect_behavior": "when owner action is in range, spawn three 0xc9 effects and return true, suppressing the 808 split",
                "collision_geometry": False,
            },
            "sequence_zero_creates_two_child_action_808_objects": True,
            "split_latch_field": "object+0x36c = 1",
            "post_split_initialization": "zeros object vx/vy before boundary checks and common motion update",
            "split_custom_data": {
                "source": "two calls to bounded random helper 0x4099f0, not the stage query",
                "draws_per_child": [160, 6],
                "transforms": ["customData+0 = -10 - draw160", "customData+4 = 10 + draw6"],
                "draw_ranges_if_rng_is_uniform_u32": {"draw160": [0, 159], "draw6": [0, 5]},
                "initializer_use": "action initializer passes customData[0] and customData[1] to 0x438c00 as angle and magnitude",
                "angle_lookup": "sine table at 0.1-degree resolution (angle*10 modulo 3600)",
                "transform_components": {
                    "object_plus_0xf4": "sin(angle_degrees) * magnitude",
                    "object_plus_0xf8": "cos(angle_degrees) * magnitude",
                },
            },
            "stage_floor_helper": "0x4397f0 queries stage ground using object.x; its result gates the split branch",
            "initializer_zeroes_horizontal_and_vertical_velocity": True,
            "initializer_does_not_override_velocity": True,
            "child_spawn_coordinates": "child world position inherits parent x/y; custom animation data uses bounded random offsets above",
            "lifetime_conditions": "sequence and stage-boundary exits remain to be mapped",
        },
        "spawn_transforms": {
            "alice_408": {"x": "owner.x + facing * 60", "y": "owner.y + 100", "sequence": 19},
            "alice_418": {"x": "owner.x", "y": "owner.y + 50", "sequences": {"21": [2, 4], "23": [3, 5]}},
            "suwako_408": {"x": "owner.x", "y": "owner.y", "sequence": 5},
            "suwako_418": {"x": "owner.x + signed_facing * s32(Player+0x158+0x98)", "y": "owner.y - s32(Player+0x158+0x9c)", "sequence": 0, "evidence": "x86 createObject callsite; offset values unresolved"},
        },
        "suwako_418_spawn_contract": {
            "handler": "0x0076f3b4",
            "animation_fields": {"0x13e": "sequence index", "0x140": "pose index", "0x142": "elapsed pose ticks"},
            "frame_adjustment_window_inclusive": [5, 17],
            "frame_adjustment_field": "object+0x0f4",
            "object_counter_window_inclusive": [1, 19],
            "spawn_when_counter_is_odd": True,
            "counter_increment": 1,
            "counter_seed_state": {"sequence_field_0x13e": "equals live DI sentinel", "substate_field_0x142": "equals live DI sentinel", "frame_field_0x140": 10},
            "counter_seed_value": 1,
            "create_object": {
                "callsite": "0x0076f514",
                "object_id": "0x328 (808)",
                "facing_source": "signed byte Player+0x104",
                "offset_record_pointer": "Player+0x158",
                "x_expression": "Player+0xec + signed_facing * s32([Player+0x158]+0x98)",
                "y_expression": "Player+0xf0 - s32([Player+0x158]+0x9c)",
                "sequence": 0,
                "offset_values": "unresolved; do not substitute PAT 808 sprite ox/oy",
            },
            "offset_record_source": {
                "selector": "0x00464ae0",
                "sequence_object": "Player+0x15c",
                "frame_array_pointer": "[Player+0x15c]+0x04",
                "frame_index": "Player+0x140",
                "frame_stride": "0xa8 bytes",
                "selected_frame_pointer_written_to": ["Player+0x158", "Player+0x150"],
                "unknown": "which PAT fields are loaded at selected_descriptor+0x98/+0x9c",
            },
            "seed_transition_calls": {"0x00464980_argument": 6, "0x00487870_argument": 30},
            "seed_transition_effects": {
                "0x00464980": "reads callback pointer object+0x164[6] and dispatches it through global context 0x0089f9f8; concrete callback effect unresolved",
                "0x00487870": "scales argument 30 by float object+0x54c, converts it through 0x00820230, and accumulates AX into object+0x5e4; timebase/meaning unresolved",
            },
            "parity_note": "the port maps +0x140 to PAT pose and advances +0x7d0 per fight tick; DI=sequence0/subframe0 is an explicit hypothesis until a PC trace confirms it, and projectile transforms/damage remain provisional",
        },
        "alice_update_anchor_y": {"owner_state_150_153": 110.0, "owner_state_154_157": 60.0, "owner_state_158": 100.0},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
