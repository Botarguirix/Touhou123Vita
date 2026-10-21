#!/usr/bin/env python3
"""Run Suika's original action setter and controlled Player updates with PAT data."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))
sys.path.insert(0, str(ROOT))
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
                               UC_X86_REG_EDI, UC_X86_REG_EDX, UC_X86_REG_EBP,
                               UC_X86_REG_EIP, UC_X86_REG_ESI,
                               UC_X86_REG_ESP)
from tools.extract_pat_pose_metadata import action_sequence_metadata, read_pat
from tools.x86_remilia_412_spawn_probe import (
    initialize_object_manager, initialize_original_action,
    run_original_character_update,
)
from tools.x86_suwako_808_factory_probe import (
    HEAP, LIST, OWNER, PAT_MAP, STACK, STOP, Suwako808FactoryProbe,
)

EXE = ROOT / "original/th123.exe"
SUIKA_VTABLE = 0x0085DA84
ACTION_SETTER = 0x00464930
PLAYER = LIST + 0x8000
PLAYER_INFO = OWNER + 0x8000
KEY_MANAGER = OWNER + 0x9000
REMILIA_UPDATE_ENTRY = 0x00587BAB
REMILIA_UPDATE_EXIT = 0x00599FB0


def apply_verified_world_box_transform(uc, obj: int) -> None:
    """Translate PAT-local boxes using the affine transform observed in the PE."""
    x = struct.unpack("<f", uc.mem_read(obj + 0xEC, 4))[0]
    y = struct.unpack("<f", uc.mem_read(obj + 0xF0, 4))[0]
    facing = struct.unpack("<b", uc.mem_read(obj + 0x104, 1))[0]
    for count_offset, boxes_offset in ((0x1CB, 0x220), (0x1CC, 0x1D0)):
        count = uc.mem_read(obj + count_offset, 1)[0]
        for index in range(count):
            address = obj + boxes_offset + index * 16
            left, top, right, bottom = struct.unpack("<4i", uc.mem_read(address, 16))
            x0, x1 = sorted((int(x + facing * left), int(x + facing * right)))
            y0, y1 = sorted((top - int(y), bottom - int(y)))
            uc.mem_write(address, struct.pack("<4i", x0, y0, x1, y1))


def run_action(action_id: int, dat_dir: Path, extra_actions: tuple[int, ...] = (),
               defender_x: float = 420.0, defender_y: float = 180.0,
               resolve_child_pair: bool = True,
               execute_original_rng: bool = False,
               player_x: float = 320.0, player_y: float = 180.0,
               player_facing: int = 1, pin_attacker: bool = True,
               contact_grid: bool = False,
               use_original_world_transform: bool = True) -> dict[str, object]:
    probe = Suwako808FactoryProbe(EXE, dat_dir, character="suika", action_id=801,
                                  intercept_box_transforms=True)
    probe.execute_original_rng = execute_original_rng
    probe.action_id = action_id
    pat_actions = (action_id, *extra_actions)
    probe._prepare_pat_actions(pat_actions)
    uc = probe.uc
    crt_sp = STACK + 0x5000 - 4
    uc.mem_write(crt_sp, struct.pack("<I", STOP))
    uc.reg_write(UC_X86_REG_ESP, crt_sp)
    uc.reg_write(UC_X86_REG_EIP, 0x00824BFA)
    crt_error = None
    try:
        uc.emu_start(0x00824BFA, STOP, count=100000)
    except Exception as exc:
        crt_error = f"{type(exc).__name__}: {exc}"
    crt_eip_after = hex(uc.reg_read(UC_X86_REG_EIP))
    global_list_sp = STACK + 0x5800 - 4
    uc.mem_write(global_list_sp, struct.pack("<I", STOP))
    uc.reg_write(UC_X86_REG_ECX, 0x0089AAE8)
    uc.reg_write(UC_X86_REG_ESP, global_list_sp)
    uc.reg_write(UC_X86_REG_EIP, 0x0046B750)
    global_list_error = None
    try:
        uc.emu_start(0x0046B750, STOP, count=100000)
    except Exception as exc:
        global_list_error = f"{type(exc).__name__}: {exc}"
    global_list_eip_after = hex(uc.reg_read(UC_X86_REG_EIP))
    global_list_head = struct.unpack("<I", uc.mem_read(0x0089AAEC, 4))[0]
    # The PE's static initializer allocates this sentinel node but the local
    # allocator returns zero-filled memory; mark its MSVC list end flag, which
    # the original clone/destroy walk tests at node+0x15.
    if global_list_head:
        uc.mem_write(global_list_head + 0x15, b"\x01")
    uc.mem_write(PLAYER, bytes(0x1000))
    # PlayerInfo is 32 bytes: four header bytes, the 20-byte Deque
    # (debug proxy + table/block count/offset/size), then KeyManager*.
    uc.mem_write(PLAYER_INFO, struct.pack("<I4B6I", 9, 0, 0, 0, 0,
                                         0, 0, 0, 0, 0, KEY_MANAGER))
    uc.mem_write(KEY_MANAGER, bytes(0x100))
    constructor_observations: list[dict[str, object]] = []
    list_copy_observations: list[dict[str, object]] = []
    def observe_deck_copy(machine, address: int, _size: int, _user: object) -> None:
        if address == 0x0046B770 and len(list_copy_observations) < 8:
            esp = machine.reg_read(UC_X86_REG_ESP)
            source = struct.unpack("<I", machine.mem_read(esp + 4, 4))[0]
            head = struct.unpack("<I", machine.mem_read(source + 4, 4))[0] if source else 0
            next_node = struct.unpack("<I", machine.mem_read(head + 4, 4))[0] if head else 0
            list_copy_observations.append({"source": hex(source), "head": hex(head),
                                           "next": hex(next_node), "size": hex(struct.unpack("<I", machine.mem_read(source + 8, 4))[0]) if source else "0x0",
                                           "head_flag": int(machine.mem_read(head + 0x15, 1)[0]) if head else 0})
        if address != 0x0046B540 or len(constructor_observations) >= 8:
            return
        source = struct.unpack("<I", machine.mem_read(machine.reg_read(UC_X86_REG_ESP) + 4, 4))[0]
        constructor_observations.append({
            "return_address": hex(struct.unpack("<I", machine.mem_read(machine.reg_read(UC_X86_REG_ESP), 4))[0]),
            "esp": hex(machine.reg_read(UC_X86_REG_ESP)),
            "source": hex(source),
            "source_0x14": hex(struct.unpack("<I", machine.mem_read(source + 0x14, 4))[0]),
            "source_0x15": int(machine.mem_read(source + 0x15, 1)[0]),
            "source_0x1c": hex(struct.unpack("<I", machine.mem_read(source + 0x1C, 4))[0]),
            "ebx": hex(machine.reg_read(UC_X86_REG_EBX)),
        })
    uc.hook_add(UC_HOOK_CODE, observe_deck_copy)
    player_ctor_sp = STACK + 0xF000 - 8
    uc.mem_write(player_ctor_sp, struct.pack("<II", STOP, PLAYER_INFO))
    uc.reg_write(UC_X86_REG_ECX, PLAYER)
    uc.reg_write(UC_X86_REG_ESP, player_ctor_sp)
    uc.reg_write(UC_X86_REG_EIP, 0x00609D40)
    player_ctor_error = None
    try:
        uc.emu_start(0x00609D40, STOP, count=250000)
    except Exception as exc:
        player_ctor_error = f"{type(exc).__name__}: {exc}"
    player_ctor_eip_after = hex(uc.reg_read(UC_X86_REG_EIP))
    player_ctor_termination = probe.host_termination
    player_object_list = struct.unpack("<I", uc.mem_read(PLAYER + 0x6F8, 4))[0]
    if not player_object_list:
        # Keep the exact Suika manager constructor as a diagnostic fallback
        # when the complete Player constructor reaches a host-only boundary.
        manager_sp = STACK + 0x7000 - 4
        uc.mem_write(manager_sp, struct.pack("<II", STOP, PLAYER))
        uc.reg_write(UC_X86_REG_ECX, LIST)
        uc.reg_write(UC_X86_REG_ESP, manager_sp)
        uc.reg_write(UC_X86_REG_EIP, 0x00609B40)
        manager_error = None
        try:
            uc.emu_start(0x00609B40, STOP, count=100000)
        except Exception as exc:
            manager_error = f"{type(exc).__name__}: {exc}"
        manager_eip_after = hex(uc.reg_read(UC_X86_REG_EIP))
        manager_host_termination = probe.host_termination
        player_object_list = struct.unpack("<I", uc.mem_read(LIST, 4))[0]
    else:
        manager_error = None
        manager_eip_after = "not-run; Player constructor created the manager"
        manager_host_termination = None
    uc.mem_write(PLAYER + 0x160, struct.pack("<I", PAT_MAP))
    uc.mem_write(PLAYER + 0x6F8, struct.pack("<I", player_object_list))

    reached: list[str] = []
    probe._pat_lookup_results = {}
    probe._pat_lookup_action_results = {}
    object_create_calls: list[dict[str, object]] = []
    factory_entry_observations: list[dict[str, object]] = []
    nested_factory_returns: list[dict[str, object]] = []
    object_create_results: list[dict[str, object]] = []
    effect_requests: list[dict[str, object]] = []
    factory_return_observations: list[dict[str, object]] = []
    pat_lookup_calls: list[dict[str, object]] = []
    pat_lookup_walks: list[dict[str, object]] = []
    action_setter_returns: list[dict[str, object]] = []
    update_manager_snapshots: list[dict[str, object]] = []
    rng_observations: list[dict[str, object]] = []
    factory_action_observations: list[dict[str, object]] = []
    sequence_setter_calls: list[dict[str, object]] = []
    landing_gate_observations: list[dict[str, object]] = []
    landing_gate_return_slots: dict[int, int] = {}
    rng_return_slots: dict[int, int] = {}
    current_parent_tick: int | None = None
    # Match the signature-correct EffectManager_Effect stub used by the
    # player-vs-player oracle so hit response can continue past 0x479d0e.
    effect_manager, effect_vtable = OWNER + 0xC000, OWNER + 0xC400
    synthetic_effect, effect_create_stub = OWNER + 0xC800, STOP + 0x500
    uc.mem_write(effect_manager, struct.pack("<I", effect_vtable))
    uc.mem_write(effect_vtable + 0x0C, struct.pack("<I", effect_create_stub))
    uc.mem_write(synthetic_effect, bytes(0x400))
    uc.mem_write(synthetic_effect, struct.pack("<I", 0x00858AB4))
    uc.mem_write(0x008985F0, struct.pack("<I", effect_manager))
    def trace(machine, address: int, _size: int, _user: object) -> None:
        if address == 0x004652A0:
            esp = machine.reg_read(UC_X86_REG_ESP)
            sequence_setter_calls.append({
                "tick": current_parent_tick,
                "caller_return": hex(struct.unpack("<I", machine.mem_read(esp, 4))[0]),
                "requested_sequence": struct.unpack("<H", machine.mem_read(esp + 4, 2))[0],
                "current_action": struct.unpack("<H", machine.mem_read(PLAYER + 0x13C, 2))[0],
                "current_sequence": struct.unpack("<H", machine.mem_read(PLAYER + 0x13E, 2))[0],
                "current_pose": struct.unpack("<H", machine.mem_read(PLAYER + 0x140, 2))[0],
                "caller_trace": [hex(pc) for pc in probe._code_trace[-48:]],
            })
        if address == 0x00487EA0:
            esp = machine.reg_read(UC_X86_REG_ESP)
            return_address = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            landing_gate_return_slots[return_address] = len(landing_gate_observations)
            landing_gate_observations.append({
                "tick": current_parent_tick,
                "return_address": hex(return_address),
                "action": struct.unpack("<H", machine.mem_read(PLAYER + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", machine.mem_read(PLAYER + 0x13E, 2))[0],
                "pose": struct.unpack("<H", machine.mem_read(PLAYER + 0x140, 2))[0],
                "position_y": struct.unpack("<f", machine.mem_read(PLAYER + 0xF0, 4))[0],
                "vertical_velocity": struct.unpack("<f", machine.mem_read(PLAYER + 0xF8, 4))[0],
                "vertical_acceleration": struct.unpack("<f", machine.mem_read(PLAYER + 0x100, 4))[0],
                "floor_or_boundary_flag": machine.mem_read(PLAYER + 0x4C4, 1)[0],
            })
        elif address in landing_gate_return_slots:
            index = landing_gate_return_slots.pop(address)
            landing_gate_observations[index]["returns_true"] = (machine.reg_read(UC_X86_REG_EAX) & 0xFF) != 0
            landing_gate_observations[index]["position_y_after"] = struct.unpack(
                "<f", machine.mem_read(PLAYER + 0xF0, 4))[0]
            landing_gate_observations[index]["vertical_velocity_after"] = struct.unpack(
                "<f", machine.mem_read(PLAYER + 0xF8, 4))[0]
        if address == 0x004099F0:
            esp = machine.reg_read(UC_X86_REG_ESP)
            return_address = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            rng_return_slots[return_address] = len(rng_observations)
            rng_observations.append({"tick": current_parent_tick,
                                     "caller": hex(return_address),
                                     "limit": struct.unpack("<I", machine.mem_read(esp + 4, 4))[0],
                                     "result": None})
        elif address in rng_return_slots:
            index = rng_return_slots.pop(address)
            rng_observations[index]["result"] = machine.reg_read(UC_X86_REG_EAX)
        if address == 0x0079B01C:
            obj = machine.reg_read(UC_X86_REG_ESI)
            factory_action_observations.append({
                "tick": current_parent_tick,
                "action": struct.unpack("<H", machine.mem_read(obj + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", machine.mem_read(obj + 0x13E, 2))[0],
                "position": [struct.unpack("<f", machine.mem_read(obj + offset, 4))[0]
                             for offset in (0xEC, 0xF0)],
                "anchor": hex(struct.unpack("<I", machine.mem_read(obj + 0x398, 4))[0]),
                "random_state": [struct.unpack("<f", machine.mem_read(obj + offset, 4))[0]
                                 for offset in (0x378, 0x37C, 0x11C, 0x120, 0x12C)]})
        if address == effect_create_stub:
            esp = machine.reg_read(UC_X86_REG_ESP)
            args = [struct.unpack("<I", machine.mem_read(esp + 4 * i, 4))[0]
                    for i in range(1, 7)]
            effect_requests.append({"manager": hex(machine.reg_read(UC_X86_REG_ECX)),
                                    "arguments_u32": [hex(value) for value in args],
                                    "x": struct.unpack("<f", struct.pack("<I", args[1]))[0],
                                    "y": struct.unpack("<f", struct.pack("<I", args[2]))[0]})
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, synthetic_effect)
            machine.reg_write(UC_X86_REG_ESP, esp + 4 + 6 * 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
            return
        if address == 0x0043F2F0 and getattr(probe, "_pat_lookup_results", None) is not None:
            esp = machine.reg_read(UC_X86_REG_ESP)
            map_key = machine.reg_read(UC_X86_REG_ECX)
            action_ptr = struct.unpack("<I", machine.mem_read(esp + 8, 4))[0]
            action_key = struct.unpack("<I", machine.mem_read(action_ptr, 4))[0]
            backing = getattr(probe, "_pat_lookup_action_results", {}).get(
                (map_key, action_key), probe._pat_lookup_results.get(map_key))
            if backing is not None:
                output_pair = struct.unpack("<I", machine.mem_read(esp + 4, 4))[0]
                machine.mem_write(output_pair, bytes(machine.mem_read(backing, 8)))
                ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
                machine.reg_write(UC_X86_REG_EAX, output_pair)
                machine.reg_write(UC_X86_REG_ESP, esp + 12)
                machine.reg_write(UC_X86_REG_EIP, ret)
                return
        if address == 0x00784020:
            esp = machine.reg_read(UC_X86_REG_ESP)
            words = [struct.unpack("<I", machine.mem_read(esp + 4 * i, 4))[0]
                     for i in range(10)]
            factory_entry_observations.append({"ecx": hex(machine.reg_read(UC_X86_REG_ECX)),
                                               "stack": [hex(value) for value in words],
                                               "x": struct.unpack("<f", struct.pack("<I", words[4]))[0],
                                               "y": struct.unpack("<f", struct.pack("<I", words[5]))[0],
                                               "custom_data_floats": list(struct.unpack(
                                                   "<3f", machine.mem_read(words[8], 12)))
                                               if words[8] else None})
        if address == 0x007840FD and factory_entry_observations:
            obj = machine.reg_read(UC_X86_REG_EAX)
            if obj > 0x1000:
                nested_factory_returns.append({"object": hex(obj),
                                               "caller": factory_entry_observations[-1]["stack"][0],
                                               "action": struct.unpack("<H", machine.mem_read(obj + 0x13C, 2))[0],
                                               "sequence": struct.unpack("<H", machine.mem_read(obj + 0x13E, 2))[0],
                                               "pose_count": struct.unpack("<H", machine.mem_read(obj + 0x148, 2))[0],
                                               "position": [struct.unpack("<f", machine.mem_read(obj + 0xEC, 4))[0],
                                                            struct.unpack("<f", machine.mem_read(obj + 0xF0, 4))[0]],
                                               "velocity": [struct.unpack("<f", machine.mem_read(obj + 0xF4, 4))[0],
                                                            struct.unpack("<f", machine.mem_read(obj + 0xF8, 4))[0]],
                                               "alpha": machine.mem_read(obj + 0x113, 1)[0],
                                               "active": struct.unpack("<I", machine.mem_read(obj + 0x34C, 4))[0]})
        if address == 0x0046EB30:
            esp = machine.reg_read(UC_X86_REG_ESP)
            args = [struct.unpack("<I", machine.mem_read(esp + 4 * i, 4))[0]
                    for i in range(1, 9)]
            manager = struct.unpack("<I", machine.mem_read(PLAYER + 0x6F8, 4))[0]
            object_create_calls.append({"entry": hex(address), "player": hex(machine.reg_read(UC_X86_REG_ECX)),
                                        "manager": hex(manager),
                                        "manager_vtable": hex(struct.unpack("<I", machine.mem_read(manager, 4))[0]) if manager else None,
                                        "stack_args": [hex(value) for value in args],
                                        "requested_action_object": hex(args[0])})
            # The original Suika manager's interface slot points outside this
            # pinned image in the isolated PE. Route its virtual factory slot
            # to the in-image createObject implementation, matching the
            # already-established Remilia factory probe.
            if action_id == 530:
                vtable = struct.unpack("<I", machine.mem_read(manager, 4))[0]
                machine.mem_write(vtable + 4, struct.pack("<I", 0x00784020))
        if address == 0x005F94DF and object_create_calls:
            obj = machine.reg_read(UC_X86_REG_EAX)
            if obj and obj > 0x1000:
                anchor = struct.unpack("<I", machine.mem_read(obj + 0x398, 4))[0]
                factory_return_observations.append({"object": hex(obj),
                                                    "vtable": hex(struct.unpack("<I", machine.mem_read(obj, 4))[0]),
                                                    "action": struct.unpack("<H", machine.mem_read(obj + 0x13C, 2))[0],
                                                    "sequence": struct.unpack("<H", machine.mem_read(obj + 0x13E, 2))[0],
                                                    "pose": struct.unpack("<H", machine.mem_read(obj + 0x140, 2))[0],
                                                    "pose_count": struct.unpack("<H", machine.mem_read(obj + 0x148, 2))[0],
                                                    "owner": hex(struct.unpack("<I", machine.mem_read(obj + 0x16C, 4))[0]),
                                                    "position": [struct.unpack("<f", machine.mem_read(obj + 0xEC, 4))[0],
                                                                 struct.unpack("<f", machine.mem_read(obj + 0xF0, 4))[0]],
                                                    "anchor": hex(anchor),
                                                    "anchor_position": [struct.unpack("<f", machine.mem_read(anchor + offset, 4))[0]
                                                                        for offset in (0xEC, 0xF0)],
                                                    "velocity": [struct.unpack("<f", machine.mem_read(obj + 0xF4, 4))[0],
                                                                 struct.unpack("<f", machine.mem_read(obj + 0xF8, 4))[0]],
                                                    "alpha": machine.mem_read(obj + 0x113, 1)[0],
                                                    "active": struct.unpack("<I", machine.mem_read(obj + 0x34C, 4))[0],
                                                    "custom_data": hex(struct.unpack("<I", machine.mem_read(obj + 0x35C, 4))[0])})
        if address in (ACTION_SETTER, 0x00438CA0, 0x00465370,
                       0x006086A0, 0x00608670, 0x0043F2F0):
            reached.append(hex(address))
        if address == 0x00464947:
            obj = machine.reg_read(UC_X86_REG_ESI)
            esp = machine.reg_read(UC_X86_REG_ESP)
            action_setter_returns.append({"object": hex(obj),
                                          "caller": hex(struct.unpack("<I", machine.mem_read(esp, 4))[0]),
                                          "vtable": hex(struct.unpack("<I", machine.mem_read(obj, 4))[0]),
                                          "action": struct.unpack("<H", machine.mem_read(obj + 0x13C, 2))[0],
                                          "sequence": struct.unpack("<H", machine.mem_read(obj + 0x13E, 2))[0],
                                          "pose": struct.unpack("<H", machine.mem_read(obj + 0x140, 2))[0],
                                          "pose_count": struct.unpack("<H", machine.mem_read(obj + 0x148, 2))[0],
                                          "pat_map": hex(struct.unpack("<I", machine.mem_read(obj + 0x160, 4))[0]),
                                          "sequence_node": hex(struct.unpack("<I", machine.mem_read(obj + 0x15C, 4))[0]),
                                          "position": [struct.unpack("<f", machine.mem_read(obj + 0xEC, 4))[0],
                                                       struct.unpack("<f", machine.mem_read(obj + 0xF0, 4))[0]],
                                          "velocity": [struct.unpack("<f", machine.mem_read(obj + 0xF4, 4))[0],
                                                       struct.unpack("<f", machine.mem_read(obj + 0xF8, 4))[0]],
                                          "alpha": machine.mem_read(obj + 0x113, 1)[0],
                                          "active": struct.unpack("<I", machine.mem_read(obj + 0x34C, 4))[0],
                                          "owner": hex(struct.unpack("<I", machine.mem_read(obj + 0x16C, 4))[0])})
        if address == 0x0043F2F0:
            esp = machine.reg_read(UC_X86_REG_ESP)
            this_ptr = machine.reg_read(UC_X86_REG_ECX)
            map_ptr = struct.unpack("<I", machine.mem_read(esp + 4, 4))[0]
            key_ptr = struct.unpack("<I", machine.mem_read(esp + 8, 4))[0]
            pat_lookup_calls.append({"return_address": hex(struct.unpack("<I", machine.mem_read(esp, 4))[0]),
                                     "this": hex(this_ptr),
                                     "object_action": struct.unpack("<H", machine.mem_read(this_ptr + 0x13C, 2))[0],
                                     "object_pat_map": hex(struct.unpack("<I", machine.mem_read(this_ptr + 0x160, 4))[0]),
                                     "map_arg": hex(map_ptr),
                                     "key_pointer": hex(key_ptr),
                                     "key_value": struct.unpack("<I", machine.mem_read(key_ptr, 4))[0] if key_ptr else None})
        if address in (0x0043F307, 0x0043F30A, 0x0043F311, 0x0043F313, 0x0043F315,
                       0x0043F319, 0x0043F30C, 0x0043F30F):
            pat_lookup_walks.append({"eip": hex(address),
                                     "ecx": hex(machine.reg_read(UC_X86_REG_ECX)),
                                     "eax": hex(machine.reg_read(UC_X86_REG_EAX)),
                                     "edx": hex(machine.reg_read(UC_X86_REG_EDX)),
                                     "esp": hex(machine.reg_read(UC_X86_REG_ESP))})

    uc.hook_add(UC_HOOK_CODE, trace)
    sp = STACK + 0xEFF0
    uc.mem_write(sp, struct.pack("<II", STOP, action_id))
    uc.reg_write(UC_X86_REG_ECX, PLAYER)
    uc.reg_write(UC_X86_REG_ESI, PLAYER)
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_EIP, ACTION_SETTER)
    error = None
    probe._code_trace.clear()
    probe._trace_active = True
    try:
        uc.emu_start(ACTION_SETTER, STOP, count=100000)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        probe._trace_active = False

    result = {
        "action_requested": action_id,
        "action": struct.unpack("<H", uc.mem_read(PLAYER + 0x13C, 2))[0],
        "sequence": struct.unpack("<H", uc.mem_read(PLAYER + 0x13E, 2))[0],
        "pose": struct.unpack("<H", uc.mem_read(PLAYER + 0x140, 2))[0],
        "pose_count": struct.unpack("<H", uc.mem_read(PLAYER + 0x148, 2))[0],
        "sequence_node": hex(struct.unpack("<I", uc.mem_read(PLAYER + 0x15C, 4))[0]),
        "pat_fixture": probe.pat_fixture,
        "functions_reached": reached,
        "rng_observations": rng_observations,
        "factory_action_observations": factory_action_observations,
        "object_create_calls": object_create_calls,
        "factory_entry_observations": factory_entry_observations,
        "nested_factory_returns": nested_factory_returns,
        "object_create_results": object_create_results,
        "factory_return_observations": factory_return_observations,
        "pat_lookup_calls": pat_lookup_calls,
        "pat_lookup_walks": pat_lookup_walks[-96:],
        "action_setter_returns": action_setter_returns,
        "object_manager_state": {
            "root_pointer": hex(struct.unpack("<I", uc.mem_read(player_object_list + 0x58, 4))[0])
            if player_object_list else None,
            "manager_words": [hex(struct.unpack("<I", uc.mem_read(player_object_list + offset, 4))[0])
                              for offset in (0x54, 0x58, 0x5C, 0x60, 0x64, 0x68)]
            if player_object_list else [],
        },
        "error": error,
        "eip_after": hex(uc.reg_read(UC_X86_REG_EIP)),
        "invalid_memory": probe._invalid_memory[-8:],
        "trace_tail": [hex(pc) for pc in probe._code_trace[-32:]],
        "object_manager": {
            "constructor": "PlayerSuika 0x609d40; original Suika object manager created at Player+0x6f8",
            "error": manager_error,
            "eip_after": manager_eip_after,
            "completed": player_object_list != 0,
            "host_termination": manager_host_termination,
            "vtable": hex(struct.unpack("<I", uc.mem_read(player_object_list, 4))[0])
            if player_object_list else None,
        },
        "player_constructor": {
            "entry": "0x609d40",
            "error": player_ctor_error,
            "eip_after": player_ctor_eip_after,
            "host_termination": player_ctor_termination,
        },
        "crt_init": {"error": crt_error, "eip_after": crt_eip_after},
        "global_list_constructor": {"entry": "0x46b750", "error": global_list_error,
                                    "eip_after": global_list_eip_after,
                                    "head": hex(global_list_head),
                                    "size": struct.unpack("<I", uc.mem_read(0x0089AAF0, 4))[0]},
        "constructor_observations": constructor_observations,
        "list_copy_observations": list_copy_observations,
    }
    if error is None:
        result["setter_state"] = {key: result[key] for key in
                                  ("action", "sequence", "pose", "pose_count", "sequence_node")}
        if action_id in (530, 531):
            # Give the spawning route a concrete arena position; this lets the
            # original factory's relative coordinates flow into its child.
            uc.mem_write(PLAYER + 0x0EC, struct.pack("<f", player_x))
            uc.mem_write(PLAYER + 0x0F0, struct.pack("<f", player_y))
            uc.mem_write(PLAYER + 0x104, struct.pack("<b", player_facing))
        update_entry = struct.unpack("<I", uc.mem_read(SUIKA_VTABLE + 10 * 4, 4))[0]
        update_sp = STACK + 0xEFD0
        update_ticks: list[dict[str, object]] = []
        animation_writes: list[dict[str, object]] = []
        update_error = None
        probe.host_termination = None
        def capture_animation_write(machine, _access, address, size, value, _user):
            if (current_parent_tick is None or address >= PLAYER + 0x150 or
                    address + size <= PLAYER + 0x13C or size > 8):
                return
            animation_writes.append({
                "tick": current_parent_tick, "eip": hex(machine.reg_read(UC_X86_REG_EIP)),
                "address": hex(address), "size": size,
                "old": bytes(machine.mem_read(address, size)).hex(),
                "new": int(value).to_bytes(size, "little", signed=False).hex(),
                "trace_before": [hex(pc) for pc in probe._code_trace[-40:]]
                if address < PLAYER + 0x140 and address + size > PLAYER + 0x13E else [],
            })
        animation_write_hook = uc.hook_add(UC_HOOK_MEM_WRITE, capture_animation_write)
        for tick in range(1, 41):
            current_parent_tick = tick
            create_calls_before = len(object_create_calls)
            factory_returns_before = len(factory_return_observations)
            uc.mem_write(update_sp, struct.pack("<I", STOP))
            uc.reg_write(UC_X86_REG_ECX, PLAYER)
            uc.reg_write(UC_X86_REG_ESP, update_sp)
            uc.reg_write(UC_X86_REG_EIP, update_entry)
            probe._code_trace.clear()
            probe._trace_active = True
            try:
                uc.emu_start(update_entry, STOP, count=250000)
            except Exception as exc:
                update_error = f"{type(exc).__name__}: {exc}"
            finally:
                probe._trace_active = False
            frame_pointer = struct.unpack("<I", uc.mem_read(PLAYER + 0x158, 4))[0]
            player_position = [struct.unpack("<f", uc.mem_read(PLAYER + offset, 4))[0]
                               for offset in (0xEC, 0xF0)]
            active_pat_ranges = getattr(probe, "_active_pat_ranges", [(PAT_MAP, PAT_MAP + 0x80000)])
            frame_valid = any(start <= frame_pointer < end for start, end in active_pat_ranges)
            frame_damage = (struct.unpack("<H", uc.mem_read(frame_pointer + 0x1C, 2))[0]
                            if frame_valid else None)
            box_start, box_end = ((struct.unpack("<I", uc.mem_read(frame_pointer + 0x6C, 4))[0],
                                   struct.unpack("<I", uc.mem_read(frame_pointer + 0x70, 4))[0])
                                  if frame_valid else (0, 0))
            update_ticks.append({
                "tick": tick,
                "eip_after": hex(uc.reg_read(UC_X86_REG_EIP)),
                "action": struct.unpack("<H", uc.mem_read(PLAYER + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", uc.mem_read(PLAYER + 0x13E, 2))[0],
                "pose": struct.unpack("<H", uc.mem_read(PLAYER + 0x140, 2))[0],
                "position": player_position,
                "frame_data_pointer": hex(frame_pointer),
                "frame_damage": frame_damage,
                "frame_attack_box_count": (box_end - box_start) // 16 if frame_valid else None,
                "object_create_calls": object_create_calls[create_calls_before:],
                "factory_returns": factory_return_observations[factory_returns_before:],
                "state_0x13c_0x14f": bytes(uc.mem_read(PLAYER + 0x13C, 0x14)).hex(),
                "trace_tail": [hex(pc) for pc in probe._code_trace[-16:]],
            })
            if update_error or uc.reg_read(UC_X86_REG_EIP) != STOP:
                break
        uc.hook_del(animation_write_hook)
        result["update"] = {
            "entry": hex(update_entry),
            "error": update_error,
            "host_termination": probe.host_termination,
            "stop_reason": ("host-termination" if probe.host_termination else
                            "exception" if update_error else
                            "returned-to-stop" if update_ticks and update_ticks[-1]["eip_after"] == hex(STOP)
                            else "unexpected-control-flow"),
            "ticks_completed": len(update_ticks),
            "ticks": update_ticks,
            "player_animation_writes": animation_writes,
            "sequence_setter_calls": sequence_setter_calls,
            "landing_gate_observations": landing_gate_observations,
            "action": struct.unpack("<H", uc.mem_read(PLAYER + 0x13C, 2))[0],
            "sequence": struct.unpack("<H", uc.mem_read(PLAYER + 0x13E, 2))[0],
            "pose": struct.unpack("<H", uc.mem_read(PLAYER + 0x140, 2))[0],
            "pose_count": struct.unpack("<H", uc.mem_read(PLAYER + 0x148, 2))[0],
            "invalid_memory": probe._invalid_memory[-8:],
            "allocations_tail": probe.allocations[-12:],
            "events_tail": probe.events[-12:],
            "trace_tail": [hex(pc) for pc in probe._code_trace[-32:]],
        }
        spawned = [row for row in action_setter_returns if row["action"] == 821]
        child_updates: list[dict[str, object]] = []
        child_box_sync: dict[str, object] | None = None
        child_pair_dispatch: dict[str, object] | None = None
        if action_id in (530, 531) and factory_return_observations:
            child_observations: list[dict[str, object]] = []
            child_update_entry = 0x007876D0
            def update_child(child_tick: int) -> dict[str, object]:
                child_sp = STACK + 0xD000 - 4
                uc.mem_write(child_sp, struct.pack("<I", STOP))
                uc.reg_write(UC_X86_REG_ECX, child)
                uc.reg_write(UC_X86_REG_ESP, child_sp)
                uc.reg_write(UC_X86_REG_EIP, child_update_entry)
                probe._code_trace.clear()
                probe._trace_active = True
                child_error = None
                try:
                    uc.emu_start(child_update_entry, STOP, count=250000)
                except Exception as exc:
                    child_error = f"{type(exc).__name__}: {exc}"
                finally:
                    probe._trace_active = False
                frame_ptr = struct.unpack("<I", uc.mem_read(child + 0x1C0, 4))[0]
                active_pat_ranges = getattr(probe, "_active_pat_ranges", [(PAT_MAP, PAT_MAP + 0x80000)])
                frame_valid = any(start <= frame_ptr < end for start, end in active_pat_ranges)
                row = {"tick": child_tick,
                                      "error": child_error,
                                      "eip_after": hex(uc.reg_read(UC_X86_REG_EIP)),
                                      "action": struct.unpack("<H", uc.mem_read(child + 0x13C, 2))[0],
                                      "sequence": struct.unpack("<H", uc.mem_read(child + 0x13E, 2))[0],
                                      "pose": struct.unpack("<H", uc.mem_read(child + 0x140, 2))[0],
                                      "subframe": struct.unpack("<H", uc.mem_read(child + 0x142, 2))[0],
                                      "pose_count": struct.unpack("<H", uc.mem_read(child + 0x148, 2))[0],
                                      "hit_box_count": uc.mem_read(child + 0x1CB, 1)[0],
                                      "hurt_box_count": uc.mem_read(child + 0x1CC, 1)[0],
                                      "collision_type_190": struct.unpack("<I", uc.mem_read(child + 0x190, 4))[0],
                                      "reaction_priority_194": uc.mem_read(child + 0x194, 1)[0],
                                      "hitstop_196": struct.unpack("<H", uc.mem_read(child + 0x196, 2))[0],
                                      "position": [struct.unpack("<f", uc.mem_read(child + 0xEC, 4))[0],
                                                   struct.unpack("<f", uc.mem_read(child + 0xF0, 4))[0]],
                                      "velocity": [struct.unpack("<f", uc.mem_read(child + 0xF4, 4))[0],
                                                   struct.unpack("<f", uc.mem_read(child + 0xF8, 4))[0]],
                                      "alpha": uc.mem_read(child + 0x113, 1)[0],
                                      "active": struct.unpack("<I", uc.mem_read(child + 0x34C, 4))[0],
                                      "frame_data_pointer": hex(frame_ptr),
                                      "frame_damage": struct.unpack("<H", uc.mem_read(frame_ptr + 0x1C, 2))[0]
                                      if frame_valid else None,
                                      "trace_tail": [hex(pc) for pc in probe._code_trace[-18:]]}
                child_updates.append(row)
                return row
            children = [int(row["object"], 16) for row in factory_return_observations]
            for child_index, child in enumerate(children):
                child_updates = []
                try:
                    child_box_sync = probe._sync_box_data(child)
                except Exception as exc:
                    child_box_sync = {"error": f"{type(exc).__name__}: {exc}"}
                child_limit = 1
                for child_tick in range(1, child_limit + 1):
                    state = update_child(child_tick)
                    if state["error"] or state["eip_after"] != hex(STOP) or not state["active"]:
                        break
                child_observations.append({"factory_return": factory_return_observations[child_index],
                                           "box_sync": child_box_sync,
                                           "updates": child_updates,
                                           "stop_reason": ("object-inactive" if child_updates and
                                                           not child_updates[-1]["active"] else
                                                           "error" if child_updates and
                                                           (child_updates[-1]["error"] or
                                                            child_updates[-1]["eip_after"] != hex(STOP)) else
                                                           "64-tick-limit")})
            # Keep the latest spawned projectile in the legacy slot so the
            # existing 623C collision regression remains unchanged.
            child = children[-1]
            child_updates = next((row["updates"] for row in child_observations
                                  if row["factory_return"].get("object") == hex(child)), [])
            secondary_setter = None
            if child_updates:
                first_child_tick = child_updates[0]
            # Bind the factory-return object into the original object-pair
            # phase and compare it with a Remilia hurtbox built from local PAT.
            # This establishes a real geometry/HP oracle for action 821 while
            # keeping arena/input/round state explicitly controlled.
            remilia_pat_resource = read_pat(dat_dir / "th123c.dat",
                                             "data/character/remilia/remilia.pat")
            if remilia_pat_resource is not None and (action_id != 530 or resolve_child_pair):
                remilia_pat, remilia_pat_sha = remilia_pat_resource
                defender_sequences = action_sequence_metadata(remilia_pat, 602)
                defender_sequence = next((row for row in defender_sequences
                                          if int(row["sequence"]) == 0), None)
                if defender_sequence is not None:
                    defender = LIST + 0xA000
                    uc.mem_write(defender, bytes(0x1400))
                    defender_ctor_sp = STACK + 0xB800 - 8
                    # The constructor is thiscall (PlayerInfo* on the stack).
                    # Reuse the initialized PlayerInfo layout from the Suika
                    # fixture instead of invoking the base constructor with a
                    # missing argument, which leaves Player+0x72c invalid.
                    uc.mem_write(defender_ctor_sp, struct.pack("<II", STOP, PLAYER_INFO))
                    uc.reg_write(UC_X86_REG_ECX, defender)
                    uc.reg_write(UC_X86_REG_ESP, defender_ctor_sp)
                    uc.reg_write(UC_X86_REG_EIP, 0x0046B7F0)
                    defender_ctor_error = None
                    try:
                        uc.emu_start(0x0046B7F0, STOP, count=200000)
                    except Exception as exc:
                        defender_ctor_error = f"{type(exc).__name__}: {exc}"
                    uc.mem_write(defender, struct.pack("<I", 0x0085D284))
                    uc.mem_write(defender + 4, struct.pack("<I", 0x0085772C))
                    defender_map = PAT_MAP + 0x40000
                    defender_setter = initialize_original_action(
                        probe, defender, 602, defender_sequence["frames"], 0,
                        pat_base=defender_map)
                    defender_map_root = defender_map + 0x7000
                    defender_map_result = defender_map + 0x1000
                    probe._pat_lookup_results[defender_map_root] = defender_map_result
                    defender_owner = OWNER + 0xA000
                    defender_data = OWNER + 0xB000
                    uc.mem_write(defender_owner, bytes(0x800))
                    uc.mem_write(defender_data, bytes(0x800))
                    uc.mem_write(defender + 0x16C, struct.pack("<I", defender_data))
                    uc.mem_write(defender + 0x168, struct.pack("<I", defender_data))
                    uc.mem_write(defender + 0x170, struct.pack("<I", defender_data))
                    uc.mem_write(defender + 0x350, struct.pack("<b", 1))
                    uc.mem_write(defender + 0x104, struct.pack("<b", -1))
                    uc.mem_write(defender + 0xEC, struct.pack("<f", 420.0))
                    uc.mem_write(defender + 0xF0, struct.pack("<f", 180.0))
                    uc.mem_write(defender + 0x184, struct.pack("<H", 1000))
                    for addr, value in ((defender + 0x198, 1.0),
                                        (defender + 0x538, 1.0),
                                        (defender_data + 0x4B0, 1.0),
                                        (defender_data + 0x530, 1.0),
                                        (defender_data + 0x534, 1.0),
                                        (defender_data + 0x544, 1.0),
                                        (defender_data + 0x548, 1.0),
                                        (defender_data + 0x53C, 1.0),
                                        (defender_data + 0x54C, 1.0),
                                        (defender_data + 0x550, 1.0)):
                        uc.mem_write(addr, struct.pack("<f", value))
                    uc.mem_write(defender_data + 0x7C, struct.pack("<I", 1000))
                    pose_sp = STACK + 0xBC00 - 8
                    uc.mem_write(pose_sp, struct.pack("<II", STOP, 0))
                    uc.reg_write(UC_X86_REG_ECX, defender)
                    uc.reg_write(UC_X86_REG_ESP, pose_sp)
                    uc.reg_write(UC_X86_REG_EIP, 0x00464B50)
                    uc.emu_start(0x00464B50, STOP, count=100000)
                    defender_box_sync = probe._sync_box_data(defender)
                    # Standard player-vs-object lists used by 0x47ce20.
                    def singleton(root: int, node: int, obj: int) -> None:
                        uc.mem_write(root, struct.pack("<3I", node, node, 0))
                        uc.mem_write(node, struct.pack("<3I", root, root, obj))
                    attacker_root, attacker_node = OWNER + 0x2000, OWNER + 0x2100
                    defender_root, defender_node = OWNER + 0x2200, OWNER + 0x2300
                    empty_root_a, empty_root_b = OWNER + 0x2400, OWNER + 0x2500
                    singleton(attacker_root, attacker_node, child)
                    singleton(defender_root, defender_node, defender)
                    singleton(empty_root_a, empty_root_a, 0)
                    singleton(empty_root_b, empty_root_b, 0)
                    for offset, ptr in ((0x60, attacker_root), (0x54, defender_root),
                                        (0x48, empty_root_a), (0x6C, empty_root_b)):
                        uc.mem_write(LIST + offset, struct.pack("<I", ptr))
                    uc.mem_write(LIST + 0x0C, struct.pack("<I", PLAYER))
                    uc.mem_write(LIST + 0x18, struct.pack("<I", defender))
                    uc.mem_write(PLAYER + 0x350, struct.pack("<b", 0))
                    uc.mem_write(defender + 0x350, struct.pack("<b", 1))
                    uc.mem_write(PLAYER + 0x170, struct.pack("<I", defender))
                    uc.mem_write(defender + 0x170, struct.pack("<I", PLAYER))
                    uc.mem_write(child + 0x190, struct.pack("<I", 0))
                    uc.mem_write(child + 0x194, struct.pack("<b", 1))
                    uc.mem_write(defender + 0x1A1, b"\0")
                    # Measure authentic transformed geometry for both combatants, then feed
                    # that same coherent geometry into the manager phase.
                    saved_intercept = probe.intercept_box_transforms
                    # The isolated fixture lacks stage/camera globals for the
                    # original transform. Natural sweeps use the affine
                    # mapping verified against its output; pinned regressions
                    # continue executing the original transform code.
                    probe.intercept_box_transforms = not pin_attacker
                    collision_matrix: list[dict[str, object]] = []
                    overlap = None
                    actual_defender_box_sync: dict[str, object] = {}
                    try:
                        from tools.x86_remilia_412_spawn_probe import run_original_hit_hurt_pair
                        if pin_attacker:
                            uc.mem_write(defender + 0xEC, struct.pack("<f", defender_x))
                            uc.mem_write(defender + 0xF0, struct.pack("<f", defender_y))
                            actual_defender_box_sync = probe._sync_box_data(defender)
                            for dy in (-300.0, -250.0, -200.0, -150.0, -100.0, -50.0, 0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0):
                                uc.mem_write(child + 0xEC, struct.pack("<f", defender_x))
                                uc.mem_write(child + 0xF0, struct.pack("<f", defender_y + dy))
                                attacker_box_sync = probe._sync_box_data(child)
                                geometry = run_original_hit_hurt_pair(probe, child, defender)
                                collision_matrix.append({"center_offset_y": dy,
                                                         "contact": geometry["return_value"] != 0,
                                                         "attacker_hit_boxes": geometry["attacker_hit_boxes"],
                                                         "defender_hurt_boxes": geometry["defender_hurt_boxes"],
                                                         "attacker_boxes_world": attacker_box_sync["hit_boxes"],
                                                         "defender_boxes_world": actual_defender_box_sync["hurt_boxes"]})
                            uc.mem_write(child + 0xEC, struct.pack("<f", defender_x))
                            uc.mem_write(child + 0xF0, struct.pack("<f", defender_y))
                            hit_geometry = probe._sync_box_data(child)
                            actual_geometry = run_original_hit_hurt_pair(probe, child, defender)
                        else:
                            natural_x = struct.unpack("<f", uc.mem_read(child + 0xEC, 4))[0]
                            natural_y = struct.unpack("<f", uc.mem_read(child + 0xF0, 4))[0]
                            if contact_grid:
                                offsets = [(dx, dy) for dx in range(-100, 101, 20)
                                           for dy in range(-100, 101, 20)]
                            else:
                                offsets = [(defender_x - natural_x, defender_y - natural_y)]
                            for dx, dy in offsets:
                                target_x, target_y = natural_x + dx, natural_y + dy
                                uc.mem_write(defender + 0xEC, struct.pack("<f", target_x))
                                uc.mem_write(defender + 0xF0, struct.pack("<f", target_y))
                                actual_defender_box_sync = probe._sync_box_data(defender)
                                if not pin_attacker:
                                    apply_verified_world_box_transform(uc, defender)
                                attacker_box_sync = probe._sync_box_data(child)
                                if not pin_attacker:
                                    apply_verified_world_box_transform(uc, child)
                                geometry = run_original_hit_hurt_pair(probe, child, defender)
                                collision_matrix.append({"center_offset_x": dx,
                                                         "center_offset_y": dy,
                                                         "contact": geometry["return_value"] != 0,
                                                         "attacker_position": [natural_x, natural_y],
                                                         "defender_position": [target_x, target_y],
                                                         "attacker_hit_boxes": geometry["attacker_hit_boxes"],
                                                         "defender_hurt_boxes": geometry["defender_hurt_boxes"],
                                                         "attacker_boxes_world": attacker_box_sync["hit_boxes"],
                                                         "defender_boxes_world": actual_defender_box_sync["hurt_boxes"]})
                            uc.mem_write(defender + 0xEC, struct.pack("<f", defender_x))
                            uc.mem_write(defender + 0xF0, struct.pack("<f", defender_y))
                            actual_defender_box_sync = probe._sync_box_data(defender)
                            if not pin_attacker:
                                apply_verified_world_box_transform(uc, defender)
                            hit_geometry = probe._sync_box_data(child)
                            if not pin_attacker:
                                apply_verified_world_box_transform(uc, child)
                            actual_geometry = run_original_hit_hurt_pair(probe, child, defender)
                    except Exception as exc:
                        hit_geometry = {"error": f"{type(exc).__name__}: {exc}"}
                        actual_geometry = {"error": f"{type(exc).__name__}: {exc}"}
                    # Keep original transforms active and restore the object's
                    # actual spawn position before the full manager phase.
                    if pin_attacker:
                        uc.mem_write(child + 0xEC, struct.pack("<f", defender_x))
                        uc.mem_write(child + 0xF0, struct.pack("<f", defender_y))
                    actual_defender_box_sync = probe._sync_box_data(defender)
                    if not pin_attacker:
                        apply_verified_world_box_transform(uc, defender)
                    hit_geometry = probe._sync_box_data(child)
                    if not pin_attacker:
                        apply_verified_world_box_transform(uc, child)
                    overlap = run_original_hit_hurt_pair(probe, child, defender)
                    pair_error = None
                    hp_before = struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0]
                    hp_writes: list[dict[str, object]] = []
                    def watch_hp_write(machine, _access, address, size, value, _user) -> None:
                        if address < defender + 0x186 and address + size > defender + 0x184:
                            hp_writes.append({"address": hex(address), "size": size,
                                              "value": int(value),
                                              "eip": hex(machine.reg_read(UC_X86_REG_EIP))})
                    hp_hook = uc.hook_add(UC_HOOK_MEM_WRITE, watch_hp_write)
                    pair_sp = STACK + 0xBE00 - 4
                    uc.mem_write(pair_sp, struct.pack("<I", STOP))
                    uc.reg_write(UC_X86_REG_ESP, pair_sp)
                    uc.reg_write(UC_X86_REG_ECX, LIST)
                    uc.reg_write(UC_X86_REG_EIP, 0x0047CE20)
                    probe._trace_limit = 12000
                    probe._code_trace.clear()
                    probe._trace_active = True
                    try:
                        uc.emu_start(0x0047CE20, STOP, count=500000)
                        if uc.reg_read(UC_X86_REG_EIP) != STOP:
                            pair_error = f"returned at {uc.reg_read(UC_X86_REG_EIP):#x}"
                    except Exception as exc:
                        pair_error = f"{type(exc).__name__}: {exc}"
                    finally:
                        probe._trace_active = False
                        uc.hook_del(hp_hook)
                    child_pair_dispatch = {
                        "defender": {"action": 602, "sequence": 0,
                                     "pat_sha256": remilia_pat_sha,
                                     "constructor_error": defender_ctor_error,
                                     "setter": defender_setter,
                                     "box_sync": defender_box_sync,
                                     "position": [defender_x, defender_y],
                                     "hp_before": hp_before,
                                     "hp_after": struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0],
                                     "collision_type_after": struct.unpack("<I", uc.mem_read(defender + 0x190, 4))[0]},
                        "attacker": {"object": hex(child), "box_sync": hit_geometry,
                                     "transform_mode": "original 0x465e10 box synchronization; both combatants synchronized consistently",
                                     "position": [struct.unpack("<f", uc.mem_read(child + 0xEC, 4))[0],
                                                    struct.unpack("<f", uc.mem_read(child + 0xF0, 4))[0]], "frame_damage": 800},
                        "pair_phase": {"entry": "0x47ce20", "error": pair_error,
                                       "trace": [hex(pc) for pc in probe._code_trace[-160:]],
                                       "reached_projectile_filter": 0x0047CA70 in probe._code_trace,
                                       "reached_character_resolver": 0x0047C990 in probe._code_trace,
                                       "reached_hit_response": 0x0047B660 in probe._code_trace,
                                       "defender_hp_before": hp_before,
                                       "defender_hp_after": struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0],
                                       "defender_action_after": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
                                       "defender_collision_type_after": struct.unpack("<I", uc.mem_read(defender + 0x190, 4))[0],
                                       "defender_reaction_timer_194": uc.mem_read(defender + 0x194, 1)[0],
                                       "defender_hitstop_196": struct.unpack("<H", uc.mem_read(defender + 0x196, 2))[0],
                                       "projectile_collision_type_190": struct.unpack("<I", uc.mem_read(child + 0x190, 4))[0],
                                       "projectile_priority_1bc_after": uc.mem_read(child + 0x1BC, 1)[0],
                                       "defender_priority_1bc_after": uc.mem_read(defender + 0x1BC, 1)[0],
                                       "projectile_reaction_timer_194": uc.mem_read(child + 0x194, 1)[0],
                                       "hp_writes": hp_writes,
                                       "attacker_hit_boxes": uc.mem_read(child + 0x1CB, 1)[0],
                                       "defender_hurt_boxes": uc.mem_read(defender + 0x1CC, 1)[0],
                                       "projectile_priority_1bc": uc.mem_read(child + 0x1BC, 1)[0],
                                       "defender_priority_1bc": uc.mem_read(defender + 0x1BC, 1)[0],
                                       "projectile_collision_type_190_before": struct.unpack("<I", uc.mem_read(child + 0x190, 4))[0],
                                       "defender_collision_type_190_before": struct.unpack("<I", uc.mem_read(defender + 0x190, 4))[0]},
                        "effect_manager": {"global": "0x8985f0",
                                           "synthetic_service": hex(effect_create_stub),
                                           "requests": effect_requests},
                        "geometry": overlap,
                        "geometry_scope": "original 0x465e10 synchronization, 0x47a5b0, and 0x47ce20 execute with both objects synchronized in the same world-space mode",
                        "actual_geometry_at_spawn": actual_geometry,
                        "actual_defender_box_sync": actual_defender_box_sync,
                        "collision_matrix": collision_matrix,
                        "lists": {"attacker": hex(attacker_root),
                                  "defender": hex(defender_root),
                                  "empty_a": hex(empty_root_a), "empty_b": hex(empty_root_b)},
                    }
                    reaction_update: dict[str, object] | None = None
                    reaction_sequences = action_sequence_metadata(remilia_pat, 50)
                    if reaction_sequences and reaction_sequences[0]["sequence"] == 0:
                        uc.mem_map(PAT_MAP + 0x80000, 0x50000)
                        reaction_fixture_obj = LIST + 0xC000
                        uc.mem_write(reaction_fixture_obj, bytes(0x1400))
                        reaction_base = PAT_MAP + 0x70000
                        reaction_setter = initialize_original_action(
                            probe, reaction_fixture_obj, 50,
                            reaction_sequences[0]["frames"], 0,
                            pat_base=reaction_base)
                        reaction_map_root = reaction_base + 0x7000
                        defender_map_root = defender_map + 0x7000
                        probe._pat_lookup_action_results[(defender_map_root, 50)] = (
                            probe._pat_lookup_results[reaction_map_root])
                        reaction_before = {"action": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
                                           "sequence": struct.unpack("<H", uc.mem_read(defender + 0x13E, 2))[0],
                                           "pose": struct.unpack("<H", uc.mem_read(defender + 0x140, 2))[0],
                                           "timer_194": uc.mem_read(defender + 0x194, 1)[0],
                                           "collision_type_190": struct.unpack("<I", uc.mem_read(defender + 0x190, 4))[0]}
                        # First preserve the true missing-resource failure.
                        baseline_update = run_original_character_update(probe, defender)
                        # Player+0x72c is spellBgTextures (not the card hand).
                        # Model its native deque layout with seven sentinel
                        # handles so action 602's playSpellBackground(6,2)
                        # path can proceed to the actual reaction update.
                        spell_bg_fixture = install_spell_bg_texture_deque(uc, defender)
                        probe.host_termination = None
                        updates = []
                        for tick in range(1, 121):
                            update_state = update_remilia_to_common_exit(probe, defender)
                            update_state["tick"] = tick
                            updates.append(update_state)
                            if (not update_state["completed"] or
                                    update_state["action"] != 602):
                                break
                        reaction_update = {"pat_action": 50,
                                           "reaction_pat_sha256": remilia_pat_sha,
                                           "reaction_frame_count": len(reaction_sequences[0]["frames"]),
                                           "fixture_setter": reaction_setter,
                                           "baseline_update_without_spell_bg": baseline_update,
                                           "spell_bg_deque_fixture": spell_bg_fixture,
                                           "before": reaction_before,
                                           "updates": updates,
                                           "update": updates[-1],
                                           "after": {"action": struct.unpack("<H", uc.mem_read(defender + 0x13C, 2))[0],
                                                     "sequence": struct.unpack("<H", uc.mem_read(defender + 0x13E, 2))[0],
                                                     "pose": struct.unpack("<H", uc.mem_read(defender + 0x140, 2))[0],
                                                     "pose_count": struct.unpack("<H", uc.mem_read(defender + 0x148, 2))[0],
                                                     "timer_194": uc.mem_read(defender + 0x194, 1)[0],
                                                     "collision_type_190": struct.unpack("<I", uc.mem_read(defender + 0x190, 4))[0],
                                                     "spell_bg_id_742": uc.mem_read(defender + 0x742, 1)[0],
                                                     "spell_bg_timer_740": struct.unpack("<H", uc.mem_read(defender + 0x740, 2))[0],
                                                     "selected_spell_bg_texture": struct.unpack(
                                                         "<I", uc.mem_read(0x008985E0 + 0xD8 + 4, 4))[0]}}
                    child_pair_dispatch["defender_reaction_update"] = reaction_update
            secondary_updates: list[dict[str, object]] = []
            nested_child_observations: list[dict[str, object]] = []
            if action_id in (530, 531) and child_updates:
                child = children[-1]
                for child_tick in range(2, 65):
                    state = update_child(child_tick)
                    if state["error"] or state["eip_after"] != hex(STOP) or not state["active"]:
                        break
                for observation in child_observations:
                    ticks = observation["updates"]
                    observation["stop_reason"] = ("object-inactive" if ticks and not ticks[-1]["active"] else
                                                   "error" if ticks and (ticks[-1]["error"] or
                                                                         ticks[-1]["eip_after"] != hex(STOP)) else
                                                   "64-tick-limit")
                if action_id == 530:
                    primary_address = factory_return_observations[-1]["object"]
                    nested_children = [row for row in nested_factory_returns
                                       if row["object"] != primary_address]
                    for nested in nested_children:
                        child = int(nested["object"], 16)
                        nested_updates: list[dict[str, object]] = []
                        child_updates = nested_updates
                        for child_tick in range(1, 65):
                            state = update_child(child_tick)
                            if state["error"] or state["eip_after"] != hex(STOP) or not state["active"]:
                                break
                        nested_child_observations.append({"factory_return": nested,
                                                          "updates": nested_updates,
                                                          "stop_reason": ("object-inactive" if nested_updates and
                                                                          not nested_updates[-1]["active"] else
                                                                          "error" if nested_updates and
                                                                          (nested_updates[-1]["error"] or
                                                                           nested_updates[-1]["eip_after"] != hex(STOP)) else
                                                                          "64-tick-limit")})
                    child = children[-1]
                    child_updates = next((row["updates"] for row in child_observations
                                          if row["factory_return"].get("object") == hex(child)), [])
                wanted_secondary_sequence = 6 if action_id == 530 else 1
                secondary_setter = next((row for row in spawned
                                         if row["action"] == 821 and
                                         row["sequence"] == wanted_secondary_sequence), None)
                if secondary_setter is not None:
                    child = int(secondary_setter["object"], 16)
                    child_updates = secondary_updates
                    for child_tick in range(1, 65):
                        state = update_child(child_tick)
                        if state["error"] or state["eip_after"] != hex(STOP) or not state["active"]:
                            break
                    child = children[-1]
                    child_updates = next((row["updates"] for row in child_observations
                                          if row["factory_return"].get("object") == hex(child)), [])
            result["spawned_object"] = {"factory_return": factory_return_observations[-1],
                                        "setter_returns": spawned,
                                        "update_entry": hex(child_update_entry),
                                        "box_sync": child_box_sync,
                                        "updates": child_updates,
                                        "all_factory_children": child_observations,
                                        "nested_factory_children": nested_child_observations,
                                        "secondary_visual": {"setter_return": secondary_setter,
                                                              "updates": secondary_updates,
                                                              "stop_reason": ("object-inactive" if secondary_updates and
                                                                              not secondary_updates[-1]["active"] else
                                                                              "error" if secondary_updates and
                                                                              (secondary_updates[-1]["error"] or
                                                                               secondary_updates[-1]["eip_after"] != hex(STOP)) else
                                                                              "64-tick-limit")},
                                        "pair_dispatch": child_pair_dispatch,
                                        "error": child_updates[-1]["error"] if child_updates else None}
    return result


def install_spell_bg_texture_deque(uc, obj: int) -> dict[str, object]:
    """Install a valid seven-entry SokuLib Deque<int> for update-only tests.

    Entries are sentinel texture handles: this models Player::spellBgTextures
    container semantics, not texture loading or rendering.
    """
    table = OWNER + 0xD000
    blocks = (OWNER + 0xE000, OWNER + 0xE100)
    values = [0xC001 + index for index in range(7)]
    uc.mem_write(table, struct.pack("<8I", blocks[0], blocks[1], 0, 0, 0, 0, 0, 0))
    uc.mem_write(blocks[0], struct.pack("<4i", *values[:4]))
    uc.mem_write(blocks[1], struct.pack("<4i", *values[4:], 0))
    # Deque<int>: debug proxy, table pointer, block count, head offset, size.
    uc.mem_write(obj + 0x72C, struct.pack("<5I", 0, table, 8, 0, len(values)))
    return {"member": "Player+0x72c (spellBgTextures)",
            "layout_source": "local/SokuLib/src/Player.hpp + SokuLib/src/Deque.hpp",
            "block_count": 8, "head_offset": 0, "size": len(values),
            "texture_handles": [hex(value) for value in values],
            "synthetic_handles": True}


def update_remilia_to_common_exit(probe: Suwako808FactoryProbe, obj: int) -> dict[str, object]:
    """Execute one Remilia update up to its original common-exit block."""
    uc = probe.uc
    sp = STACK + 0xC000
    uc.mem_write(sp, struct.pack("<I", STOP))
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_EBX, 1)
    uc.reg_write(UC_X86_REG_EBP, 0)
    uc.reg_write(UC_X86_REG_EDI, 0)
    uc.reg_write(UC_X86_REG_ECX, obj)
    uc.reg_write(UC_X86_REG_ESI, obj)
    uc.reg_write(UC_X86_REG_EIP, REMILIA_UPDATE_ENTRY)
    probe._code_trace.clear()
    probe._trace_active = True
    error = None
    try:
        uc.emu_start(REMILIA_UPDATE_ENTRY, REMILIA_UPDATE_EXIT, count=150000)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}"
    finally:
        probe._trace_active = False
    return {"entry": hex(REMILIA_UPDATE_ENTRY), "common_exit": hex(REMILIA_UPDATE_EXIT),
            "error": error, "exit": hex(uc.reg_read(UC_X86_REG_EIP)),
            "completed": error is None and uc.reg_read(UC_X86_REG_EIP) in (REMILIA_UPDATE_EXIT, 0),
            "host_termination": probe.host_termination,
            "action": struct.unpack("<H", uc.mem_read(obj + 0x13C, 2))[0],
            "sequence": struct.unpack("<H", uc.mem_read(obj + 0x13E, 2))[0],
            "pose": struct.unpack("<H", uc.mem_read(obj + 0x140, 2))[0],
            "subframe": struct.unpack("<H", uc.mem_read(obj + 0x142, 2))[0],
            "pose_count": struct.unpack("<H", uc.mem_read(obj + 0x148, 2))[0],
            "timer_194": uc.mem_read(obj + 0x194, 1)[0],
            "spell_bg_id_742": uc.mem_read(obj + 0x742, 1)[0],
            "spell_bg_timer_740": struct.unpack("<H", uc.mem_read(obj + 0x740, 2))[0],
            "trace": [hex(pc) for pc in probe._code_trace[-300:]]}


def run(dat_dir: Path, actions: tuple[int, ...] = (521, 526, 531)) -> dict[str, object]:
    rows = [run_action(action_id, dat_dir, (821,) if action_id == 531 else ()) for action_id in actions]
    return {
        "reference_sha256": "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e",
        "actions": rows,
        "scope": "Original Suika constructor, action 531 update, createObject factory for 821, PAT box synchronizer, original coordinate transforms and object-pair phase execute with original DAT frames. The 821 projectile contacts Remilia neutral 602 at the factory spawn and applies 800 PAT damage (HP 1000→200) with reaction timer `+0x194=20` and hitstop `+0x196=0`. A synthetic effect-manager service substitutes presentation; original Remilia spellBgTextures are also absent, so a seven-entry deque of sentinel handles lets CPU update proceed. The original action 602 update advances through its eight PAT poses, requests spell background 6/timer 2, and selects action 0 at tick 50. Tick 51 cannot continue because action 0 PAT/resources are absent in the fixture. Positions, player/object lists, stage context and the effect service remain controlled; this is not natural input/replay, rendering, a complete round, or a Vita runtime change.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dat_dir", nargs="?", type=Path, default=ROOT / "original")
    parser.add_argument("--output", type=Path, default=Path("artifacts/x86-suika-action-setter.json"))
    args = parser.parse_args()
    report = run(args.dat_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Suika action setter cases={len(report['actions'])}; output={args.output}")


if __name__ == "__main__":
    main()


