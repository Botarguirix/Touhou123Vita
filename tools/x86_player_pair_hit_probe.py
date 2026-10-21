#!/usr/bin/env python3
"""Run the original TH123 Player-vs-Player hit resolver on authored PAT frames."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "local/python-deps"))

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ECX,
    UC_X86_REG_EDI, UC_X86_REG_EDX,
    UC_X86_REG_EIP, UC_X86_REG_ESI, UC_X86_REG_ESP,
)
from tools.extract_pat_pose_metadata import action_sequence_metadata, read_pat
from tools.x86_remilia_412_action_setter_probe import PAT_LOOKUP
from tools.x86_remilia_412_spawn_probe import (
    initialize_object_manager, initialize_original_action,
    run_original_hit_hurt_pair, u32,
)
from tools.x86_suwako_808_factory_probe import (
    HEAP, LIST, OWNER, PAT_MAP, STACK, STOP, Suwako808FactoryProbe,
)

PLAYER_VTABLES = {"remilia": 0x0085D284, "suika": 0x0085DA84,
                  "udonge": 0x0085DD5C}


def run(dat_dir: Path = ROOT / "original", character: str = "remilia",
        action_id: int | None = None, attack_sequence: int = 0,
        attack_frame: int | None = None,
        positions: tuple[tuple[float, float], tuple[float, float]] =
        ((320.0, 180.0), (320.0, 180.0)),
        facings: tuple[int, int] = (1, -1)) -> dict[str, object]:
    exe = dat_dir / "th123.exe"
    if character not in PLAYER_VTABLES:
        raise ValueError(f"unsupported character fixture: {character}")
    pat_path = f"data/character/{character}/{character}.pat"
    pat_record = read_pat(dat_dir / "th123c.dat", pat_path)
    if pat_record is None:
        raise FileNotFoundError(f"{character} PAT not found in th123c.dat")
    pat = pat_record[0]
    if action_id is None:
        action_id = 320 if character == "remilia" else 521
    attack_sequences = action_sequence_metadata(pat, action_id, effective=True)
    selected_attack_sequence = next((entry for entry in attack_sequences
                                     if int(entry["sequence"]) == attack_sequence), None)
    if selected_attack_sequence is None:
        raise ValueError(f"action {action_id} sequence {attack_sequence} missing for {character}")
    attack_frames = selected_attack_sequence["frames"]
    if attack_frame is None:
        attack_frame = 3 if character == "remilia" else next(
            (index for index, frame in enumerate(attack_frames)
             if frame["damage"] and frame["attack_boxes"]), -1)
    if attack_frame < 0 or attack_frame >= len(attack_frames):
        raise ValueError(f"attack frame {attack_frame} out of range for {character}/{action_id}/{attack_sequence}")
    target_action_id = 321 if character == "remilia" else 400
    target_sequences = action_sequence_metadata(pat, target_action_id, effective=True)
    target_sequence = next((entry for entry in target_sequences
                            if int(entry["sequence"]) == 0), None)
    if target_sequence is None:
        raise ValueError(f"target action {target_action_id}/0 missing for {character}")
    target_frames = target_sequence["frames"]
    attacker, defender = LIST + 0x8000, LIST + 0xA000
    attacker_map, defender_map = PAT_MAP, PAT_MAP + 0x40000

    probe = Suwako808FactoryProbe(exe, dat_dir, character=character, action_id=801,
                                  intercept_box_transforms=False)
    uc = probe.uc
    box_transform_entries: list[dict[str, object]] = []

    def capture_original_box_transform(machine, address, _size, _user):
        if address not in (0x004640B0, 0x00464200):
            return
        esp = machine.reg_read(UC_X86_REG_ESP)
        source = u32(machine, esp + 4)
        destination = u32(machine, esp + 8)
        obj = machine.reg_read(UC_X86_REG_ECX)
        box_transform_entries.append({"helper": hex(address), "source": hex(source),
                                      "destination": hex(destination), "object": hex(obj),
                                      "position": [struct.unpack("<f", machine.mem_read(obj + 0xEC, 4))[0],
                                                   struct.unpack("<f", machine.mem_read(obj + 0xF0, 4))[0]]})

    # The probe's general factory runner clears its own diagnostics per run;
    # keep this independent trace for the separately executed two-player path.
    uc.hook_add(UC_HOOK_CODE, capture_original_box_transform)
    # The extra action-50 PAT fixture uses a non-overlapping region after the
    # two player maps and ends below the separately mapped emulated heap.
    uc.mem_map(PAT_MAP + 0x80000, 0x50000)
    uc.mem_write(LIST, bytes(0x10000))
    uc.mem_write(OWNER, bytes(0x10000))
    probe.heap_cursor = HEAP
    initialize_object_manager(probe)
    probe._pat_lookup_results = {}
    probe._pat_lookup_action_results = {}

    # 0x479cb0 calls EffectManager_Effect::CreateEffect through the global
    # secondary manager interface at 0x8985f0. The full effect factory needs
    # game resources, so provide an observable, signature-correct host stub.
    effect_manager, effect_vtable, effect_create_stub = OWNER + 0x8000, OWNER + 0x7000, 0x0047D000
    synthetic_effect = OWNER + 0x9000
    uc.mem_write(effect_manager, struct.pack("<I", effect_vtable))
    uc.mem_write(effect_vtable + 0x0C, struct.pack("<I", effect_create_stub))
    uc.mem_write(synthetic_effect, bytes(0x400))
    uc.mem_write(synthetic_effect, struct.pack("<I", 0x00858AB4))
    uc.mem_write(0x008985F0, struct.pack("<I", effect_manager))
    effect_requests: list[dict[str, object]] = []
    damage_checkpoints: list[dict[str, str]] = []
    damage_scale_events: list[dict[str, object]] = []
    damage_branch_events: list[dict[str, object]] = []
    reaction_selection: list[dict[str, str]] = []
    pat_lookup_events: list[dict[str, str]] = []
    cleanup_dispatches: list[dict[str, str]] = []
    exception_events: list[dict[str, object]] = []

    # Resolve each Player's independent PAT map through one shared hook.
    def pat_lookup(machine, address: int, _size: int, _user: object) -> None:
        if address != PAT_LOOKUP:
            return
        esp = machine.reg_read(UC_X86_REG_ESP)
        key = machine.reg_read(UC_X86_REG_ECX)
        action_key_ptr = u32(machine, esp + 8)
        action_id = u32(machine, action_key_ptr)
        result = probe._pat_lookup_action_results.get(
            (key, action_id), probe._pat_lookup_results.get(key))
        if result is None:
            raise RuntimeError(f"unmapped PAT lookup key {key:#x}, action {action_id}")
        output_pair = u32(machine, esp + 4)
        machine.mem_write(output_pair, bytes(machine.mem_read(result, 8)))
        pat_lookup_events.append({"map": hex(key), "action": str(action_id),
                                  "backing_result": hex(result),
                                  "output_pair": hex(output_pair)})
        ret = u32(machine, esp)
        machine.reg_write(UC_X86_REG_EAX, output_pair)
        machine.reg_write(UC_X86_REG_ESP, esp + 12)
        machine.reg_write(UC_X86_REG_EIP, ret)

    def effect_create(machine, address: int, _size: int, _user: object) -> None:
        if address != effect_create_stub:
            return
        esp = machine.reg_read(UC_X86_REG_ESP)
        args = [u32(machine, esp + 4 * index) for index in range(1, 7)]
        effect_requests.append({"manager": hex(machine.reg_read(UC_X86_REG_ECX)),
                                "arguments_u32": [hex(value) for value in args],
                                "x": struct.unpack("<f", struct.pack("<I", args[1]))[0],
                                "y": struct.unpack("<f", struct.pack("<I", args[2]))[0]})
        machine.reg_write(UC_X86_REG_EAX, synthetic_effect)
        machine.reg_write(UC_X86_REG_ESP, esp + 4 + 6 * 4)  # thiscall + six stack args
        machine.reg_write(UC_X86_REG_EIP, u32(machine, esp))

    def reaction_virtual(machine, address: int, _size: int, _user: object) -> None:
        if address in (0x47AED5, 0x47AF05, 0x47AF61):
            frame = machine.reg_read(UC_X86_REG_EBP)
            damage_scale_events.append({
                "pc": hex(address), "eax": hex(machine.reg_read(UC_X86_REG_EAX)),
                "ax": machine.reg_read(UC_X86_REG_EAX) & 0xFFFF,
                "ebp": hex(frame),
                "edi": hex(machine.reg_read(UC_X86_REG_EDI)),
                "edi_198": struct.unpack("<f", machine.mem_read(machine.reg_read(UC_X86_REG_EDI) + 0x198, 4))[0],
                "frame_fields": [struct.unpack("<h", machine.mem_read(frame + off, 2))[0]
                                 for off in (0x1C, 0x20, 0x24, 0x2A, 0x2C)],
                "player_198": struct.unpack("<f", machine.mem_read(attacker + 0x198, 4))[0],
                "data_4b0": struct.unpack("<f", machine.mem_read(u32(machine, attacker + 0x16C) + 0x4B0, 4))[0],
            })
        if address in (0x47AE11, 0x47AE3A, 0x47AE70):
            esp = machine.reg_read(UC_X86_REG_ESP)
            damage_branch_events.append({
                "pc": hex(address), "stack_byte_esp13": int(machine.mem_read(esp + 0x13, 1)[0]),
                "global_8971c0": u32(machine, 0x008971C0),
                "global_8971cc": struct.unpack("<h", machine.mem_read(0x008971CC, 2))[0],
                "frame_flags_4c": u32(machine, u32(machine, attacker + 0x158) + 0x4C),
                "attack_flags_50": u32(machine, u32(machine, attacker + 0x158) + 0x50),
            })
        if address == 0x47AF61:
            data = u32(machine, attacker + 0x16C)
            own_stats = u32(machine, attacker + 0x168)
            enemy_stats = u32(machine, attacker + 0x170)
            combat = u32(machine, attacker + 0x1C0)
            damage_scale_events.append({
                "pc": hex(address), "eax": hex(machine.reg_read(UC_X86_REG_EAX)),
                "ax": machine.reg_read(UC_X86_REG_EAX) & 0xFFFF,
                "action": struct.unpack("<H", machine.mem_read(attacker + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", machine.mem_read(attacker + 0x13E, 2))[0],
                "pose": struct.unpack("<H", machine.mem_read(attacker + 0x140, 2))[0],
                "frame_damage": struct.unpack("<H", machine.mem_read(combat + 0x1C, 2))[0],
                "player_multipliers": [struct.unpack("<f", machine.mem_read(own_stats + offset, 4))[0]
                                       for offset in (0x530, 0x534)],
                "character_multipliers": [struct.unpack("<f", machine.mem_read(data + offset, 4))[0]
                                          for offset in (0x4B0, 0x540, 0x544, 0x548)],
                "buff_flags": machine.mem_read(data + 0x4AD, 1)[0],
            })
        if address in (0x008245E9, 0x0081F74F, 0x00824682, 0x0047ED40, 0x00481768):
            esp = machine.reg_read(UC_X86_REG_ESP)
            exception_events.append({
                "pc": hex(address), "eax": hex(machine.reg_read(UC_X86_REG_EAX)),
                "ecx": hex(machine.reg_read(UC_X86_REG_ECX)),
                "edx": hex(machine.reg_read(UC_X86_REG_EDX)),
                "ebx": hex(machine.reg_read(UC_X86_REG_EBX)),
                "ebp": hex(machine.reg_read(UC_X86_REG_EBP)),
                "esi": hex(machine.reg_read(UC_X86_REG_ESI)),
                "edi": hex(machine.reg_read(UC_X86_REG_EDI)),
                "stack": [hex(u32(machine, esp + offset)) for offset in range(0, 0x28, 4)],
                "preceding_trace": [hex(pc) for pc in probe._code_trace[-80:] ]})
        if address == 0x00481390:
            obj = machine.reg_read(UC_X86_REG_ECX)
            cleanup_dispatches.append({"pc": hex(address), "object": hex(obj),
                                       "vtable": hex(u32(machine, obj)),
                                       "embedded_vtable": hex(u32(machine, obj + 4))})
        if address == 0x004813E5:
            obj = machine.reg_read(UC_X86_REG_EBX)
            sprite = u32(machine, obj + 4)
            cleanup_dispatches.append({"pc": hex(address), "object": hex(obj),
                                       "embedded_vtable": hex(sprite),
                                       "virtual_target": hex(u32(machine, sprite + 0x14)),
                                       "stack_return": hex(u32(machine, machine.reg_read(UC_X86_REG_ESP)))})
        if address == 0x0047AB11:
            frame = machine.reg_read(UC_X86_REG_EBP)
            reaction_selection.append({"pc": hex(address), "attacker_frame": hex(frame),
                                       "frame_byte_48": str(machine.mem_read(frame + 0x48, 1)[0]),
                                       "frame_byte_44": str(machine.mem_read(frame + 0x44, 1)[0])})
        if address == 0x0047B181:
            esp = machine.reg_read(UC_X86_REG_ESP)
            defender_obj = machine.reg_read(UC_X86_REG_ESI)
            reaction_selection.append({"pc": hex(address), "reaction_action": str(u32(machine, esp + 0x24)),
                                       "defender_current_action": str(struct.unpack("<H", machine.mem_read(defender_obj + 0x13C, 2))[0]),
                                       "attacker_current_action": str(struct.unpack("<H", machine.mem_read(machine.reg_read(UC_X86_REG_EDI) + 0x13C, 2))[0]),
                                       "defender_vtable": hex(u32(machine, defender_obj)),
                                       "set_action_target": hex(u32(machine, u32(machine, defender_obj) + 8)),
                                       "initialize_action_target": hex(u32(machine, u32(machine, defender_obj) + 0x3C))})
        if address not in (0x0047B11C, 0x0047B123):
            return
        target_player = machine.reg_read(UC_X86_REG_ESI)
        damage_checkpoints.append({"pc": hex(address),
                                   "target_player": hex(target_player),
                                   "damage": str(machine.reg_read(UC_X86_REG_EBX) & 0xFFFF),
                                   "hp": str(struct.unpack("<H", machine.mem_read(target_player + 0x184, 2))[0])})

    uc.hook_add(UC_HOOK_CODE, pat_lookup)
    uc.hook_add(UC_HOOK_CODE, effect_create)
    uc.hook_add(UC_HOOK_CODE, reaction_virtual)

    constructor_trace: list[list[str]] = []
    for obj in (attacker, defender):
        uc.mem_write(obj, bytes(0x1400))
        sp = STACK + (0x6000 if obj == attacker else 0x6800) - 4
        uc.mem_write(sp, struct.pack("<I", STOP))
        probe.heap_cursor = HEAP
        uc.reg_write(UC_X86_REG_ESP, sp)
        uc.reg_write(UC_X86_REG_ECX, obj)
        uc.reg_write(UC_X86_REG_EIP, 0x0046B7F0)
        probe._code_trace.clear()
        probe._trace_active = True
        uc.emu_start(0x0046B7F0, STOP, count=200000)
        probe._trace_active = False
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"Player constructor stopped at {uc.reg_read(UC_X86_REG_EIP):#x}")
        constructor_trace.append([hex(pc) for pc in probe._code_trace[-12:]])
        # The base Player constructor leaves the polymorphic type at Player.
        # The test pair represents two Remilia instances, so install the exact
        # Remilia vtable before exercising cross-player reaction dispatch.
        uc.mem_write(obj, struct.pack("<I", PLAYER_VTABLES[character]))
        # AnimationObject embeds SpriteEx immediately after its primary vptr.
        # The base Player constructor does not construct this graphics object,
        # but the original hit-response cleanup calls its virtual destructor.
        uc.mem_write(obj + 4, struct.pack("<I", 0x0085772C))

    attacker_setter = initialize_original_action(
        probe, attacker, action_id, attack_frames, 0, pat_base=attacker_map)
    # initialize_original_action installs the selected PAT sequence's frame
    # vector as a compact fixture at local index zero. Preserve its authored
    # sequence number on Player so action-specific combat gates see the same
    # state as the original full PAT map.
    if attack_sequence:
        uc.mem_write(attacker + 0x13E, struct.pack("<H", attack_sequence))
    defender_setter = initialize_original_action(
        probe, defender, target_action_id, target_frames, 0, pat_base=defender_map)
    reaction_action_id = 50
    reaction_lookup_action_id = 50 if character in ("remilia", "udonge") else 74
    reaction_sequences = action_sequence_metadata(pat, reaction_action_id, effective=True)
    if len(reaction_sequences) != 1 or reaction_sequences[0]["sequence"] != 0:
        raise ValueError(f"expected one contiguous {character} reaction sequence")
    reaction_pat_base = PAT_MAP + 0x70000
    reaction_fixture_obj = LIST + 0xC000
    uc.mem_write(reaction_fixture_obj, bytes(0x1400))
    reaction_setter = initialize_original_action(
        probe, reaction_fixture_obj, reaction_action_id, reaction_sequences[0]["frames"], 0,
        pat_base=reaction_pat_base)
    defender_map_root = defender_map + 0x7000
    reaction_map_root = reaction_pat_base + 0x7000
    probe._pat_lookup_action_results[(defender_map_root, reaction_lookup_action_id)] = (
        probe._pat_lookup_results[reaction_map_root])

    # Give the two player objects separate owner/data blocks, as the original
    # factory copies Player+0x16c from its owner argument.
    data_blocks = (OWNER + 0x4000, OWNER + 0x5000)
    for index, (obj, data, team, own_stats, enemy_stats) in enumerate((
            (attacker, data_blocks[0], 0, data_blocks[0], data_blocks[1]),
            (defender, data_blocks[1], 1, data_blocks[1], data_blocks[0]))):
        uc.mem_write(data, bytes(0x800))
        uc.mem_write(obj + 0x16C, struct.pack("<I", data))
        uc.mem_write(obj + 0x168, struct.pack("<I", own_stats))
        uc.mem_write(obj + 0x170, struct.pack("<I", enemy_stats))
        uc.mem_write(obj + 0x350, struct.pack("<b", team))
        if facings[index] not in (-1, 1):
            raise ValueError("player facings must be -1 or 1")
        uc.mem_write(obj + 0x104, struct.pack("<b", facings[index]))
        uc.mem_write(obj + 0xEC, struct.pack("<f", positions[index][0]))
        uc.mem_write(obj + 0xF0, struct.pack("<f", positions[index][1]))
        uc.mem_write(obj + 0x184, struct.pack("<H", 1000))
        # The base Player constructor leaves this neutral combat multiplier
        # unset; the fight setup normally initializes it to 1.0 before a hit.
        uc.mem_write(obj + 0x198, struct.pack("<f", 1.0))
        uc.mem_write(obj + 0x538, struct.pack("<f", 1.0))
        uc.mem_write(data + 0x4B0, struct.pack("<f", 1.0))
        uc.mem_write(data + 0x530, struct.pack("<f", 1.0))
        uc.mem_write(data + 0x534, struct.pack("<f", 1.0))
        uc.mem_write(data + 0x544, struct.pack("<f", 1.0))
        uc.mem_write(data + 0x548, struct.pack("<f", 1.0))
        uc.mem_write(data + 0x1B4, struct.pack("<h", 0))
        uc.mem_write(data + 0x53C, struct.pack("<f", 1.0))
        uc.mem_write(data + 0x54C, struct.pack("<f", 1.0))
        uc.mem_write(data + 0x550, struct.pack("<f", 1.0))
        uc.mem_write(data + 0x554, struct.pack("<f", 0.0))
        uc.mem_write(data + 0x7C + team * 4, struct.pack("<I", 1000))

    # Select the requested authored attack frame using the game's original pose selector.
    uc.mem_write(attacker + 0x140, struct.pack("<H", attack_frame))
    for obj in (attacker, defender):
        sp = STACK + (0x7000 if obj == attacker else 0x7800) - 4
        requested_pose = attack_frame if obj == attacker else 0
        uc.mem_write(sp, struct.pack("<II", STOP, requested_pose))
        uc.mem_write(obj + 0x1C0, struct.pack("<I", 0))
        uc.reg_write(UC_X86_REG_ESP, sp)
        uc.reg_write(UC_X86_REG_ECX, obj)
        uc.reg_write(UC_X86_REG_EIP, 0x00464B50)
        uc.emu_start(0x00464B50, STOP, count=100000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"pose selection stopped at {uc.reg_read(UC_X86_REG_EIP):#x}")
        sp = STACK + (0x7400 if obj == attacker else 0x7C00) - 4
        uc.mem_write(sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESP, sp)
        uc.reg_write(UC_X86_REG_ECX, obj)
        uc.reg_write(UC_X86_REG_EIP, 0x00465E10)
        uc.emu_start(0x00465E10, STOP, count=100000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"PAT box synchronization stopped at {uc.reg_read(UC_X86_REG_EIP):#x}")

    geometry = run_original_hit_hurt_pair(probe, attacker, defender)
    if geometry["return_value"] != 1 and positions[0] == positions[1]:
        raise AssertionError(
            f"selected PAT frames do not overlap: {geometry}; "
            f"attacker descriptor={u32(uc, attacker + 0x158):#x}, "
            f"defender descriptor={u32(uc, defender + 0x158):#x}, "
            f"attacker flags={uc.mem_read(attacker + 0x1CB, 1)[0]}, "
            f"target hurt={uc.mem_read(defender + 0x1CC, 1)[0]}")

    scale_sp = STACK + 0x9800 - 4
    uc.mem_write(scale_sp, struct.pack("<I", STOP))
    uc.reg_write(UC_X86_REG_ESP, scale_sp)
    uc.reg_write(UC_X86_REG_ECX, attacker)
    uc.reg_write(UC_X86_REG_EIP, 0x00464A80)
    uc.emu_start(0x00464A80, STOP, count=100000)
    if uc.reg_read(UC_X86_REG_EIP) != STOP:
        raise RuntimeError(f"direct damage helper stopped at {uc.reg_read(UC_X86_REG_EIP):#x}")
    direct_damage_helper = uc.reg_read(UC_X86_REG_EAX) & 0xFFFF

    watched_ranges = [(base, base + 0x600) for base in data_blocks]
    writes: list[dict[str, object]] = []
    def watch_write(machine, _access, address, size, value, _user) -> None:
        if any(address < end and address + size > start for start, end in watched_ranges):
            writes.append({"address": hex(address), "size": size, "value": int(value)})
    write_hook = uc.hook_add(UC_HOOK_MEM_WRITE, watch_write)

    sp = STACK + 0x9000 - 12
    uc.mem_write(sp, struct.pack("<3I", STOP, attacker, defender))
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_ECX, attacker)
    uc.reg_write(UC_X86_REG_EIP, 0x0047C770)
    probe._code_trace.clear()
    probe._trace_limit = 12000
    probe._trace_active = True
    error = None
    try:
        uc.emu_start(0x0047C770, STOP, count=300000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            error = f"resolver returned at {uc.reg_read(UC_X86_REG_EIP):#x}"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}"
    finally:
        probe._trace_active = False
        uc.hook_del(write_hook)

    trait = attack_frames[attack_frame]["combat_traits"]
    authored_attack_damage = int(attack_frames[attack_frame]["damage"])
    attack_frame_pointer = u32(uc, attacker + 0x158)
    attack_frame_runtime_damage = struct.unpack(
        "<H", uc.mem_read(attack_frame_pointer + 0x1C, 2))[0]
    attack_combat_pointer = u32(uc, attacker + 0x1C0)
    attack_combat_runtime_damage = (struct.unpack(
        "<H", uc.mem_read(attack_combat_pointer + 0x1C, 2))[0]
        if attack_combat_pointer else None)
    return {
        "exe_sha256": probe.sha256,
        "fixture": {"character": character, "attacker": hex(attacker), "defender": hex(defender),
                    "attacker_action": action_id, "attacker_sequence": attack_sequence,
                    "attacker_frame": attack_frame,
                    "defender_action": target_action_id, "defender_frame": 0,
                    "attacker_trait_0x26": trait[10],
                    "attacker_damage": authored_attack_damage,
                    "attacker_frame_runtime_damage": attack_frame_runtime_damage,
                    "attacker_frame_pointer": hex(attack_frame_pointer),
                    "attacker_combat_pointer": hex(attack_combat_pointer),
                    "attacker_combat_runtime_damage": attack_combat_runtime_damage,
                    "positions": [list(position) for position in positions],
                    "facings": list(facings)},
        "constructors": constructor_trace,
        "action_setters": [attacker_setter, defender_setter],
        "box_transforms": [
            {**entry,
             "input_box": list(struct.unpack("<4i", uc.mem_read(int(entry["source"], 16), 16))),
             "output_box": list(struct.unpack("<4i", uc.mem_read(int(entry["destination"], 16), 16)))}
            for entry in box_transform_entries],
        "reaction_fixture": {"action": reaction_action_id,
                              "lookup_action_id": reaction_lookup_action_id,
                              "sequence_count": len(reaction_sequences),
                              "frame_count": len(reaction_sequences[0]["frames"]),
                              "map_root": hex(reaction_map_root),
                              "setter": reaction_setter},
        "geometry": geometry,
        "direct_damage_helper": direct_damage_helper,
        "effect_manager": {"global": "0x8985f0", "type": "EffectManager_Effect",
                           "create_effect_slot": "vtable+0x0c",
                           "controlled_stub": hex(effect_create_stub),
                           "synthetic_effect_object": hex(synthetic_effect),
                           "requests": effect_requests},
        "reaction_selection": reaction_selection,
        "damage_scale_events": damage_scale_events,
        "damage_branch_events": damage_branch_events,
        "pat_lookup_events": pat_lookup_events,
        "cleanup_dispatches": cleanup_dispatches,
        "exception_events": exception_events,
        "resolver": {"entry": "0x47c770", "error": error,
                     "trace": [hex(pc) for pc in probe._code_trace[-12000:]],
                     "exception_events": exception_events,
                     "damage_checkpoints": damage_checkpoints,
                     "invalid_memory": list(probe._invalid_memory),
                     "collision_type_attacker": u32(uc, attacker + 0x190),
                     "collision_type_defender": u32(uc, defender + 0x190),
                     "hp_attacker_184": struct.unpack("<H", uc.mem_read(attacker + 0x184, 2))[0],
                     "hp_defender_184": struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0],
                     "action_attacker_13c": struct.unpack("<H", uc.mem_read(attacker + 0x13C, 2))[0],
                     "action_defender_13c": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
                     "sequence_defender_13e": struct.unpack("<H", uc.mem_read(defender + 0x13E, 2))[0],
                     "pose_defender_140": struct.unpack("<H", uc.mem_read(defender + 0x140, 2))[0],
                     "pose_count_defender_148": struct.unpack("<H", uc.mem_read(defender + 0x148, 2))[0],
                     "account_counters_before": [1000, 1000],
                     "account_counters_after": [
                         u32(uc, data_blocks[0] + 0x7C),
                         u32(uc, data_blocks[1] + 0x80)],
                     "writes_to_account_blocks": writes},
        "scope": f"Both original base Player constructors, action setters/initializers, pose selection, box synchronization, 0x4640b0/0x464200 box coordinate transforms, geometry and 0x47c770 execute for {character}. PAT lookup, team contexts, owner-data multipliers, positions/facing, account counters and EffectManager_Effect::CreateEffect are controlled; the effect stub records the request and returns a synthetic object without rendering. This fixture is not driven by gameplay input or a PC replay.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dat-dir", type=Path, default=ROOT / "original")
    parser.add_argument("--character", choices=tuple(PLAYER_VTABLES), default="remilia")
    parser.add_argument("--action", type=int)
    parser.add_argument("--sequence", type=int, default=0)
    parser.add_argument("--frame", type=int)
    parser.add_argument("--attacker-x", type=float, default=320.0)
    parser.add_argument("--attacker-y", type=float, default=180.0)
    parser.add_argument("--defender-x", type=float, default=320.0)
    parser.add_argument("--defender-y", type=float, default=180.0)
    parser.add_argument("--attacker-facing", type=int, choices=(-1, 1), default=1)
    parser.add_argument("--defender-facing", type=int, choices=(-1, 1), default=-1)
    parser.add_argument("--sweep-defender-x", nargs=3, type=float, metavar=("START", "STOP", "STEP"),
                        help="run inclusive x positions with fixed attacker position; emits geometry only")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    positions = ((args.attacker_x, args.attacker_y), (args.defender_x, args.defender_y))
    facings = (args.attacker_facing, args.defender_facing)
    if args.sweep_defender_x:
        start, stop, step = args.sweep_defender_x
        if step <= 0 or stop < start:
            parser.error("sweep requires STOP >= START and STEP > 0")
        count = int((stop - start) // step) + 1
        rows = []
        for index in range(count):
            defender_x = start + index * step
            report = run(args.dat_dir, args.character, args.action, args.sequence,
                         args.frame, (positions[0], (defender_x, args.defender_y)), facings)
            rows.append({"defender_x": defender_x,
                         "geometry_return": report["geometry"]["return_value"],
                         "transforms": report["box_transforms"],
                         "damage": report["resolver"]["damage_checkpoints"]})
        result = {"character": args.character, "action": args.action,
                  "sequence": args.sequence, "frame": args.frame,
                  "attacker_position": list(positions[0]), "attacker_facing": facings[0],
                  "defender_facing": facings[1], "defender_y": args.defender_y,
                  "sweep": {"start": start, "stop": stop, "step": step}, "rows": rows,
                  "scope": "Each row independently initializes original PE constructors, PAT actions, original box synchronization/transforms, geometry and damage resolver. Position/facing, scenario/camera globals, effects and player stats remain controlled; this is a static pose probe, not gameplay or a PC replay."}
    else:
        result = run(args.dat_dir, args.character, args.action, args.sequence,
                     args.frame, positions, facings)
    encoded = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
