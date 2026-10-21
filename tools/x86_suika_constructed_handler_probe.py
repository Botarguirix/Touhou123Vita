#!/usr/bin/env python3
"""Run Suika's original constructor, action setter, then handleInputs PE."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))
sys.path.insert(0, str(ROOT))

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EIP,
                               UC_X86_REG_EDI, UC_X86_REG_ESI, UC_X86_REG_ESP)
from tools.x86_suwako_808_factory_probe import (
    ACTION_NODE, HEAP, LIST, NIL, OWNER, PAT_MAP, STACK, STOP, Suwako808FactoryProbe,
)
from tools.x86_remilia_412_spawn_probe import (
    initialize_original_action, run_original_hit_hurt_pair,
)
from tools.extract_pat_pose_metadata import action_sequence_metadata, read_pat

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
PLAYER = LIST + 0x8000
PLAYER_INFO = OWNER + 0x8000
KEY_MANAGER = OWNER + 0x9000
DEFENDER_INFO = OWNER + 0xA000
DEFENDER_KEY_MANAGER = OWNER + 0xB000
PLAYER_CTOR = 0x00609D40
ACTION_SETTER = 0x00464930
HANDLE_INPUTS = 0x00609DC0
TARGET_BRANCH = 0x0060BE83
CLEANUP = 0x0046CAC0
INPUT_SEED = 0x0046D950
INPUT_UPDATE = 0x0046D5D0
MOTION_MATCHER = 0x00487020


def _execute(uc, entry: int, stop: int, ecx: int, esp: int,
             args: tuple[int, ...] = (), count: int = 300000) -> str | None:
    uc.mem_write(esp, struct.pack("<I", stop) +
                 (struct.pack("<" + "I" * len(args), *args) if args else b""))
    uc.reg_write(UC_X86_REG_ECX, ecx)
    uc.reg_write(UC_X86_REG_ESP, esp)
    uc.reg_write(UC_X86_REG_EIP, entry)
    try:
        uc.emu_start(entry, stop, count=count)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}"
    return None


def run() -> dict[str, object]:
    exe = ROOT / "original/th123.exe"
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    if digest != REFERENCE_SHA256:
        raise ValueError(f"reference PE SHA-256 mismatch: {digest}")
    probe = Suwako808FactoryProbe(exe, character="suika", action_id=801,
                                  intercept_box_transforms=True)
    probe.action_id = 200
    probe._prepare_pat_actions((50, 96, 97, 200, 400, 418))
    uc = probe.uc
    observations: dict[str, object] = {
        "handler_branch_reached": False,
        "cleanup_entry_reached": False,
        "setter_requests": [],
        "handler_trace": [],
        "matcher_calls": 0,
        "collect_handler_setters": True,
    }

    # Match the native startup ordering needed by PlayerSuika's PE constructor.
    crt_error = _execute(uc, 0x00824BFA, STOP, 0, STACK + 0x5000 - 4, count=100000)
    list_error = _execute(uc, 0x0046B750, STOP, 0x0089AAE8,
                          STACK + 0x5800 - 4, count=100000)
    global_list = struct.unpack("<I", uc.mem_read(0x0089AAEC, 4))[0]
    if global_list:
        uc.mem_write(global_list + 0x15, b"\x01")
    uc.mem_write(PLAYER, bytes(0x1000))
    uc.mem_write(PLAYER_INFO, struct.pack(
        "<I4B6I", 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, KEY_MANAGER))
    uc.mem_write(KEY_MANAGER, bytes(0x100))
    ctor_error = _execute(uc, PLAYER_CTOR, STOP, PLAYER,
                          STACK + 0xF000 - 8, (PLAYER_INFO,), count=300000)
    object_manager = struct.unpack("<I", uc.mem_read(PLAYER + 0x6F8, 4))[0]
    ctor_state = {
        "error": ctor_error,
        "returned_to_stop": uc.reg_read(UC_X86_REG_EIP) == STOP,
        "player_vtable": hex(struct.unpack("<I", uc.mem_read(PLAYER, 4))[0]),
        "member_158_pointer": hex(struct.unpack("<I", uc.mem_read(PLAYER + 0x158, 4))[0]),
        "member_15c_pointer": hex(struct.unpack("<I", uc.mem_read(PLAYER + 0x15C, 4))[0]),
        "key_manager_pointer": hex(struct.unpack("<I", uc.mem_read(PLAYER + 0x750, 4))[0]),
        "object_manager": hex(object_manager),
    }
    if crt_error or list_error or ctor_error or not object_manager:
        raise RuntimeError(json.dumps({"crt_error": crt_error, "list_error": list_error,
                                       "constructor": ctor_state,
                                       "host_termination": probe.host_termination}, indent=2))

    uc.mem_write(PLAYER + 0x160, struct.pack("<I", PAT_MAP))
    # Enter dash action 200 through the original setAction method and real PAT.
    setter_error = _execute(uc, ACTION_SETTER, STOP, PLAYER,
                            STACK + 0xEFF0, (200,), count=200000)
    action_before_handler = struct.unpack("<H", uc.mem_read(PLAYER + 0x13C, 2))[0]
    if setter_error or action_before_handler != 200:
        raise RuntimeError(json.dumps({"setter_error": setter_error,
                                       "action_after_original_setter": action_before_handler,
                                       "constructor": ctor_state,
                                       "trace": [hex(pc) for pc in probe._code_trace[-80:]],
                                       "invalid_memory": probe._invalid_memory[-8:]}, indent=2))

    # The Player and KeyManager now come from the original constructor. Seed
    # its own deque with the PE seeder, then let updates append/match in place.
    uc.mem_write(PLAYER + 0x104, struct.pack("<b", 1))
    uc.mem_write(PLAYER + 0x754, bytes(0x20))
    seed_error = _execute(uc, INPUT_SEED, STOP, PLAYER,
                          STACK + 0xD000, count=200000)
    ring_address = PLAYER + 0x7B0
    ring_before = list(struct.unpack("<5I", uc.mem_read(ring_address, 20)))
    input_trace: list[dict[str, object]] = []
    # Suika's 418 branch also checks the current C key through Player+0x784.
    # Keep C held while entering the NRNR motion so the real update derives
    # that gate field instead of injecting it after input processing.
    states = ((0, 0, "neutral+C"), (1, 1, "right+C"),
              (0, 1, "neutral+C"), (1, 1, "right+C"))

    def input_services(machine, address: int, _size: int, _user: object) -> None:
        if address == 0x0046C8E0:
            # Physical KeyManager refresh is the only input boundary replaced;
            # Player fields are authored by this deterministic test sequence.
            esp = machine.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == MOTION_MATCHER:
            observations["matcher_calls"] += 1

    uc.hook_add(UC_HOOK_CODE, input_services)
    if seed_error:
        raise RuntimeError(f"original input ring seeding failed: {seed_error}")
    for horizontal, button_c, label in states:
        uc.mem_write(PLAYER + 0x754, struct.pack(
            "<8i", horizontal, 0, 0, 0, button_c, 0, 0, 0))
        input_error = _execute(uc, INPUT_UPDATE, STOP, PLAYER,
                               STACK + 0xC000, count=150000)
        if input_error:
            raise RuntimeError(f"original input update failed: {input_error}; invalid={probe._invalid_memory[-4:]}")
        ring = struct.unpack("<5I", uc.mem_read(ring_address, 20))
        block_count, offset, size = ring[2], ring[3], ring[4]
        logical = (offset + size - 1) if size else offset
        block_index = (logical // 8) % max(block_count, 1)
        block_ptr = struct.unpack("<I", uc.mem_read(ring[1] + block_index * 4, 4))[0]
        sample = struct.unpack("<H", uc.mem_read(block_ptr + (logical % 8) * 2, 2))[0] if block_ptr else None
        input_trace.append({"input": label, "sample": sample, "ring_size": size,
                            "ring_offset": offset,
                            "motion_bits": struct.unpack("<I", uc.mem_read(PLAYER + 0x7C4, 4))[0],
                            "buffered_c": struct.unpack("<I", uc.mem_read(PLAYER + 0x784, 4))[0]})
    uc.mem_write(PLAYER + 0x49E, struct.pack("<H", 1000))

    def observe(machine, address: int, _size: int, _user: object) -> None:
        if 0x00609DC0 <= address < 0x0060C200:
            observations["handler_trace"].append(hex(address))
        if address == 0x0048A220:
            # This state/cancel query depends on the native fight manager;
            # hold it false while preserving the real Player/PAT/handler.
            esp = machine.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, 0)
            machine.reg_write(UC_X86_REG_ESP, esp + 12)
            machine.reg_write(UC_X86_REG_EIP, ret)
            return
        if address == TARGET_BRANCH:
            observations["handler_branch_reached"] = True
        elif address == ACTION_SETTER:
            if observations["collect_handler_setters"]:
                esp = machine.reg_read(UC_X86_REG_ESP)
                observations["setter_requests"].append(
                    struct.unpack("<H", machine.mem_read(esp + 4, 2))[0])
        elif address == CLEANUP:
            observations["cleanup_entry_reached"] = True
            machine.emu_stop()

    uc.hook_add(UC_HOOK_CODE, observe)
    probe._code_trace.clear()
    probe._trace_active = True
    handler_error = _execute(uc, HANDLE_INPUTS, STOP, PLAYER,
                             STACK + 0xE000, (0, 0, 0, 0, 0, 0, 0), count=400000)
    probe._trace_active = False
    observations["collect_handler_setters"] = False
    action_after = struct.unpack("<H", uc.mem_read(PLAYER + 0x13C, 2))[0]
    # Complete the original buffered-input cleanup, then dispatch the
    # character's virtual update on this same Player to observe PAT progress.
    cleanup_error = _execute(uc, CLEANUP, STOP, PLAYER,
                             STACK + 0xE100, count=100000)
    update_entry = struct.unpack("<I", uc.mem_read(0x0085DA84 + 10 * 4, 4))[0]
    pat_ticks: list[dict[str, object]] = []
    pat_update_error = None
    for tick in range(1, 17):
        pat_update_error = _execute(uc, update_entry, STOP, PLAYER,
                                    STACK + 0xE200, count=250000)
        frame_pointer = struct.unpack("<I", uc.mem_read(PLAYER + 0x158, 4))[0]
        action = struct.unpack("<H", uc.mem_read(PLAYER + 0x13C, 2))[0]
        sequence = struct.unpack("<H", uc.mem_read(PLAYER + 0x13E, 2))[0]
        pose = struct.unpack("<H", uc.mem_read(PLAYER + 0x140, 2))[0]
        pat_ranges = getattr(probe, "_active_pat_ranges", [(PAT_MAP, PAT_MAP + 0x80000)])
        frame_valid = any(start <= frame_pointer < end for start, end in pat_ranges)
        frame_damage = struct.unpack("<H", uc.mem_read(frame_pointer + 0x1C, 2))[0] if frame_valid else None
        boxes_start, boxes_end = ((struct.unpack("<II", uc.mem_read(frame_pointer + 0x6C, 8))
                                   if frame_valid else (0, 0)))
        pat_ticks.append({"tick": tick, "action": action, "sequence": sequence,
                          "pose": pose, "frame_pointer": hex(frame_pointer),
                          "frame_damage": frame_damage,
                          "frame_attack_boxes": (boxes_end - boxes_start) // 16 if frame_valid else None,
                          "update_error": pat_update_error})
        if pat_update_error or action != 418:
            break
    geometry_result: dict[str, object] | None = None
    damage_result: dict[str, object] | None = None
    attacker_box_sync_error = None
    defender_box_sync_error = None
    defender_setter = None
    defender_ctor_error = None
    if len(pat_ticks) == 16 and pat_ticks[-1]["frame_damage"] == 900:
        # Feed the transitioned PAT geometry into the original PE overlap
        # helper. Box placement uses the verified 0x4640b0/0x464200 affine
        # transform; the overlap test itself is the original 0x47a5b0.
        defender = LIST + 0xA000
        uc.mem_write(defender, bytes(0x1400))
        uc.mem_write(defender, bytes(0x1000))
        uc.mem_write(DEFENDER_INFO, struct.pack(
            "<I4B6I", 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, DEFENDER_KEY_MANAGER))
        uc.mem_write(DEFENDER_KEY_MANAGER, bytes(0x100))
        defender_ctor_error = _execute(uc, PLAYER_CTOR, STOP, defender,
                                       STACK + 0xEE00 - 8, (DEFENDER_INFO,), count=300000)
        pat_record = read_pat(ROOT / "original/th123c.dat", "data/character/suika/suika.pat")
        if pat_record is None:
            raise FileNotFoundError("Suika PAT is missing from original/th123c.dat")
        reaction_rows = action_sequence_metadata(pat_record[0], 50, effective=True)
        reaction = next(row for row in reaction_rows if int(row["sequence"]) == 0)
        probe._pat_lookup_results = {}
        probe._pat_lookup_action_results = {}
        def resolve_pat_lookup(machine, address: int, _size: int, _user: object) -> None:
            if address != 0x0043F2F0:
                return
            esp = machine.reg_read(UC_X86_REG_ESP)
            map_key = machine.reg_read(UC_X86_REG_ECX)
            action_key_ptr = struct.unpack("<I", machine.mem_read(esp + 8, 4))[0]
            action_key = struct.unpack("<I", machine.mem_read(action_key_ptr, 4))[0]
            result = probe._pat_lookup_action_results.get(
                (map_key, action_key), probe._pat_lookup_results.get(map_key))
            if result is None:
                return
            output_pair = struct.unpack("<I", machine.mem_read(esp + 4, 4))[0]
            machine.mem_write(output_pair, bytes(machine.mem_read(result, 8)))
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, output_pair)
            machine.reg_write(UC_X86_REG_ESP, esp + 12)
            machine.reg_write(UC_X86_REG_EIP, ret)
        uc.hook_add(UC_HOOK_CODE, resolve_pat_lookup)
        reaction_fixture = LIST + 0xC000
        uc.mem_write(reaction_fixture, bytes(0x1400))
        reaction_map_base = PAT_MAP + 0x40000
        reaction_setter = initialize_original_action(
            probe, reaction_fixture, 50, reaction["frames"], 0,
            pat_base=reaction_map_base)
        reaction_map_root = reaction_map_base + 0x7000
        reaction_map_result = probe._pat_lookup_results[reaction_map_root]
        # Re-key the controlled, authentic Suika action-50 sequence as 74 in
        # the native PAT RB-tree so the original selector sees a coherent key
        # and the sequence node/value remain the character's actual reaction.
        probe._pat_lookup_action_results[(PAT_MAP, 74)] = reaction_map_result
        uc.mem_write(defender + 0x160, struct.pack("<I", PAT_MAP))
        defender_setter_error = _execute(uc, ACTION_SETTER, STOP, defender,
                                         STACK + 0xED00, (400,), count=200000)
        defender_action_before_hit = struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0]
        attack_sequences = action_sequence_metadata(pat_record[0], 418, effective=True)
        attack_sequence = next(row for row in attack_sequences if int(row["sequence"]) == 2)
        attack_frame = attack_sequence["frames"][0]
        neutral_sequences = action_sequence_metadata(pat_record[0], 400, effective=True)
        neutral = next(row for row in neutral_sequences if int(row["sequence"]) == 0)
        neutral_frame = neutral["frames"][0]
        uc.mem_write(PLAYER + 0xEC, struct.pack("<f", 320.0))
        uc.mem_write(PLAYER + 0xF0, struct.pack("<f", 180.0))
        attacker_box_sync_error = _execute(
            uc, 0x00465E10, STOP, PLAYER, STACK + 0xE400, count=150000)
        for obj, authored, facing, position_x, position_y, attack in (
                (PLAYER, attack_frame, 1, 320.0, 180.0, True),
                (defender, neutral_frame, -1, 320.0, 180.0, False)):
            uc.mem_write(obj + 0xEC, struct.pack("<f", position_x))
            uc.mem_write(obj + 0xF0, struct.pack("<f", position_y))
            uc.mem_write(obj + 0x104, struct.pack("<b", facing))
            if not attack:
                defender_box_sync_error = _execute(
                    uc, 0x00465E10, STOP, defender, STACK + 0xE500, count=150000)
            boxes = authored["attack_boxes"] if attack else authored["hurt_boxes"]
            count_offset, boxes_offset = ((0x1CB, 0x220) if attack else (0x1CC, 0x1D0))
            uc.mem_write(obj + count_offset, struct.pack("<B", len(boxes)))
            world = []
            for left, top, right, bottom in boxes:
                x0, x1 = sorted((int(position_x + facing * left),
                                 int(position_x + facing * right)))
                y0, y1 = sorted((top - int(position_y), bottom - int(position_y)))
                world.append((x0, y0, x1, y1))
            if world:
                uc.mem_write(obj + boxes_offset,
                             b"".join(struct.pack("<4i", *box) for box in world))
        geometry_result = run_original_hit_hurt_pair(probe, PLAYER, defender)
        # Recreate the fight-owned combat/stat blocks used by the original
        # resolver, then invoke the real PE damage helper and pair resolver.
        data_blocks = (OWNER + 0x4000, OWNER + 0x5000)
        for index, (obj, data, own_stats, enemy_stats) in enumerate((
                (PLAYER, data_blocks[0], data_blocks[0], data_blocks[1]),
                (defender, data_blocks[1], data_blocks[1], data_blocks[0]))):
            uc.mem_write(data, bytes(0x800))
            for offset, value in ((0x16C, data), (0x168, own_stats), (0x170, enemy_stats)):
                uc.mem_write(obj + offset, struct.pack("<I", value))
            uc.mem_write(obj + 0x350, struct.pack("<b", index))
            # Keep this response probe non-lethal so the PE takes the ordinary
            # reaction-selection path instead of the round/KO branch.
            uc.mem_write(obj + 0x184, struct.pack("<H", 2000))
            for offset in (0x198, 0x538):
                uc.mem_write(obj + offset, struct.pack("<f", 1.0))
            for offset in (0x4B0, 0x530, 0x534, 0x53C, 0x544, 0x548, 0x54C, 0x550):
                uc.mem_write(data + offset, struct.pack("<f", 1.0))
            uc.mem_write(data + 0x554, struct.pack("<f", 0.0))
            uc.mem_write(data + 0x7C + index * 4, struct.pack("<I", 2000))
        direct_damage_error = _execute(uc, 0x00464A80, STOP, PLAYER,
                                       STACK + 0xE700, count=100000)
        direct_damage_value = uc.reg_read(UC_X86_REG_EAX) & 0xFFFF
        effect_manager, effect_vtable = OWNER + 0xC000, OWNER + 0xD000
        effect_object, effect_stub = OWNER + 0xE000, 0x0047D000
        uc.mem_write(effect_manager, struct.pack("<I", effect_vtable))
        uc.mem_write(effect_vtable + 0x0C, struct.pack("<I", effect_stub))
        uc.mem_write(effect_object, bytes(0x400))
        uc.mem_write(effect_object, struct.pack("<I", 0x00858AB4))
        uc.mem_write(0x008985F0, struct.pack("<I", effect_manager))
        effect_requests: list[list[str]] = []
        damage_checkpoints: list[dict[str, int]] = []
        reaction_dispatches: list[dict[str, object]] = []
        reaction_inputs: list[dict[str, object]] = []
        action_setter_requests: list[dict[str, object]] = []
        sequence_setter_requests: list[dict[str, object]] = []
        current_hit_tick = [0]
        field_884_writes: list[dict[str, object]] = []
        def capture_field_884_write(machine, _access, address: int, size: int,
                                    value: int, _user: object) -> None:
            if address < defender + 0x886 and address + size > defender + 0x884:
                field_884_writes.append({
                    "tick": current_hit_tick[0],
                    "pc": hex(machine.reg_read(UC_X86_REG_EIP)),
                    "action": struct.unpack("<H", machine.mem_read(defender + 0x13C, 2))[0],
                    "address": hex(address),
                    "size": size,
                    "old": struct.unpack("<H", machine.mem_read(defender + 0x884, 2))[0],
                    "value": int(value),
                })
        uc.hook_add(UC_HOOK_MEM_WRITE, capture_field_884_write)
        def resolver_services(machine, address: int, _size: int, _user: object) -> None:
            if address == effect_stub:
                esp = machine.reg_read(UC_X86_REG_ESP)
                raw = struct.unpack("<7I", machine.mem_read(esp, 28))
                effect_requests.append([hex(value) for value in raw[1:]])
                machine.reg_write(UC_X86_REG_EAX, effect_object)
                machine.reg_write(UC_X86_REG_ESP, esp + 28)
                machine.reg_write(UC_X86_REG_EIP, raw[0])
            elif address in (0x0047B11C, 0x0047B123):
                target = machine.reg_read(UC_X86_REG_ESI)
                damage_checkpoints.append({"pc": hex(address),
                                           "damage": machine.reg_read(UC_X86_REG_EBX) & 0xFFFF,
                                           "hp": struct.unpack("<H", machine.mem_read(target + 0x184, 2))[0]})
            elif address == 0x0047B181:
                esp = machine.reg_read(UC_X86_REG_ESP)
                target = machine.reg_read(UC_X86_REG_ESI)
                attacker = machine.reg_read(UC_X86_REG_EDI)
                reaction_dispatches.append({
                    "reaction_action": struct.unpack("<I", machine.mem_read(esp + 0x24, 4))[0],
                    "target_action": struct.unpack("<H", machine.mem_read(target + 0x13C, 2))[0],
                    "target_vtable": hex(struct.unpack("<I", machine.mem_read(target, 4))[0]),
                    "attacker_action": struct.unpack("<H", machine.mem_read(attacker + 0x13C, 2))[0],
                })
            elif address == 0x0047AB11:
                frame = machine.reg_read(UC_X86_REG_EBP)
                reaction_inputs.append({
                    "attacker_frame": hex(frame),
                    "frame_bytes_44_48": list(machine.mem_read(frame + 0x44, 5)),
                    "frame_flags": struct.unpack("<I", machine.mem_read(frame + 0x4C, 4))[0],
                    "attack_flags": struct.unpack("<I", machine.mem_read(frame + 0x50, 4))[0],
                    "trait_26": machine.mem_read(frame + 0x26, 1)[0],
                    "enemy_stun": struct.unpack("<H", machine.mem_read(frame + 0x2C, 2))[0],
                })
            elif address == ACTION_SETTER:
                esp = machine.reg_read(UC_X86_REG_ESP)
                action_setter_requests.append({
                    "player": hex(machine.reg_read(UC_X86_REG_ECX)),
                    "action": struct.unpack("<H", machine.mem_read(esp + 4, 2))[0],
                    "callsite": hex(struct.unpack("<I", machine.mem_read(esp, 4))[0]),
                })
            elif address == 0x004652A0 and machine.reg_read(UC_X86_REG_ECX) == defender:
                esp = machine.reg_read(UC_X86_REG_ESP)
                sequence_setter_requests.append({
                    "tick": current_hit_tick[0],
                    "callsite": hex(struct.unpack("<I", machine.mem_read(esp, 4))[0]),
                    "action": struct.unpack("<H", machine.mem_read(defender + 0x13C, 2))[0],
                    "sequence_argument": struct.unpack("<H", machine.mem_read(esp + 4, 2))[0],
                    "sequence_before": struct.unpack("<H", machine.mem_read(defender + 0x13E, 2))[0],
                })
        uc.hook_add(UC_HOOK_CODE, resolver_services)
        resolver_sp = STACK + 0xF800 - 12
        probe._code_trace.clear()
        probe._trace_active = True
        resolver_error = _execute(uc, 0x0047C770, STOP, PLAYER, resolver_sp,
                                  (PLAYER, defender), count=400000)
        probe._trace_active = False
        damage_result = {
            "attacker_box_sync_error": attacker_box_sync_error,
            "defender_box_sync_error": defender_box_sync_error,
            "direct_damage_helper_error": direct_damage_error,
            "direct_damage_helper_value": direct_damage_value,
            "resolver_error": resolver_error,
            "damage_checkpoints": damage_checkpoints,
            "hp_attacker": struct.unpack("<H", uc.mem_read(PLAYER + 0x184, 2))[0],
            "hp_defender": struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0],
            "action_attacker": struct.unpack("<H", uc.mem_read(PLAYER + 0x13C, 2))[0],
            "action_defender": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
            "sequence_defender": struct.unpack("<H", uc.mem_read(defender + 0x13E, 2))[0],
            "defender_combat_state": {
                "collision_type_190": struct.unpack("<I", uc.mem_read(defender + 0x190, 4))[0],
                "reaction_timer_194": struct.unpack("<H", uc.mem_read(defender + 0x194, 2))[0],
                "hitstop_196": struct.unpack("<H", uc.mem_read(defender + 0x196, 2))[0],
                "subframe_142": struct.unpack("<H", uc.mem_read(defender + 0x142, 2))[0],
            },
            "effect_requests": effect_requests,
            "reaction_dispatches": reaction_dispatches,
            "reaction_inputs": reaction_inputs,
            "action_setter_requests": action_setter_requests,
            "sequence_setter_requests": sequence_setter_requests,
            "trace_tail": [hex(pc) for pc in probe._code_trace[-100:]],
        }
        defender_hitstun_ticks: list[dict[str, object]] = []
        defender_update_error = None
        defender_timer_error = None
        defender_input_error = None
        defender_update_failure_trace: list[str] = []
        defender_transition_trace: list[str] = []
        defender_transition_checkpoint: dict[str, object] | None = None
        action_route_observations: list[dict[str, object]] = []
        transition_snapshot_ranges = (
            (defender, 0x1400), (LIST, 0x10000),
            (OWNER, 0x10000), (HEAP, 0x100000),
        )
        post_hit_transition_snapshots = tuple(
            (address, bytes(uc.mem_read(address, size)))
            for address, size in transition_snapshot_ranges)
        defender_update_entry = struct.unpack("<I", uc.mem_read(0x0085DA84 + 10 * 4, 4))[0]
        defender_timer_entry = 0x0046A330
        action_route_addresses = {0x0046A330, 0x00483F40, 0x004849F6,
                                  0x00484A20, 0x00484A80, 0x00484AB0,
                                  0x00484AD1, 0x004847D4, 0x00484807,
                                  0x00484696, 0x00487EA0,
                                  0x005EE620, 0x006086A0, 0x00609145, 0x0048B210,
                                  0x0048B242, 0x0048B480, 0x0048B85F, 0x0048B8CF,
                                  0x0048B8E4,
                                  0x004846A1, 0x004846A5}
        def capture_action_route(machine, address: int, _size: int, _user: object) -> None:
            if current_hit_tick[0] != 10 or address not in action_route_addresses:
                return
            player = machine.reg_read(UC_X86_REG_ESI)
            action_route_observations.append({
                "tick": current_hit_tick[0],
                "pc": hex(address),
                "esi": hex(player),
                "eax": hex(machine.reg_read(UC_X86_REG_EAX)),
                "action": struct.unpack("<H", machine.mem_read(player + 0x13C, 2))[0]
                if player > 0x10000 else None,
            })
        uc.hook_add(UC_HOOK_CODE, capture_action_route)
        action97_sequence_by_pointer = {
            int(pointer): int(sequence)
            for sequence, pointer in probe._sequence_node_by_action[97].items()
        }
        action97_pat_graph = []
        for sequence, pointer in sorted(probe._sequence_node_by_action[97].items()):
            previous = struct.unpack("<I", uc.mem_read(int(pointer) + 0x18, 4))[0]
            following = struct.unpack("<I", uc.mem_read(int(pointer) + 0x1C, 4))[0]
            action97_pat_graph.append({
                "sequence": int(sequence),
                "node": hex(int(pointer)),
                "loop_mode": uc.mem_read(int(pointer) + 0x14, 1)[0],
                "previous_sequence": action97_sequence_by_pointer.get(previous),
                "previous_node": hex(previous) if previous else None,
                "next_sequence": action97_sequence_by_pointer.get(following),
                "next_node": hex(following) if following else None,
            })
        # Continue well beyond the authored fall animation. If action 97
        # remains in its looping downed PAT node, recovery is gated by fight
        # context outside this per-player timer/update pair.
        for tick in range(1, 301):
            current_hit_tick[0] = tick
            if tick == 10 or tick >= 175:
                probe._code_trace.clear()
                probe._trace_active = True
            action_before_input = struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0]
            # Original Player common timer update decrements +0x196, unless
            # opponent freeze +0x4a8 is active; then dispatch character update.
            defender_timer_error = _execute(
                uc, defender_timer_entry, STOP, defender,
                STACK + 0xEB00, count=100000)
            defender_update_error = None
            if defender_timer_error is None and struct.unpack(
                    "<H", uc.mem_read(defender + 0x196, 2))[0] == 0:
                # The native frame also dispatches the character's input
                # handler separately from its virtual update. Keep the
                # defender neutral and execute that original path here.
                defender_input_error = _execute(
                    uc, HANDLE_INPUTS, STOP, defender,
                    STACK + 0xEA00,
                    (0, 0, 0, 0, 0, 0, 0), count=400000)
                if defender_input_error is not None:
                    defender_update_error = defender_input_error
            action_after_input = struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0]
            if (defender_update_error is None and defender_timer_error is None
                    and struct.unpack("<H", uc.mem_read(defender + 0x196, 2))[0] == 0):
                defender_update_error = _execute(
                    uc, defender_update_entry, STOP, defender,
                    STACK + 0xEC00, count=250000)
            elif defender_timer_error is not None:
                defender_update_error = defender_timer_error
            if defender_update_error is not None and tick >= 175:
                defender_update_failure_trace = [hex(pc) for pc in probe._code_trace[-120:]]
            if tick == 10:
                defender_transition_trace = [hex(pc) for pc in probe._code_trace[-300:]]
                defender_transition_checkpoint = {
                    "tick": tick,
                    "action_before_input": action_before_input,
                    "action_after_input": action_after_input,
                    "action_after_character_update": struct.unpack(
                        "<H", uc.mem_read(defender + 0x13C, 2))[0],
                    "setters": action_setter_requests[:],
                }
            probe._trace_active = False
            sequence_pointer = struct.unpack("<I", uc.mem_read(defender + 0x15C, 4))[0]
            sequence_metadata = (uc.mem_read(sequence_pointer + 0x14, 1)[0]
                                 if sequence_pointer in action97_sequence_by_pointer else None)
            defender_hitstun_ticks.append({
                "tick": tick,
                "action": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", uc.mem_read(defender + 0x13E, 2))[0],
                "sequence_pointer": hex(sequence_pointer),
                "authored_pat_sequence": action97_sequence_by_pointer.get(sequence_pointer),
                "sequence_loop_mode": sequence_metadata,
                "frame_pointer": hex(struct.unpack("<I", uc.mem_read(defender + 0x158, 4))[0]),
                "pose": struct.unpack("<H", uc.mem_read(defender + 0x140, 2))[0],
                "subframe": struct.unpack("<H", uc.mem_read(defender + 0x142, 2))[0],
                "duration": struct.unpack("<H", uc.mem_read(defender + 0x14C, 2))[0],
                "field_884": struct.unpack("<H", uc.mem_read(defender + 0x884, 2))[0],
                "reaction_timer": struct.unpack("<H", uc.mem_read(defender + 0x194, 2))[0],
                "hitstop": struct.unpack("<H", uc.mem_read(defender + 0x196, 2))[0],
                "input_error": defender_input_error,
                "position": [struct.unpack("<f", uc.mem_read(defender + offset, 4))[0]
                             for offset in (0xEC, 0xF0)],
                "velocity": [struct.unpack("<f", uc.mem_read(defender + offset, 4))[0]
                             for offset in (0xF4, 0xF8)],
                "error": defender_update_error,
            })
            if defender_update_error:
                break
        damage_result["defender_update_entry"] = hex(defender_update_entry)
        damage_result["defender_timer_entry"] = hex(defender_timer_entry)
        damage_result["action97_pat_graph_before_diagnostic_mutation"] = action97_pat_graph
        damage_result["defender_timer_error"] = defender_timer_error
        damage_result["defender_input_error"] = defender_input_error
        damage_result["defender_update_error"] = defender_update_error
        damage_result["defender_update_failure_trace"] = defender_update_failure_trace
        damage_result["defender_transition_checkpoint"] = defender_transition_checkpoint
        damage_result["defender_transition_trace_tick10"] = defender_transition_trace
        damage_result["action_route_observations_tick10"] = action_route_observations
        damage_result["field_884_writes"] = field_884_writes
        damage_result["defender_hitstun_ticks"] = defender_hitstun_ticks
        damage_result["defender_action_after_updates"] = struct.unpack(
            "<H", uc.mem_read(defender + 0x13C, 2))[0]
        # Probe likely wake-up inputs from an identical post-hit state. Each
        # case restores Player, object-list, owner, and heap regions so actions
        # cannot contaminate one another.
        input_case_states = (
            ("neutral", (0, 0, 0, 0, 0, 0, 0, 0)),
            ("right", (1, 0, 0, 0, 0, 0, 0, 0)),
            ("left", (-1, 0, 0, 0, 0, 0, 0, 0)),
            ("up", (0, -1, 0, 0, 0, 0, 0, 0)),
            ("down", (0, 1, 0, 0, 0, 0, 0, 0)),
            ("A", (0, 0, 1, 0, 0, 0, 0, 0)),
            ("B", (0, 0, 0, 1, 0, 0, 0, 0)),
            ("C", (0, 0, 0, 0, 1, 0, 0, 0)),
            ("D", (0, 0, 0, 0, 0, 1, 0, 0)),
            ("down+C", (0, 1, 0, 0, 1, 0, 0, 0)),
        )
        input_probe_snapshots = (
            (defender, bytes(uc.mem_read(defender, 0x1400))),
            (LIST, bytes(uc.mem_read(LIST, 0x10000))),
            (OWNER, bytes(uc.mem_read(OWNER, 0x10000))),
            (HEAP, bytes(uc.mem_read(HEAP, 0x100000))),
        )
        input_recovery_probe: list[dict[str, object]] = []
        for label, state in input_case_states:
            for address, snapshot in input_probe_snapshots:
                uc.mem_write(address, snapshot)
            uc.mem_write(defender + 0x754, struct.pack("<8i", *state))
            action_setter_start = len(action_setter_requests)
            sequence_setter_start = len(sequence_setter_requests)
            input_update_error = _execute(
                uc, INPUT_UPDATE, STOP, defender,
                STACK + 0xE900, count=150000)
            key_input_after_update = list(struct.unpack(
                "<8i", uc.mem_read(defender + 0x754, 32)))
            input_error = input_update_error or _execute(
                uc, HANDLE_INPUTS, STOP, defender,
                STACK + 0xEA00, (0, 0, 0, 0, 0, 0, 0), count=400000)
            update_error = input_error or _execute(
                uc, defender_update_entry, STOP, defender,
                STACK + 0xEC00, count=250000)
            pointer = struct.unpack("<I", uc.mem_read(defender + 0x15C, 4))[0]
            input_recovery_probe.append({
                "input": label,
                "state": list(state),
                "key_input_after_update": key_input_after_update,
                "input_update_error": input_update_error,
                "error": update_error,
                "action": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
                "sequence_counter": struct.unpack("<H", uc.mem_read(defender + 0x13E, 2))[0],
                "authored_pat_sequence": action97_sequence_by_pointer.get(pointer),
                "field_884": struct.unpack("<H", uc.mem_read(defender + 0x884, 2))[0],
                "action_setters": action_setter_requests[action_setter_start:],
                "sequence_setters": sequence_setter_requests[sequence_setter_start:],
            })
        for address, snapshot in input_probe_snapshots:
            uc.mem_write(address, snapshot)
        damage_result["input_recovery_probe"] = input_recovery_probe
        multi_tick_cases = (
            ("A_hold_24", (0, 0, 1, 0, 0, 0, 0, 0)),
            ("B_hold_24", (0, 0, 0, 1, 0, 0, 0, 0)),
            ("C_hold_24", (0, 0, 0, 0, 1, 0, 0, 0)),
            ("D_hold_24", (0, 0, 0, 0, 0, 1, 0, 0)),
            ("down+A_hold_24", (0, 1, 1, 0, 0, 0, 0, 0)),
            ("down+B_hold_24", (0, 1, 0, 1, 0, 0, 0, 0)),
            ("down+C_hold_24", (0, 1, 0, 0, 1, 0, 0, 0)),
            ("down+D_hold_24", (0, 1, 0, 0, 0, 1, 0, 0)),
        )
        multi_tick_recovery_probe: list[dict[str, object]] = []
        for case_index, (label, state) in enumerate(multi_tick_cases):
            for address, snapshot in input_probe_snapshots:
                uc.mem_write(address, snapshot)
            action_setter_start = len(action_setter_requests)
            sequence_setter_start = len(sequence_setter_requests)
            field_write_start = len(field_884_writes)
            timeline: list[dict[str, int | None]] = []
            input_error = None
            for input_tick in range(1, 25):
                current_hit_tick[0] = 350 + case_index * 24 + input_tick
                uc.mem_write(defender + 0x754, struct.pack("<8i", *state))
                input_error = _execute(
                    uc, INPUT_UPDATE, STOP, defender,
                    STACK + 0xE900, count=150000)
                if input_error is None:
                    input_error = _execute(
                        uc, HANDLE_INPUTS, STOP, defender,
                        STACK + 0xEA00, (0, 0, 0, 0, 0, 0, 0), count=400000)
                if input_error is None:
                    input_error = _execute(
                        uc, defender_update_entry, STOP, defender,
                        STACK + 0xEC00, count=250000)
                timeline.append({
                    "tick": input_tick,
                    "action": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
                    "field_884": struct.unpack("<H", uc.mem_read(defender + 0x884, 2))[0],
                })
                if input_error is not None:
                    break
            multi_tick_recovery_probe.append({
                "input": label,
                "state": list(state),
                "ticks_completed": len(timeline),
                "error": input_error,
                "final_action": timeline[-1]["action"] if timeline else None,
                "final_field_884": timeline[-1]["field_884"] if timeline else None,
                "field_writes": field_884_writes[field_write_start:],
                "action_setters": action_setter_requests[action_setter_start:],
                "sequence_setters": sequence_setter_requests[sequence_setter_start:],
            })
            del field_884_writes[field_write_start:]
            del action_setter_requests[action_setter_start:]
            del sequence_setter_requests[sequence_setter_start:]
        for address, snapshot in input_probe_snapshots:
            uc.mem_write(address, snapshot)
        damage_result["multi_tick_input_recovery_probe"] = multi_tick_recovery_probe
        # Replay from immediately after the hit and force +0x884 only on tick
        # 10, just before the 74->97 landing update. This tests the consumer
        # when its action-change callback actually runs.
        for address, snapshot in post_hit_transition_snapshots:
            uc.mem_write(address, snapshot)
        field_gate_setter_start = len(action_setter_requests)
        field_gate_sequence_start = len(sequence_setter_requests)
        field_gate_write_start = len(field_884_writes)
        field_gate_error = None
        for pre_tick in range(1, 10):
            current_hit_tick[0] = 300 + pre_tick
            field_gate_error = _execute(
                uc, defender_timer_entry, STOP, defender,
                STACK + 0xEB00, count=100000)
            if field_gate_error is not None:
                break
            if struct.unpack("<H", uc.mem_read(defender + 0x196, 2))[0] == 0:
                field_gate_error = _execute(
                    uc, HANDLE_INPUTS, STOP, defender, STACK + 0xEA00,
                    (0, 0, 0, 0, 0, 0, 0), count=400000)
                if field_gate_error is None:
                    field_gate_error = _execute(
                        uc, defender_update_entry, STOP, defender,
                        STACK + 0xEC00, count=250000)
            if field_gate_error is not None:
                break
        if field_gate_error is None:
            current_hit_tick[0] = 310
            field_gate_error = _execute(
                uc, defender_timer_entry, STOP, defender,
                STACK + 0xEB00, count=100000)
            if (field_gate_error is None and
                    struct.unpack("<H", uc.mem_read(defender + 0x196, 2))[0] == 0):
                field_gate_error = _execute(
                    uc, HANDLE_INPUTS, STOP, defender, STACK + 0xEA00,
                    (0, 0, 0, 0, 0, 0, 0), count=400000)
            if field_gate_error is None:
                field_884_before_transition = struct.unpack(
                    "<H", uc.mem_read(defender + 0x884, 2))[0]
                uc.mem_write(defender + 0x884, struct.pack("<H", 1))
                field_gate_error = _execute(
                    uc, defender_update_entry, STOP, defender,
                    STACK + 0xEC00, count=250000)
        damage_result["field_884_positive_entry_probe"] = {
            "scope": "diagnostic-only; replay post-hit ticks 1-10 and force +0x884=1 just before the action-74 landing update",
            "action_before_tick10_update": 74,
            "field_before_force": locals().get("field_884_before_transition", None),
            "field_forced": 1,
            "error": field_gate_error,
            "action_after_update": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
            "field_after_update": struct.unpack("<H", uc.mem_read(defender + 0x884, 2))[0],
            "setter_requests": action_setter_requests[field_gate_setter_start:],
            "sequence_setter_requests": sequence_setter_requests[field_gate_sequence_start:],
            "field_writes": field_884_writes[field_gate_write_start:],
        }
        del action_setter_requests[field_gate_setter_start:]
        del sequence_setter_requests[field_gate_sequence_start:]
        del field_884_writes[field_gate_write_start:]
        for address, snapshot in input_probe_snapshots:
            uc.mem_write(address, snapshot)
        # Diagnostic only: preserve the authentic 300-tick evidence above,
        # then clear only the authored down-loop bit to inspect the PAT graph.
        # This fixture mutation does not reproduce the natural action-98 path.
        sequence_pointer = struct.unpack("<I", uc.mem_read(defender + 0x15C, 4))[0]
        loop_mode_before = uc.mem_read(sequence_pointer + 0x14, 1)[0]
        action_setter_count = len(action_setter_requests)
        uc.mem_write(sequence_pointer + 0x14, b"\x00")
        current_hit_tick[0] = 301
        recovery_gate_error = _execute(
            uc, defender_update_entry, STOP, defender,
            STACK + 0xEC00, count=250000)
        recovery_gate_ticks: list[dict[str, object]] = []
        # Allow the authored non-looping sequence 3 to finish after the
        # artificial loop-bit mutation; 60 ticks only reached its first poses.
        for diagnostic_tick in range(1, 121):
            current_hit_tick[0] = 301 + diagnostic_tick
            input_error = _execute(
                uc, HANDLE_INPUTS, STOP, defender,
                STACK + 0xEA00, (0, 0, 0, 0, 0, 0, 0), count=400000)
            update_error = input_error or _execute(
                uc, defender_update_entry, STOP, defender,
                STACK + 0xEC00, count=250000)
            diagnostic_sequence_pointer = struct.unpack(
                "<I", uc.mem_read(defender + 0x15C, 4))[0]
            recovery_gate_ticks.append({
                "tick": diagnostic_tick,
                "action": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
                "sequence_counter": struct.unpack("<H", uc.mem_read(defender + 0x13E, 2))[0],
                "authored_pat_sequence": action97_sequence_by_pointer.get(
                    diagnostic_sequence_pointer),
                "pose": struct.unpack("<H", uc.mem_read(defender + 0x140, 2))[0],
                "error": update_error,
            })
            if update_error or recovery_gate_ticks[-1]["action"] != 97:
                break
        damage_result["recovery_gate_probe"] = {
            "scope": "fixture-only; after authentic timeline, clear authored seq2 loop bit and run extra PE updates",
            "authored_loop_mode": loop_mode_before,
            "forced_loop_mode": uc.mem_read(sequence_pointer + 0x14, 1)[0],
            "sequence_pointer": hex(sequence_pointer),
            "error": recovery_gate_error,
            "action_before": damage_result["defender_action_after_updates"],
            "first_update_action": recovery_gate_ticks[0]["action"] if recovery_gate_ticks else None,
            "first_update_sequence": recovery_gate_ticks[0]["sequence_counter"] if recovery_gate_ticks else None,
            "action_after_diagnostic": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
            "sequence_after_diagnostic": struct.unpack("<H", uc.mem_read(defender + 0x13E, 2))[0],
            "diagnostic_ticks": recovery_gate_ticks,
            "setter_requests": action_setter_requests[action_setter_count:],
        }
        # Isolate action96 from the post-hit state and follow its authentic PAT
        # through the original setter, timer, neutral input handler and update.
        # The PE transition to 96 is still not natural here; this measures the
        # resulting action's real execution once entered.
        for address, snapshot in post_hit_transition_snapshots:
            uc.mem_write(address, snapshot)
        action96_setter_start = len(action_setter_requests)
        action96_sequence_start = len(sequence_setter_requests)
        action96_write_start = len(field_884_writes)
        action96_setter_error = _execute(
            uc, ACTION_SETTER, STOP, defender,
            STACK + 0xE900, (96,), count=200000)
        action96_action_before_ticks = struct.unpack(
            "<H", uc.mem_read(defender + 0x13C, 2))[0]
        action96_error = action96_setter_error
        action96_ticks: list[dict[str, object]] = []
        action96_sequence_by_pointer = {
            pointer: sequence for sequence, pointer in
            probe._sequence_node_by_action[96].items()
        }
        # The original timer periodically calls InfoManager's vtable slot +0x18
        # to refresh HUD design/gauge state. Those rendering resources are not
        # constructed by this gameplay probe, so isolate that presentation-only
        # callback while preserving the original timer and call arguments.
        info_manager_vtable = (probe.heap_cursor + 0xF) & ~0xF
        info_manager_object = info_manager_vtable + 0x100
        probe.heap_cursor = info_manager_object + 0x688 + 0x10
        uc.mem_write(info_manager_vtable, bytes(uc.mem_read(0x85B530, 0x30)))
        # STOP+0x300 is already the stage-floor x87 stub installed by the
        # shared probe; reserve a separate address for this cdecl cleanup shim.
        info_hud_callback = STOP + 0x500
        uc.mem_write(info_manager_vtable + 0x18,
                     struct.pack("<I", info_hud_callback))
        uc.mem_write(info_manager_object, struct.pack("<I", info_manager_vtable))
        uc.mem_write(info_manager_object + 4, bytes(0x684))
        uc.mem_write(info_hud_callback, b"\xc2\x0c\x00")
        uc.mem_write(0x008985E8, struct.pack("<I", info_manager_object))
        info_hud_callback_calls: list[dict[str, str]] = []
        action96_code_trace: list[int] = []
        action96_stack_trace: list[dict[str, str]] = []
        action96_invalid_fetches: list[str] = []
        action96_epilogue: list[dict[str, str]] = []
        action96_phase = ["idle"]
        action96_invalid_context: list[dict[str, object]] = []
        action96_timer_return: list[dict[str, object]] = []
        def action96_code_observer(machine, address: int, _size: int, _user: object) -> None:
            action96_code_trace.append(address)
            del action96_code_trace[:-500]
            action96_stack_trace.append({
                "address": hex(address),
                "esp": hex(machine.reg_read(UC_X86_REG_ESP)),
            })
            del action96_stack_trace[:-300]
            if address == info_hud_callback:
                esp = machine.reg_read(UC_X86_REG_ESP)
                info_hud_callback_calls.append({
                    "kind": hex(struct.unpack("<I", machine.mem_read(esp + 4, 4))[0]),
                    "player_id": hex(struct.unpack("<I", machine.mem_read(esp + 8, 4))[0]),
                    "timer_value": hex(struct.unpack("<I", machine.mem_read(esp + 12, 4))[0]),
                })
            if address == 0x00463CD0:
                esp = machine.reg_read(UC_X86_REG_ESP)
                action96_timer_return.append({
                    "esp": hex(esp),
                    "stack_words": [hex(struct.unpack(
                        "<I", machine.mem_read(esp + offset, 4))[0])
                        for offset in (0, 4, 8, 12)],
                })
                del action96_timer_return[:-8]
            if address == 0x00606ABE:
                esp = machine.reg_read(UC_X86_REG_ESP)
                ebp = machine.reg_read(UC_X86_REG_EBP)
                action96_epilogue.append({
                    "esp": hex(esp),
                    "ebp": hex(ebp),
                    "return_address": hex(struct.unpack(
                        "<I", machine.mem_read(esp, 4))[0]),
                    "stack_words": [hex(struct.unpack(
                        "<I", machine.mem_read(esp + offset, 4))[0])
                        for offset in (0, 4, 8, 12)],
                })
                del action96_epilogue[:-8]
            if address < 0x1000:
                action96_invalid_fetches.append(hex(address))
                action96_invalid_context.append({
                    "phase": action96_phase[0],
                    "address": hex(address),
                    "esp": hex(machine.reg_read(UC_X86_REG_ESP)),
                    "stack_words": [hex(struct.unpack(
                        "<I", machine.mem_read(machine.reg_read(UC_X86_REG_ESP) + offset, 4))[0])
                        for offset in (0, 4, 8, 12)],
                    "trace_tail": action96_stack_trace[-100:],
                })
                machine.emu_stop()
        action96_code_hook = uc.hook_add(UC_HOOK_CODE, action96_code_observer)
        for action96_tick in range(1, 1201):
            if action96_error is not None:
                break
            current_hit_tick[0] = 400 + action96_tick
            action96_phase[0] = "timer"
            action96_error = _execute(
                uc, defender_timer_entry, STOP, defender,
                STACK + 0xE800, count=100000)
            if action96_error is None and struct.unpack(
                    "<H", uc.mem_read(defender + 0x196, 2))[0] == 0:
                action96_phase[0] = "neutral_inputs"
                action96_error = _execute(
                    uc, HANDLE_INPUTS, STOP, defender, STACK + 0xE700,
                    (0, 0, 0, 0, 0, 0, 0), count=400000)
            if action96_error is None:
                action96_phase[0] = "character_update"
                action96_error = _execute(
                    uc, defender_update_entry, STOP, defender,
                    STACK + 0xE600, count=250000)
            sequence_pointer = struct.unpack(
                "<I", uc.mem_read(defender + 0x15C, 4))[0]
            frame_pointer = struct.unpack(
                "<I", uc.mem_read(defender + 0x158, 4))[0]
            frame_valid = any(start <= frame_pointer < end
                              for start, end in probe._active_pat_ranges)
            action96_ticks.append({
                "tick": action96_tick,
                "action": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", uc.mem_read(defender + 0x13E, 2))[0],
                "sequence_node": hex(sequence_pointer),
                "pat_sequence_for_node": action96_sequence_by_pointer.get(sequence_pointer),
                "pose": struct.unpack("<H", uc.mem_read(defender + 0x140, 2))[0],
                "frame_pointer": hex(frame_pointer),
                "frame_in_pat_fixture": frame_valid,
                "hitstop": struct.unpack("<H", uc.mem_read(defender + 0x196, 2))[0],
                "invalid_code_fetch": bool(action96_invalid_fetches),
                "error": action96_error,
            })
            if (action96_error is not None or action96_invalid_fetches or
                    action96_ticks[-1]["action"] != 96):
                break
        uc.hook_del(action96_code_hook)
        damage_result["action96_original_execution"] = {
            "scope": "original action setter, timer, neutral handleInputs and update from the post-hit Player snapshot; entry into 96 is explicitly forced",
            "setter_error": action96_setter_error,
            "setter_action": 96,
            "action_before_ticks": action96_action_before_ticks,
            "ticks": action96_ticks,
            "action_setter_requests": action_setter_requests[action96_setter_start:],
            "sequence_setter_requests": sequence_setter_requests[action96_sequence_start:],
            "field_884_writes": field_884_writes[action96_write_start:],
            "invalid_code_fetches": action96_invalid_fetches,
            "epilogue_before_ret": action96_epilogue,
            "invalid_fetch_context": action96_invalid_context,
            "timer_return_before_ret": action96_timer_return,
            "info_manager_hud_shim": {
                "object": hex(info_manager_object),
                "vtable": hex(info_manager_vtable),
                "original_vtable": "0x85b530",
                "original_slot_6": "0x47eb70",
                "isolated_callback": hex(info_hud_callback),
                "callback_calls": info_hud_callback_calls,
            },
            "trace_tail": [hex(pc) for pc in action96_code_trace[-80:]],
            "final_action": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
            "final_field_884": struct.unpack("<H", uc.mem_read(defender + 0x884, 2))[0],
        }
        # The earlier response snapshot must not inherit this diagnostic's
        # later appends through shared list references.
        damage_result["action_setter_requests"] = action_setter_requests[:action96_setter_start]
        damage_result["sequence_setter_requests"] = sequence_setter_requests[:action96_sequence_start]
        damage_result["field_884_writes"] = field_884_writes[:action96_write_start]
    result = {
        "schema": 3,
        "reference_sha256": digest,
        "constructor": ctor_state,
        "crt_error": crt_error,
        "global_list_error": list_error,
        "original_action_setter_error": setter_error,
        "action_before_handler": action_before_handler,
        "handler_entry": hex(HANDLE_INPUTS),
        "handler_error": handler_error,
        "branch": hex(TARGET_BRANCH),
        "key_input": list(struct.unpack("<2i", uc.mem_read(PLAYER + 0x754, 8))),
        "buffered_gate_word_784": struct.unpack("<I", uc.mem_read(PLAYER + 0x784, 4))[0],
        "input_seed_error": seed_error,
        "ring_before_updates": [hex(value) for value in ring_before],
        "input_trace": input_trace,
        "matcher_calls": observations["matcher_calls"],
        "facing": struct.unpack("<b", uc.mem_read(PLAYER + 0x104, 1))[0],
        "setter_requests": observations["setter_requests"],
        "action_after_handler": action_after,
        "cleanup_entry_reached": observations["cleanup_entry_reached"],
        "original_cleanup_error": cleanup_error,
        "character_update_entry": hex(update_entry),
        "character_update_error": pat_update_error,
        "pat_ticks": pat_ticks,
        "prepared_pat_actions": [int(row["action"]) for row in probe.pat_fixture["actions"]],
        "defender_constructor_error": defender_ctor_error,
        "defender_action_setter_error": defender_setter_error if geometry_result is not None else None,
        "defender_action_before_hit": (defender_action_before_hit if geometry_result is not None else None),
        "reaction_fixture": ({"action": 50, "lookup_action": 74,
                              "setter": reaction_setter,
                              "map_root": hex(reaction_map_root)}
                             if geometry_result is not None else None),
        "defender_action_setter": defender_setter,
        "geometry_after_transition": geometry_result,
        "attacker_box_sync_error": attacker_box_sync_error,
        "defender_box_sync_error": defender_box_sync_error,
        "damage_after_transition": damage_result,
        "handler_trace_tail": observations["handler_trace"][-100:],
        "trace_tail": [hex(pc) for pc in probe._code_trace[-80:]],
        "invalid_memory": probe._invalid_memory[-8:],
        "passed": handler_error is None and bool(observations["handler_branch_reached"])
        and observations["setter_requests"] == [418] and action_after == 418
        and geometry_result is not None and geometry_result["return_value"] == 1
        and damage_result is not None and damage_result["resolver_error"] is None
        and damage_result["hp_defender"] == 800
        and damage_result["action_defender"] == 74,
        "scope": "Original Suika Player constructor, action setter 200, PE ring seeder 0x46d950, four input updates 0x46d5d0 with original matcher 0x487020, full handleInputs 0x609dc0, original cleanup 0x46cac0, and up to 16 virtual character updates execute on the same constructed Player/deque. C is held in the deterministic fixture while the NRNR horizontal sequence is entered, allowing 0x46d5d0 to derive Player+0x784. Damage and reaction 74 execute through the original pair resolver using Suika action 50 as the reaction PAT alias; authentic Suika action96/97 PAT is included. The original common timer 0x46a330, neutral defender handleInputs 0x609dc0, and character update slot10 run for 300 post-hit ticks. A forced-entry action96 diagnostic runs up to 1200 ticks; its InfoManager singleton is a controlled object using the original vtable except for slot +0x18, the HUD/gauge rendering callback, which is shimmed to preserve its 12-byte cleanup while recording arguments. The harness still controls stage floor (500), geometry placement, fight-state query and effect rendering; the manager/round caller and complete external tick context remain absent.",
    }
    if not result["passed"]:
        raise AssertionError(json.dumps(result, indent=2))
    return result


def main() -> None:
    report = run()
    out = ROOT / "artifacts/x86-suika-constructed-handler.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "constructor": report["constructor"],
                      "action": report["action_after_handler"], "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
