#!/usr/bin/env python3
"""Capture the original Remilia 412 state-4 spawn callsite under Unicorn.

The callsite instructions and callback-table lookup execute from the pinned PE.
Entry into the state-4 basic block, player state, callback table, and external
object manager are controlled fixtures; this is not a natural fight trace.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "local/python-deps"))

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EIP,
    UC_X86_REG_ESP, UC_X86_REG_ESI, UC_X86_REG_EBP, UC_X86_REG_EDI, UC_X86_REG_EDX,
)
from tools.x86_remilia_412_box_sync_probe import effective_pat
from tools.x86_remilia_412_action_setter_probe import (
    ACTION_SETTER, ACTION_WRITE, RESET_SEQUENCE, INITIALIZE_ACTION,
    INITIALIZER_BODY, ZERO_MOTION, PAT_LOOKUP, MAP_RESULT, MAP_OBJECT,
    MAP_NODE, SEQUENCE_NODE, FRAME_DATA, SET_POSE_CAPTURE,
)
from tools.extract_pat_pose_metadata import action_sequence_metadata, read_pat
from tools.x86_suwako_808_factory_probe import LIST, OWNER, PAT_MAP, STACK, STOP, Suwako808FactoryProbe

MAIN_ACTION_COMPARE = 0x00587BAB
CREATE_OBJECT_WRAPPER = 0x0046EB30
CALLBACK_DISPATCH = 0x00401D50
HANDLER_EPILOGUE = 0x0058CDCC
COMMON_UPDATE_EXIT = 0x00599FB0
PLAYER = LIST + 0x8000
CALLBACKS = OWNER + 0x100


def initialize_action_412(probe: Suwako808FactoryProbe, dat_dir: Path) -> dict[str, object]:
    """Run the original setter/initializer chain and controlled PAT lookup."""
    _archive, _digest, frames = effective_pat(dat_dir)
    uc = probe.uc
    uc.mem_write(PLAYER, bytes(0x1000))
    uc.mem_write(OWNER, bytes(0x100))
    for address, size in ((MAP_RESULT, 0x100), (MAP_OBJECT, 0x100),
                          (MAP_NODE, 0x100), (SEQUENCE_NODE, 0x100),
                          (FRAME_DATA, len(frames) * 0xA8)):
        uc.mem_write(address, bytes(size))
    uc.mem_write(PLAYER, struct.pack("<I", OWNER))
    uc.mem_write(OWNER + 2 * 4, struct.pack("<I", ACTION_SETTER))
    uc.mem_write(OWNER + 4 * 4, struct.pack("<I", RESET_SEQUENCE))
    uc.mem_write(OWNER + 5 * 4, struct.pack("<I", 0x00464BF0))
    uc.mem_write(OWNER + 7 * 4, struct.pack("<I", 0x00464B50))
    uc.mem_write(OWNER + 8 * 4, struct.pack("<I", 0x00464B70))
    uc.mem_write(OWNER + 15 * 4, struct.pack("<I", INITIALIZE_ACTION))
    uc.mem_write(PLAYER + 0x160, struct.pack("<I", PAT_MAP + 0x7000))
    uc.mem_write(MAP_RESULT, struct.pack("<II", MAP_OBJECT, MAP_NODE))
    uc.mem_write(MAP_OBJECT + 4, struct.pack("<I", MAP_NODE + 0x100))
    uc.mem_write(MAP_NODE + 0x10, struct.pack("<I", SEQUENCE_NODE))
    uc.mem_write(SEQUENCE_NODE + 4,
                 struct.pack("<II", FRAME_DATA, FRAME_DATA + len(frames) * 0xA8))
    uc.mem_write(SEQUENCE_NODE + 0x14, b"\x00")
    for index, frame in enumerate(frames):
        uc.mem_write(FRAME_DATA + index * 0xA8 + 8, struct.pack("<H", int(frame["duration"])))
    uc.mem_write(SEQUENCE_NODE + 0x1C, struct.pack("<I", SEQUENCE_NODE))

    reached: list[str] = []
    def setup_hook(machine, address: int, _size: int, _user: object) -> None:
        if address in (ACTION_SETTER, ACTION_WRITE, RESET_SEQUENCE,
                       INITIALIZE_ACTION, INITIALIZER_BODY, ZERO_MOTION):
            reached.append(hex(address))
        esp = machine.reg_read(UC_X86_REG_ESP)
        if address == PAT_LOOKUP:
            ret = u32(machine, esp)
            machine.reg_write(UC_X86_REG_EAX, MAP_RESULT)
            machine.reg_write(UC_X86_REG_ESP, esp + 12)
            machine.reg_write(UC_X86_REG_EIP, ret)

    uc.hook_add(UC_HOOK_CODE, setup_hook)
    sp = STACK + 0xB000
    uc.mem_write(sp, struct.pack("<II", STOP, 412))
    uc.reg_write(UC_X86_REG_ECX, PLAYER)
    uc.reg_write(UC_X86_REG_ESI, PLAYER)
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_EIP, ACTION_SETTER)
    uc.emu_start(ACTION_SETTER, STOP, count=100000)
    state = {
        "action": struct.unpack("<H", uc.mem_read(PLAYER + 0x13C, 2))[0],
        "sequence": struct.unpack("<H", uc.mem_read(PLAYER + 0x13E, 2))[0],
        "pose": struct.unpack("<H", uc.mem_read(PLAYER + 0x140, 2))[0],
        "pose_count": struct.unpack("<H", uc.mem_read(PLAYER + 0x148, 2))[0],
        "initializer_chain": reached,
    }
    if (state["action"], state["sequence"], state["pose"], state["pose_count"]) != (412, 0, 0, len(frames)):
        raise AssertionError(f"original action setter did not initialize 412/seq0: {state}")

    return state


def u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def initialize_object_manager(probe: Suwako808FactoryProbe) -> dict[str, object]:
    uc = probe.uc
    sp = STACK + 0x5000 - 4
    uc.mem_write(sp, struct.pack("<I", STOP))
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_EIP, 0x00824BFA)
    uc.emu_start(0x00824BFA, STOP, count=100000)
    if uc.reg_read(UC_X86_REG_EIP) != STOP:
        raise RuntimeError(f"CRT init did not return: {uc.reg_read(UC_X86_REG_EIP):#x}")
    sp = STACK + 0x7000 - 4
    uc.mem_write(sp, struct.pack("<I", STOP))
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_ECX, LIST)
    uc.reg_write(UC_X86_REG_EIP, 0x00783D70)
    uc.emu_start(0x00783D70, STOP, count=100000)
    if uc.reg_read(UC_X86_REG_EIP) != STOP:
        raise RuntimeError(f"object manager ctor did not return: {uc.reg_read(UC_X86_REG_EIP):#x}")
    return {"crt": "0x824bfa", "manager_constructor": "0x783d70", "completed": True}


def run_case(dat_dir: Path, x: float, y: float, facing: int, callback_index: int,
             real_factory: bool = False, resolve_damage: bool = False) -> dict[str, object]:
    probe = Suwako808FactoryProbe(ROOT / "original/th123.exe", dat_dir,
                                  character="remilia", action_id=801)
    uc = probe.uc
    manager_state = initialize_object_manager(probe) if real_factory else None
    initialized_action = initialize_action_412(probe, dat_dir)
    if real_factory:
        # The original manager's vtable slot +4 points outside the pinned PE
        # in this isolated image. Route that interface slot to the game's own
        # 0x784020 factory while preserving its actual list/handle state.
        manager_vtable = OWNER + 0x800
        uc.mem_write(manager_vtable, bytes(0x20))
        uc.mem_write(manager_vtable + 4, struct.pack("<I", 0x00784020))
        uc.mem_write(LIST - 4, struct.pack("<I", manager_vtable))
        uc.mem_write(PLAYER + 0x130, struct.pack("<I", OWNER))
        uc.mem_write(PLAYER + 0x170, struct.pack("<I", PLAYER))
        uc.mem_write(PLAYER + 0x6F8, struct.pack("<I", LIST - 4))
        uc.mem_write(OWNER + 0x130, struct.pack("<I", OWNER))
        uc.mem_write(OWNER + 0x160, struct.pack("<I", PAT_MAP))
        uc.mem_write(LIST + 0x60, struct.pack("<I", PLAYER))
    uc.mem_write(CALLBACKS, bytes(0x500))
    uc.mem_write(PLAYER + 0x164, struct.pack("<I", CALLBACKS))
    # The original vtable pose-advance method has already reached pose 4.
    uc.mem_write(PLAYER + 0x142, struct.pack("<H", 0))
    uc.mem_write(PLAYER + 0x104, struct.pack("<b", facing))
    uc.mem_write(PLAYER + 0xEC, struct.pack("<f", x))
    uc.mem_write(PLAYER + 0xF0, struct.pack("<f", y))
    uc.mem_write(PLAYER + 0x49E, struct.pack("<H", 1000))
    uc.mem_write(PLAYER + 0x4C8, struct.pack("<I", 0))
    uc.mem_write(PLAYER + 0x54C, struct.pack("<f", 1.0))
    uc.mem_write(PLAYER + 0x5E4, struct.pack("<H", 0))
    uc.mem_write(CALLBACKS + callback_index * 4, struct.pack("<I", 0x12345678))

    # State-4 block has a 0x288-byte local frame. We stop at its epilogue so
    # the harness need not invent the parent dispatcher's saved-register frame.
    entry_sp = STACK + 0xC000
    spawn: dict[str, object] = {}
    callback: dict[str, object] = {}
    errors: list[str] = []
    original_helpers: list[str] = []
    dispatch_trace: list[str] = []
    execution_tail: list[str] = []
    tick_states: list[dict[str, int]] = []
    child_factory: dict[str, object] = {}
    child_box_sync: dict[str, object] | None = None
    child_updates: list[dict[str, object]] = []
    child_update_error: str | None = None
    manager_tick: dict[str, object] | None = None
    manager_node_visits: list[dict[str, str]] = []
    factory_calls: list[dict[str, str]] = []
    factory_returns: list[dict[str, str]] = []
    create_object_helper_calls: list[dict[str, object]] = []

    def hook(machine, address: int, _size: int, _user: object) -> None:
        esp = machine.reg_read(UC_X86_REG_ESP)
        execution_tail.append(hex(address))
        if len(execution_tail) > 80:
            del execution_tail[:-80]
        if address in (MAIN_ACTION_COMPARE, 0x0058A3A1, 0x0058CCE7):
            dispatch_trace.append(hex(address))
        if address in (0x0047A9E0, 0x00487870, 0x00820230, 0x00438C60):
            original_helpers.append(hex(address))
        if real_factory and address == 0x00633C50:
            node = machine.reg_read(UC_X86_REG_ESI)
            obj = u32(machine, node + 8)
            object_details = {"vtable": hex(u32(machine, obj))} if obj > 0x1000 else {}
            if obj > 0x1000:
                object_details["action"] = str(struct.unpack("<H", machine.mem_read(obj + 0x13C, 2))[0])
            manager_node_visits.append({
                "node": hex(node), "next": hex(u32(machine, node)),
                "previous": hex(u32(machine, node + 4)),
                "object": hex(obj), **object_details,
            })
        if real_factory and address == 0x00784020:
            esp_factory = machine.reg_read(UC_X86_REG_ESP)
            factory_calls.append({"action": hex(u32(machine, esp_factory + 12)),
                                  "owner": hex(u32(machine, esp_factory + 8)),
                                  "return": hex(u32(machine, esp_factory))})
        if real_factory and address == 0x0059B70A:
            result_ptr = machine.reg_read(UC_X86_REG_EAX)
            factory_returns.append({"pointer": hex(result_ptr),
                                    "action": str(struct.unpack("<H", machine.mem_read(result_ptr + 0x13C, 2))[0])
                                    if result_ptr > 0x1000 else "invalid",
                                    "mode_190": str(u32(machine, result_ptr + 0x190))
                                    if result_ptr > 0x1000 else "invalid",
                                    "field_34c": str(u32(machine, result_ptr + 0x34C))
                                    if result_ptr > 0x1000 else "invalid"})
        if real_factory and address == 0x0059B6C0:
            helper_this = machine.reg_read(UC_X86_REG_ECX)
            helper_sp = machine.reg_read(UC_X86_REG_ESP)
            create_object_helper_calls.append({
                "return_address": hex(u32(machine, helper_sp)),
                "this": hex(helper_this),
                "this_action": struct.unpack("<H", machine.mem_read(helper_this + 0x13C, 2))[0]
                if helper_this > 0x1000 else None,
                "this_pose": struct.unpack("<H", machine.mem_read(helper_this + 0x140, 2))[0]
                if helper_this > 0x1000 else None,
                "this_mode_190": u32(machine, helper_this + 0x190)
                if helper_this > 0x1000 else None,
                "stack_arguments": [hex(u32(machine, helper_sp + offset))
                                    for offset in (4, 8, 12, 16, 20, 24, 28)],
            })
        if address == 0x00487CA0:
            ret = u32(machine, esp)
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
        if address == CREATE_OBJECT_WRAPPER:
            words = struct.unpack("<8I", machine.mem_read(esp, 32))
            ptr = words[6]
            spawn.update({
                "return_address": hex(words[0]),
                "arguments_raw": [hex(v) for v in words[1:]],
                "object_id": words[1],
                "x": struct.unpack("<f", struct.pack("<I", words[2]))[0],
                "y": struct.unpack("<f", struct.pack("<I", words[3]))[0],
                "facing": words[4],
                "callback_index_argument": words[5],
                "temporary_float_block": list(struct.unpack("<3f", machine.mem_read(ptr, 12))),
                "temporary_float_count": words[7],
            })
            if real_factory:
                # The parent action has reached its spawn frame; prepare the
                # child's real PAT lookup and let 0x46eb30 call the manager.
                machine.mem_write(PLAYER + 0x160, struct.pack("<I", PAT_MAP))
                probe._prepare_pat()
            else:
                machine.reg_write(UC_X86_REG_EAX, 0x0BADF00D)
                machine.reg_write(UC_X86_REG_ESP, esp + 32)
                machine.reg_write(UC_X86_REG_EIP, words[0])
        elif address == 0x0058CDC4 and real_factory:
            child = machine.reg_read(UC_X86_REG_EAX)
            if child:
                child_factory.update({
                    "pointer": hex(child),
                    "action": struct.unpack("<H", machine.mem_read(child + 0x13C, 2))[0],
                    "sequence": struct.unpack("<H", machine.mem_read(child + 0x13E, 2))[0],
                    "pose": struct.unpack("<H", machine.mem_read(child + 0x140, 2))[0],
                    "pose_count": struct.unpack("<H", machine.mem_read(child + 0x148, 2))[0],
                    "position": [struct.unpack("<f", machine.mem_read(child + 0xEC, 4))[0],
                                 struct.unpack("<f", machine.mem_read(child + 0xF0, 4))[0]],
                    "lifetime_field_34c": u32(machine, child + 0x34C),
                })
        elif address == CALLBACK_DISPATCH:
            callback_pointer = u32(machine, esp + 4)
            callback.update({
                "dispatcher": hex(address),
                "index": machine.reg_read(UC_X86_REG_EBX),
                "table_pointer": hex(u32(machine, PLAYER + 0x164)),
                "selected_function_pointer": hex(callback_pointer),
                "action": struct.unpack("<H", machine.mem_read(PLAYER + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", machine.mem_read(PLAYER + 0x13E, 2))[0],
                "substate": struct.unpack("<H", machine.mem_read(PLAYER + 0x140, 2))[0],
            })
            ret = u32(machine, esp)
            machine.reg_write(UC_X86_REG_ESP, esp + 8)  # callback dispatch ret 4
            machine.reg_write(UC_X86_REG_EAX, 0)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address in (HANDLER_EPILOGUE, COMMON_UPDATE_EXIT):
            tick_states.append({
                "pose": struct.unpack("<H", machine.mem_read(PLAYER + 0x140, 2))[0],
                "subframe": struct.unpack("<H", machine.mem_read(PLAYER + 0x142, 2))[0],
                "duration": struct.unpack("<H", machine.mem_read(PLAYER + 0x14C, 2))[0],
                "sequence": struct.unpack("<H", machine.mem_read(PLAYER + 0x13E, 2))[0],
            })
            machine.emu_stop()

    uc.hook_add(UC_HOOK_CODE, hook)
    for tick in range(120):
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EBX, 1)  # value loaded by 0x5879cf in the skipped prologue
        uc.reg_write(UC_X86_REG_EBP, 0)
        uc.reg_write(UC_X86_REG_EDI, 0)
        uc.reg_write(UC_X86_REG_ECX, PLAYER)
        uc.reg_write(UC_X86_REG_ESI, PLAYER)
        uc.reg_write(UC_X86_REG_EIP, MAIN_ACTION_COMPARE)
        try:
            uc.emu_start(MAIN_ACTION_COMPARE, STOP, count=10000)
        except Exception as exc:
            errors.append(f"tick {tick + 1}: {type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}; eax={uc.reg_read(UC_X86_REG_EAX):#x} ecx={uc.reg_read(UC_X86_REG_ECX):#x} edx={uc.reg_read(UC_X86_REG_EDX):#x} esi={uc.reg_read(UC_X86_REG_ESI):#x} esp={uc.reg_read(UC_X86_REG_ESP):#x}; trace={execution_tail[-20:]}")
            break
        if spawn:
            break
        if uc.reg_read(UC_X86_REG_EIP) not in (HANDLER_EPILOGUE, COMMON_UPDATE_EXIT):
            errors.append(f"tick {tick + 1}: handler did not reach epilogue: {uc.reg_read(UC_X86_REG_EIP):#x}")
            break
    if not spawn:
        raise RuntimeError(f"original handler block did not request object 801: {errors}")
    if not callback:
        raise RuntimeError(f"original indexed callback did not dispatch: {errors}")
    collision_matrix: list[dict[str, object]] = []
    damage_response: dict[str, object] | None = None
    pair_dispatch: dict[str, object] | None = None
    if real_factory and child_factory:
        child = int(child_factory["pointer"], 16)
        try:
            child_box_sync = probe._sync_box_data(child)
        except Exception as exc:
            child_update_error = f"box sync: {type(exc).__name__}: {exc}"
        # Exercise the reference hit-vs-hurt helper with the factory-created
        # projectile and defender boxes extracted from Remilia's neutral PAT.
        # Pair resolution and damage response remain outside this probe.
        sequences = probe.pat_fixture["sequences"]
        attack_frame = sequences[0]["frames"][0]
        neutral_frame = next(
            frame for frame in action_sequence_metadata(
                read_pat(dat_dir / probe.pat_fixture["archive"],
                         "data/character/remilia/remilia.pat")[0], 0)[0]["frames"]
            if frame["hurt_boxes"]
        )
        defender = LIST + 0x8800
        uc.mem_write(defender, bytes(0x1400))
        character_ctor_sp = STACK + 0x7000 - 4
        uc.mem_write(character_ctor_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESP, character_ctor_sp)
        uc.reg_write(UC_X86_REG_ECX, defender)
        uc.reg_write(UC_X86_REG_EIP, 0x0046B7F0)
        probe._code_trace.clear()
        probe._trace_active = True
        try:
            uc.emu_start(0x0046B7F0, STOP, count=500000)
        except Exception as exc:
            raise RuntimeError(
                f"original character constructor fault at {uc.reg_read(UC_X86_REG_EIP):#x}: {exc}; "
                f"trace={[hex(pc) for pc in probe._code_trace[-20:]]}") from exc
        finally:
            probe._trace_active = False
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"original character base constructor returned at {uc.reg_read(UC_X86_REG_EIP):#x}; trace={[hex(pc) for pc in probe._code_trace[-24:]]}")
        defender_constructor = {
            "function": "0x46b7f0",
            "field_1ac_after_constructor": uc.mem_read(defender + 0x1AC, 1)[0],
        }
        neutral_descriptor = PAT_MAP + 0x60000
        neutral_collision = PAT_MAP + 0x61000
        neutral_hurt = PAT_MAP + 0x62000
        uc.mem_write(neutral_descriptor, bytes(0xA8))
        uc.mem_write(defender + 0x158, struct.pack("<I", neutral_descriptor))
        if neutral_frame["collision_boxes"]:
            uc.mem_write(neutral_collision,
                         struct.pack("<4i", *neutral_frame["collision_boxes"][0]))
            uc.mem_write(neutral_descriptor + 0x54,
                         struct.pack("<I", neutral_collision))
        hurt = neutral_frame["hurt_boxes"]
        hurt_start = neutral_hurt
        hurt_end = hurt_start + len(hurt) * 16
        uc.mem_write(neutral_descriptor + 0x58,
                     struct.pack("<4I", 0, hurt_start, hurt_end, hurt_end))
        if hurt:
            uc.mem_write(hurt_start, b"".join(struct.pack("<4i", *box) for box in hurt))
        for offset, key in ((0x4C, "frame_flags"), (0x50, "attack_flags")):
            uc.mem_write(neutral_descriptor + offset,
                         struct.pack("<I", int(neutral_frame.get(key, 0))))
        uc.mem_write(defender + 0xEC, struct.pack("<f", 403.0))
        uc.mem_write(defender + 0xF0, struct.pack("<f", 360.0))
        probe._sync_box_data(defender)
        saved_intercept = probe.intercept_box_transforms
        try:
            probe.intercept_box_transforms = False
            for dx in (0.0, 40.0, 60.0, 70.0, 71.0, 100.0, 200.0):
                uc.mem_write(child + 0xEC, struct.pack("<f", 403.0 - dx))
                uc.mem_write(child + 0xF0, struct.pack("<f", 360.0))
                probe._sync_box_data(child)
                transform_start = len(probe.box_transform_calls)
                collision = run_original_hit_hurt_pair(probe, child, defender)
                collision_matrix.append({"center_distance_x": dx,
                                         "attacker_hit_boxes": collision["attacker_hit_boxes"],
                                         "defender_hurt_boxes": collision["defender_hurt_boxes"],
                                         "contact": collision["return_value"] != 0,
                                         "transform_helpers": probe.box_transform_calls[transform_start:]})
        finally:
            probe.intercept_box_transforms = saved_intercept
        if resolve_damage:
            # Build the original character-pair manager's two-player and
            # team-indexed intrusive-list layout, then enter its PE dispatcher.
            pair_dispatch = {}
            uc.mem_write(child + 0xEC, struct.pack("<f", 403.0))
            uc.mem_write(child + 0xF0, struct.pack("<f", 360.0))
            probe._sync_box_data(child)
            uc.mem_write(PLAYER + 0x350, struct.pack("<b", 0))
            uc.mem_write(defender + 0x350, struct.pack("<b", 1))
            uc.mem_write(PLAYER + 0x170, struct.pack("<I", defender))
            uc.mem_write(defender + 0x170, struct.pack("<I", PLAYER))
            uc.mem_write(LIST + 0x0C, struct.pack("<I", PLAYER))
            uc.mem_write(LIST + 0x18, struct.pack("<I", defender))

            def make_singleton_list(root: int, node: int, obj: int) -> None:
                uc.mem_write(root, struct.pack("<3I", node, node, 0))
                uc.mem_write(node, struct.pack("<3I", root, root, obj))

            attacker_root, attacker_node = OWNER + 0x2000, OWNER + 0x2100
            target_root, target_node = OWNER + 0x2200, OWNER + 0x2300
            empty_a, empty_b = OWNER + 0x2400, OWNER + 0x2500
            make_singleton_list(attacker_root, attacker_node, child)
            make_singleton_list(target_root, target_node, defender)
            make_singleton_list(empty_a, empty_a, 0)
            make_singleton_list(empty_b, empty_b, 0)
            uc.mem_write(LIST + 0x60, struct.pack("<I", attacker_root))
            uc.mem_write(LIST + 0x54, struct.pack("<I", target_root))
            uc.mem_write(LIST + 0x48, struct.pack("<I", empty_a))
            uc.mem_write(LIST + 0x6C, struct.pack("<I", empty_b))
            uc.mem_write(child + 0x190, struct.pack("<I", 0))
            uc.mem_write(child + 0x194, struct.pack("<b", 1))
            uc.mem_write(defender + 0x1A1, struct.pack("<B", 0))
            uc.mem_write(defender + 0x184, struct.pack("<H", 1000))
            pair_hp_before = struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0]
            pair_sp = STACK + 0xB000 - 4
            uc.mem_write(pair_sp, struct.pack("<I", STOP))
            uc.reg_write(UC_X86_REG_ESP, pair_sp)
            uc.reg_write(UC_X86_REG_ECX, LIST)
            uc.reg_write(UC_X86_REG_EIP, 0x0047CE20)
            probe._code_trace.clear()
            probe._trace_active = True
            pair_error = None
            try:
                uc.emu_start(0x0047CE20, STOP, count=500000)
                if uc.reg_read(UC_X86_REG_EIP) != STOP:
                    pair_error = f"pair phase returned at {uc.reg_read(UC_X86_REG_EIP):#x}"
            except Exception as exc:
                pair_error = f"{type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}"
            finally:
                probe._trace_active = False
            pair_dispatch = {
                "function": "0x47ce20", "error": pair_error,
                "trace": [hex(pc) for pc in probe._code_trace[-80:]],
                "reached_projectile_filter": "0x47ca70" in [hex(pc) for pc in probe._code_trace],
                "reached_character_resolver": "0x47c990" in [hex(pc) for pc in probe._code_trace],
                "defender_hp_before": pair_hp_before,
                "defender_hp_after": struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0],
                "attacker_flags": hex(struct.unpack("<I", uc.mem_read(
                    u32(uc, child + 0x1C0) + 0x50, 4))[0]),
                "attacker_frame_flags": hex(struct.unpack("<I", uc.mem_read(
                    u32(uc, child + 0x1C0) + 0x4C, 4))[0]),
                "defender_flags": hex(struct.unpack("<I", uc.mem_read(
                    u32(uc, defender + 0x1C0) + 0x50, 4))[0]),
                "defender_frame_flags": hex(struct.unpack("<I", uc.mem_read(
                    u32(uc, defender + 0x1C0) + 0x4C, 4))[0]),
                "defender_field_1ac_after_original_constructor": defender_constructor["field_1ac_after_constructor"],
            }
            # Differentially open only the descriptor flag gate observed at
            # 0x47c990. object+0x1ac already came from the original character ctor.
            if not pair_error and pair_dispatch["defender_hp_after"] == pair_hp_before:
                original_frame_flags = struct.unpack(
                    "<I", uc.mem_read(neutral_descriptor + 0x4C, 4))[0]
                uc.mem_write(neutral_descriptor + 0x4C,
                             struct.pack("<I", original_frame_flags | 0x40))
                uc.mem_write(defender + 0x184, struct.pack("<H", pair_hp_before))
                uc.mem_write(pair_sp, struct.pack("<I", STOP))
                uc.reg_write(UC_X86_REG_ESP, pair_sp)
                uc.reg_write(UC_X86_REG_ECX, LIST)
                uc.reg_write(UC_X86_REG_EIP, 0x0047CE20)
                probe._code_trace.clear()
                probe._trace_active = True
                gate_error = None
                try:
                    uc.emu_start(0x0047CE20, STOP, count=500000)
                    if uc.reg_read(UC_X86_REG_EIP) != STOP:
                        gate_error = f"pair phase returned at {uc.reg_read(UC_X86_REG_EIP):#x}"
                except Exception as exc:
                    gate_error = f"{type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}"
                finally:
                    probe._trace_active = False
                gate_trace = [hex(pc) for pc in probe._code_trace[-80:]]
                gate_calls = [hex(pc) for pc in probe._code_trace
                              if pc in (0x47CA70, 0x47C990, 0x47B660, 0x47A5B0)]
                post_pair_geometry = run_original_hit_hurt_pair(probe, child, defender)
                gate_hp_after = struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0]
                pair_dispatch["gate_open_trial"] = {
                    "synthetic": True, "changed_frame_flags": "OR 0x40",
                    "object_field_1ac_from_original_constructor": defender_constructor["field_1ac_after_constructor"],
                    "error": gate_error,
                    "reached_hit_response": "0x47b660" in gate_calls,
                    "reached_geometry": "0x47a5b0" in gate_calls,
                    "call_sites": gate_calls,
                    "geometry_after_dispatch": post_pair_geometry,
                    "defender_hp_before": pair_hp_before,
                    "defender_hp_after": gate_hp_after,
                    "trace": gate_trace,
                }
                if gate_hp_after < pair_hp_before or gate_error:
                    damage_response = {
                        "function": "pair-dispatch-gate-open", "pat_damage": 120,
                        "defender_hp_before": pair_hp_before,
                        "defender_hp_after": gate_hp_after,
                        "damage_applied": gate_hp_after < pair_hp_before,
                        "attacker_frame_damage_field": struct.unpack("<H", uc.mem_read(
                            u32(uc, child + 0x1C0) + 0x1C, 2))[0],
                        "attacker_frame_flags": hex(struct.unpack("<I", uc.mem_read(
                            u32(uc, child + 0x1C0) + 0x4C, 4))[0]),
                        "attacker_attack_flags": hex(struct.unpack("<I", uc.mem_read(
                            u32(uc, child + 0x1C0) + 0x50, 4))[0]),
                        "attacker_hitbox_count": uc.mem_read(child + 0x1CB, 1)[0],
                        "defender_hurtbox_count": uc.mem_read(defender + 0x1CC, 1)[0],
                        "attacker_cooldown_190": u32(uc, child + 0x190),
                        "error": gate_error,
                        "failure_after_damage": bool(gate_error and gate_hp_after < pair_hp_before),
                        "external_callback_pointer": "0x0" if gate_error and "0x0" in gate_error else None,
                        "trace": gate_trace,
                    }
                    if gate_hp_after < pair_hp_before:
                        resolve_damage = False
            if pair_error or pair_dispatch["defender_hp_after"] < pair_hp_before:
                damage_response = {
                    "function": "pair-dispatch", "pat_damage": 120,
                    "defender_hp_before": pair_hp_before,
                    "defender_hp_after": pair_dispatch["defender_hp_after"],
                    "damage_applied": pair_dispatch["defender_hp_after"] < pair_hp_before,
                    "error": pair_error,
                    "failure_after_damage": bool(pair_error and
                        pair_dispatch["defender_hp_after"] < pair_hp_before),
                    "external_callback_pointer": "0x0" if uc.reg_read(UC_X86_REG_EIP) == 0 else None,
                    "trace": pair_dispatch["trace"],
                }
                # If pair dispatch actually applies the contact, retain its
                # proof and skip the standalone response below.
                resolve_damage = False
        if resolve_damage:
            # Reach the original hit-response function after a verified PAT box overlap.
            # Its presentation callback is outside this harness; keep this opt-in.
            # Damage and cooldown execute from the PE; presentation service is absent.
            uc.mem_write(child + 0xEC, struct.pack("<f", 403.0))
            uc.mem_write(child + 0xF0, struct.pack("<f", 360.0))
            probe._sync_box_data(child)
            uc.mem_write(defender + 0x184, struct.pack("<H", 1000))
            hp_before = struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0]
            response_sp = STACK + 0xB000 - 12
            uc.mem_write(response_sp, struct.pack("<3I", STOP, child, defender))
            uc.reg_write(UC_X86_REG_ESP, response_sp)
            uc.reg_write(UC_X86_REG_ECX, LIST)
            uc.reg_write(UC_X86_REG_EIP, 0x0047B660)
            probe._code_trace.clear()
            probe._trace_active = True
            response_error = None
            try:
                uc.emu_start(0x0047B660, STOP, count=250000)
                if uc.reg_read(UC_X86_REG_EIP) != STOP:
                    response_error = f"response returned at {uc.reg_read(UC_X86_REG_EIP):#x}"
            except Exception as exc:
                response_error = f"{type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}"
            finally:
                probe._trace_active = False
            damage_response = {
                "function": "0x47b660", "attacker": hex(child), "defender": hex(defender),
                "pat_damage": int(probe.pat_fixture["sequences"][0]["frames"][0]["damage"]),
                "attacker_frame_damage_field": struct.unpack("<H", uc.mem_read(
                    u32(uc, child + 0x1C0) + 0x1C, 2))[0],
                "attacker_frame_flags": hex(struct.unpack("<I", uc.mem_read(
                    u32(uc, child + 0x1C0) + 0x4C, 4))[0]),
                "attacker_attack_flags": hex(struct.unpack("<I", uc.mem_read(
                    u32(uc, child + 0x1C0) + 0x50, 4))[0]),
                "attacker_hitbox_count": uc.mem_read(child + 0x1CB, 1)[0],
                "defender_hurtbox_count": uc.mem_read(defender + 0x1CC, 1)[0],
                "defender_hp_before": hp_before,
                "defender_hp_after": struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0],
                "damage_applied": struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0]
                == hp_before - int(probe.pat_fixture["sequences"][0]["frames"][0]["damage"]),
                "attacker_hit_priority_1bc": uc.mem_read(child + 0x1BC, 1)[0],
                "defender_reaction_194": uc.mem_read(defender + 0x194, 1)[0],
                "attacker_cooldown_190": u32(uc, child + 0x190),
                "error": response_error,
                "failure_after_damage": bool(response_error and
                    struct.unpack("<H", uc.mem_read(defender + 0x184, 2))[0] < hp_before),
                "external_callback_pointer": "0x0" if uc.reg_read(UC_X86_REG_EIP) == 0 else None,
                "trace": [hex(pc) for pc in probe._code_trace[-35:]],
            }
        # The factory inserts the child into the real list. Advance only via
        # the manager's virtual slot so its callback and removal gate remain in
        # the execution path throughout the lifecycle sample.
        manager_vtable = OWNER + 0x800
        # The secondary manager interface at LIST-4 dispatches factory in
        # slot 1 and update in slot 4; both methods adjust `this` by +4.
        uc.mem_write(manager_vtable + 0x10, struct.pack("<I", 0x00633CE0))
        manager_update_stub = STOP + 0x500
        uc.mem_write(manager_update_stub, b"\x8b\x01\xff\x50\x10\xc3")
        manager_ticks: list[dict[str, object]] = []
        for tick in range(120):
            if u32(uc, child + 0x34C) == 0:
                break
            manager_sp = STACK + 0x9800 - 4
            uc.mem_write(manager_sp, struct.pack("<I", STOP))
            uc.reg_write(UC_X86_REG_ESP, manager_sp)
            uc.reg_write(UC_X86_REG_ECX, LIST - 4)
            uc.reg_write(UC_X86_REG_EIP, manager_update_stub)
            probe._code_trace.clear()
            probe._trace_active = True
            try:
                uc.emu_start(manager_update_stub, STOP, count=500000)
                completed = uc.reg_read(UC_X86_REG_EIP) == STOP
                state = {"tick": tick + 1, "completed": completed,
                         "field_34c": u32(uc, child + 0x34C),
                         "action": struct.unpack("<H", uc.mem_read(child + 0x13C, 2))[0],
                         "pose": struct.unpack("<H", uc.mem_read(child + 0x140, 2))[0],
                         "trace": [hex(pc) for pc in probe._code_trace[-12:]]}
                manager_ticks.append(state)
                child_updates.append({"tick": tick + 1,
                                      "action": state["action"],
                                      "sequence": struct.unpack("<H", uc.mem_read(child + 0x13E, 2))[0],
                                      "pose": state["pose"],
                                      "subframe": struct.unpack("<H", uc.mem_read(child + 0x142, 2))[0],
                                      "field_34c": state["field_34c"],
                                      "position": [struct.unpack("<f", uc.mem_read(child + 0xEC, 4))[0],
                                                   struct.unpack("<f", uc.mem_read(child + 0xF0, 4))[0]]})
                if not completed:
                    child_update_error = f"manager update returned at {uc.reg_read(UC_X86_REG_EIP):#x}"
                    break
            except Exception as exc:
                manager_ticks.append({"tick": tick + 1, "completed": False,
                                      "error": f"{type(exc).__name__}: {exc} at {uc.reg_read(UC_X86_REG_EIP):#x}",
                                      "child_vtable": hex(u32(uc, child)),
                                      "child_field_34c": u32(uc, child + 0x34C),
                                      "esi": hex(uc.reg_read(UC_X86_REG_ESI)),
                                      "edx": hex(uc.reg_read(UC_X86_REG_EDX)),
                                      "trace": [hex(pc) for pc in probe._code_trace[-12:]]})
                child_update_error = f"manager update: {manager_ticks[-1]['error']}"
                break
            finally:
                probe._trace_active = False
        root_node = u32(uc, LIST + 0x58)
        node = u32(uc, root_node)
        live_nodes: list[dict[str, str]] = []
        seen_nodes: set[int] = set()
        while node != root_node and node not in seen_nodes and len(live_nodes) < 512:
            seen_nodes.add(node)
            obj = u32(uc, node + 8)
            live_nodes.append({"node": hex(node), "object": hex(obj),
                               "action": str(struct.unpack("<H", uc.mem_read(obj + 0x13C, 2))[0])
                               if obj > 0x1000 else "invalid"})
            node = u32(uc, node)
        manager_tick = {"ticks": manager_ticks,
                        "interface": hex(LIST - 4),
                        "update_slot": "vtable[4] -> 0x633ce0",
                        "object_retired": bool(manager_ticks and manager_ticks[-1].get("field_34c") == 0),
                        "last": manager_ticks[-1] if manager_ticks else None,
                        "live_node_count": len(live_nodes),
                        "original_child_still_linked": any(
                            row["object"] == child_factory["pointer"] for row in live_nodes),
                        "live_node_actions": [row["action"] for row in live_nodes],
                        "list_root_pointer": hex(u32(uc, LIST + 0x58)),
                        "root_node": {"next": hex(u32(uc, u32(uc, LIST + 0x58))),
                                      "previous": hex(u32(uc, u32(uc, LIST + 0x58) + 4)),
                                      "data": hex(u32(uc, u32(uc, LIST + 0x58) + 8))},
                        "list_header_words": [hex(u32(uc, LIST + offset))
                                              for offset in (0x54, 0x58, 0x5C, 0x60, 0x64, 0x68)]}
    return {
        "initialized_action": initialized_action,
        "manager_setup": manager_state,
        "defender_constructor": defender_constructor if real_factory and child_factory else None,
        "input_fixture": {"position": [x, y], "facing": facing,
                          "main_update_ebx": 1, "callback_slot_fixture": callback_index},
        "spawn_call": spawn,
        "child_factory_result": child_factory or None,
        "child_box_sync": child_box_sync,
        "child_updates": child_updates,
        "child_update_error": child_update_error,
        "manager_tick": manager_tick,
        "manager_node_visits": manager_node_visits,
        "factory_calls": factory_calls,
        "factory_returns": factory_returns,
        "create_object_helper_calls": create_object_helper_calls,
        "collision_matrix": collision_matrix,
        "pair_dispatch": pair_dispatch,
        "damage_response": damage_response,
        "callback_dispatch": callback,
        "main_update_dispatch_trace": dispatch_trace,
        "animation_tick_states": tick_states,
        "ticks_until_spawn": len(tick_states),
        "original_helpers_reached": original_helpers,
        "post_spawn_fields": {
            "meter_49e": struct.unpack("<H", uc.mem_read(PLAYER + 0x49E, 2))[0],
            "gauge_5e4": struct.unpack("<H", uc.mem_read(PLAYER + 0x5E4, 2))[0],
        },
        "error": errors or None,
        "scope": "Original action setter/initializer, 0x438c60 timer, action dispatch, helpers, spawn wrapper, and 0x464980 lookup execute. With real_factory=true, CRT startup and object manager constructor execute; manager interface slot +4 is directed to the original 0x784020 factory because its normal target is outside this pinned image. Player PAT/animation fixture, EBX=1 from skipped prologue, callback table/external dispatcher, and 0x487ca0 service remain controlled. In real_factory mode the original child box sync and 0x7876d0 update dispatcher run; pair collision/damage remain unresolved.",
    }


def run_original_hit_hurt_pair(probe: Suwako808FactoryProbe,
                               attacker: int, defender: int) -> dict[str, int]:
    uc = probe.uc
    sp = STACK + 0xB000 - 12
    uc.mem_write(sp, struct.pack("<3I", STOP, attacker, defender))
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_ECX, attacker)
    uc.reg_write(UC_X86_REG_EIP, 0x0047A5B0)
    uc.emu_start(0x0047A5B0, STOP, count=100000)
    if uc.reg_read(UC_X86_REG_EIP) != STOP:
        raise RuntimeError(f"0x47a5b0 did not return: {uc.reg_read(UC_X86_REG_EIP):#x}")
    return {"return_value": uc.reg_read(UC_X86_REG_EAX),
            "attacker_hit_boxes": uc.mem_read(attacker + 0x1CB, 1)[0],
            "defender_hurt_boxes": uc.mem_read(defender + 0x1CC, 1)[0]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dat-dir", type=Path, default=ROOT / "original")
    parser.add_argument("--x", type=float, default=320.0)
    parser.add_argument("--y", type=float, default=180.0)
    parser.add_argument("--facing", type=int, choices=(-1, 1), default=1)
    parser.add_argument("--real-factory", action="store_true",
                        help="execute CRT startup, object manager, and the actual 801 factory")
    parser.add_argument("--resolve-damage", action="store_true",
                        help="run original hit response after overlap (requires real factory)")
    parser.add_argument("--callback-index", type=int, choices=(0, 1, 2, 3), default=1,
                        help="callback table slot preloaded with the fixture function pointer")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/x86-remilia-412-spawn-probe.json")
    args = parser.parse_args()
    result = run_case(args.dat_dir, args.x, args.y, args.facing, args.callback_index,
                      real_factory=args.real_factory, resolve_damage=args.resolve_damage)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
