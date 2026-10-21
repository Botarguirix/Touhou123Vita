#!/usr/bin/env python3
"""Check Story lifecycle, replay input setup, and the per-call replay counter chain."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile  # noqa: E402
from capstone import CS_ARCH_X86, CS_MODE_32, Cs  # noqa: E402
from capstone.x86 import X86_OP_IMM  # noqa: E402

EXE_SHA256 = "24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3"
MODE_DISPATCHER = 0x0043CCA0
STORY_INITIALIZERS = {0: 0x0043B440, 6: 0x004378D0}
STORY_VTABLE = 0x0082192C
MANAGER_GLOBAL = 0x0085EB64
INPUT_STATE_GLOBAL = 0x0085EC98
INPUT_SOURCE_WRITER = 0x0042D6B0
LIFECYCLE_DISPATCHER = 0x0043D480
MODE_SETTER = 0x0043D8E0
INPUT_BACKEND_DISPATCHER = 0x0043DEE0
INPUT_BACKEND_TABLE = 0x0043E248
TITLE_VTABLE = 0x00820F9C
TITLE_UPDATE = 0x00426D50
TITLE_STATE_GLOBAL = 0x00848A94
TITLE_STATE_TAGS = 0x00427218
TITLE_STATE_JUMPS = 0x00427200
TITLE_REPLAY_SELECTOR = 0x00447C0C
TITLE_REPLAY_LOAD = 0x0044A120
REPLAY_STORY_DIR_FORMAT = 0x00821394
REPLAY_DIR_FORMAT = 0x008213C0
REPLAY_ENUM_PATTERN = 0x00821350
REPLAY_LIST_VTABLE = 0x0082133C
REPLAY_LIST_CONSTRUCTOR = 0x0042BBD0
REPLAY_LIST_ENUMERATOR = 0x0043C140
REPLAY_MENU_UPDATE = 0x00449FE0
REPLAY_ROW_FLAG_GETTER = 0x0043BA50
STORY_MANAGER_SLOT1_METHOD = 0x0047EAA0
STORY_MANAGER_SLOT5_METHOD = 0x0047F810
STORY_MANAGER_SLOT15_METHOD = 0x0047F7C0
STORY_REPLAY_CALLBACK = 0x0047EE10
STORY_SLOT15_HELPER = 0x00478640
LIFECYCLE_STATE3_HANDLER = 0x00437790
LIFECYCLE_STATE5_HANDLER = 0x004377E0
REPLAY_COUNTER_CALLBACK_CANDIDATE = 0x004787F0


def analyze(exe_path: Path) -> dict[str, object]:
    raw = exe_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXE_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {digest}")
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    def disasm(start: int, size: int):
        return list(md.disasm(pe.get_data(start - base, size), start))

    selector = disasm(MODE_DISPATCHER, 0x30)
    selector_text = [(ins.address, ins.mnemonic, ins.op_str) for ins in selector]
    direct_jumps = {ins.address: ins.operands[0].imm & 0xFFFFFFFF
                    for ins in selector if ins.mnemonic == "jmp" and ins.operands
                    and ins.operands[0].type == X86_OP_IMM}

    def u32(va: int) -> int:
        off = pe.get_offset_from_rva(va - base)
        return struct.unpack_from("<I", raw, off)[0]

    def cstring(va: int) -> str:
        off = pe.get_offset_from_rva(va - base)
        return raw[off:off + 256].split(b"\0", 1)[0].decode("cp932")

    def direct_call_sites(target: int) -> list[int]:
        sites: list[int] = []
        for section in pe.sections:
            if not (section.Characteristics & 0x20000000):
                continue
            blob = section.get_data()
            for offset, opcode in enumerate(blob[:-4]):
                if opcode != 0xE8:
                    continue
                call_va = base + section.VirtualAddress + offset
                displacement = struct.unpack_from("<i", blob, offset + 1)[0]
                if call_va + 5 + displacement == target:
                    sites.append(call_va)
        return sites

    def type_name(type_descriptor: int) -> str:
        offset = pe.get_offset_from_rva(type_descriptor - base)
        encoded = raw[offset + 8:offset + 168].split(b"\0", 1)[0]
        if not (encoded.startswith((b".?AV", b".?AU")) and encoded.endswith(b"@@")):
            raise ValueError(f"unexpected RTTI TypeDescriptor at 0x{type_descriptor:08x}")
        return encoded[4:-2].decode("ascii")

    title_complete_object_locator = u32(TITLE_VTABLE - 4)
    title_type_descriptor = u32(title_complete_object_locator + 12)
    title_hierarchy_descriptor = u32(title_complete_object_locator + 16)
    title_base_count = u32(title_hierarchy_descriptor + 8)
    title_base_array = u32(title_hierarchy_descriptor + 12)
    title_class_name = type_name(title_type_descriptor)
    title_base_classes = [
        type_name(u32(u32(title_base_array + i * 4)))
        for i in range(title_base_count)
    ]
    title_update_slot1_target = u32(TITLE_VTABLE + 4)
    replay_list_col = u32(REPLAY_LIST_VTABLE - 4)
    replay_list_type_descriptor = u32(replay_list_col + 12)
    replay_list_class_name = type_name(replay_list_type_descriptor)
    replay_list_slot1_target = u32(REPLAY_LIST_VTABLE + 4)
    replay_list_constructor_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(REPLAY_LIST_CONSTRUCTOR, 0x90))
    replay_list_enumerator_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(REPLAY_LIST_ENUMERATOR, 0x360))
    replay_menu_update_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(REPLAY_MENU_UPDATE, 0x220))
    replay_row_flag_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(REPLAY_ROW_FLAG_GETTER, 0x20))
    lifecycle_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(LIFECYCLE_DISPATCHER, 0x90))
    lifecycle_state3_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(LIFECYCLE_STATE3_HANDLER, 0x20))
    story_slot1_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(STORY_MANAGER_SLOT1_METHOD, 0x300))
    story_slot5_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(STORY_MANAGER_SLOT5_METHOD, 0x70))
    story_slot15_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(STORY_MANAGER_SLOT15_METHOD, 0x20))
    story_slot15_helper_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(STORY_SLOT15_HELPER, 0x40))
    lifecycle_state5_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(LIFECYCLE_STATE5_HANDLER, 0x30))
    counter_callback_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in disasm(REPLAY_COUNTER_CALLBACK_CANDIDATE, 0x70))
    lifecycle_table = [u32(0x0043D520 + i * 4) for i in range(5)]
    replay_selector_handler = disasm(TITLE_REPLAY_SELECTOR, 0x180)
    replay_load_handler = disasm(TITLE_REPLAY_LOAD, 0xC0)
    replay_selector_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in replay_selector_handler)
    replay_load_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in replay_load_handler)
    replay_story_format = cstring(REPLAY_STORY_DIR_FORMAT)
    replay_format = cstring(REPLAY_DIR_FORMAT)
    replay_enum_pattern = cstring(REPLAY_ENUM_PATTERN)

    def title_state_target(state: int) -> tuple[int, int]:
        index = state - 2
        tag_offset = pe.get_offset_from_rva(TITLE_STATE_TAGS - base) + index
        tag = raw[tag_offset]
        target = u32(TITLE_STATE_JUMPS + tag * 4)
        return tag, target

    title_state_targets = {
        state: title_state_target(state) for state in (8, 9, 12)
    }

    writes = {}
    for mode, initializer in STORY_INITIALIZERS.items():
        code = disasm(initializer, 0x90)
        writes[str(mode)] = {
            "initializer": f"0x{initializer:08x}",
            "manager_global_write": any(
                ins.mnemonic == "mov" and "[0x85eb64]" in ins.op_str.lower()
                for ins in code),
            "story_vtable_write": any(
                ins.mnemonic == "mov" and "0x82192c" in ins.op_str.lower()
                for ins in code),
        }

    writer = disasm(INPUT_SOURCE_WRITER, 0x90)
    writer_text = "\n".join(f"{ins.mnemonic} {ins.op_str}" for ins in writer)
    caller = disasm(0x00428180, 0x40)
    caller_rows = [{"va": f"0x{ins.address:08x}",
                    "target": f"0x{ins.operands[0].imm & 0xFFFFFFFF:08x}"}
                   for ins in caller if ins.mnemonic == "call" and ins.operands
                   and ins.operands[0].type == X86_OP_IMM]
    replay_callback = disasm(0x0047EE10, 0x70)
    replay_callback_targets = [ins.operands[0].imm & 0xFFFFFFFF
                               for ins in replay_callback if ins.mnemonic == "call"
                               and ins.operands and ins.operands[0].type == X86_OP_IMM]
    candidate_mode_path = disasm(0x00426DE2, 0x0C)
    candidate_pushes = [ins.operands[0].imm for ins in candidate_mode_path
                        if ins.mnemonic == "push" and ins.operands
                        and ins.operands[0].type == X86_OP_IMM]
    lifecycle = disasm(LIFECYCLE_DISPATCHER, 0xA0)
    lifecycle_targets = {ins.operands[0].imm & 0xFFFFFFFF
                         for ins in lifecycle if ins.mnemonic == "call" and ins.operands
                         and ins.operands[0].type == X86_OP_IMM}
    mode_setter = disasm(MODE_SETTER, 0x80)
    mode_6_tail = disasm(0x0043D9C1, 0x40)
    input_manager_setup = disasm(0x0043D310, 0x90)
    input_manager_setup_text = "\n".join(
        f"{ins.mnemonic} {ins.op_str}" for ins in input_manager_setup)
    input_backend_dispatcher = disasm(INPUT_BACKEND_DISPATCHER, 0x40)
    input_backend_callers = direct_call_sites(INPUT_BACKEND_DISPATCHER)
    input_default_init_callers = direct_call_sites(0x0043CCF0)
    backend_state_handler = disasm(0x004209C1, 0x1B0)
    backend_mode_handler = disasm(0x00425703, 0x240)
    input_config_handler = disasm(0x0044AF00, 0x1B0)
    backend_state_handler_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in backend_state_handler)
    backend_mode_handler_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in backend_mode_handler)
    input_config_handler_text = "\n".join(
        f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
        for ins in input_config_handler)
    input_backend_targets = {
        mode: u32(INPUT_BACKEND_TABLE + 4 * (mode - 1))
        for mode in range(1, 9)
    }
    input_backend_mode_6_target = input_backend_targets[6]
    input_backend_mode_3_target = input_backend_targets[3]
    backend_branch_text = {
        1: "\n".join(f"{ins.mnemonic} {ins.op_str}"
                     for ins in disasm(0x0043DFE4, 0x30)
                     + disasm(0x0043DFAF, 0x40)),
        2: "\n".join(f"{ins.mnemonic} {ins.op_str}"
                     for ins in disasm(0x0043DF20, 0x70)),
        3: "\n".join(f"{ins.mnemonic} {ins.op_str}"
                     for ins in disasm(0x0043E0A0, 0x90)),
        4: "\n".join(f"{ins.mnemonic} {ins.op_str}"
                     for ins in disasm(0x0043DFF9, 0x60)),
        5: "\n".join(f"{ins.mnemonic} {ins.op_str}"
                     for ins in disasm(0x0043E05B, 0x50)),
        6: "\n".join(f"{ins.mnemonic} {ins.op_str}"
                     for ins in disasm(0x0043E122, 0x125)),
        7: "\n".join(f"{ins.mnemonic} {ins.op_str}"
                     for ins in disasm(0x0043E122, 0x125)),
        8: "\n".join(f"{ins.mnemonic} {ins.op_str}"
                     for ins in disasm(0x0043DF7E, 0x70)),
    }
    input_backend_mode_6_body = disasm(input_backend_mode_6_target, 0x120)
    input_backend_mode_6_text = "\n".join(
        f"{ins.mnemonic} {ins.op_str}" for ins in input_backend_mode_6_body)
    input_backend_mode_3_body = disasm(input_backend_mode_3_target, 0x90)
    input_backend_mode_3_text = "\n".join(
        f"{ins.mnemonic} {ins.op_str}" for ins in input_backend_mode_3_body)
    checks = {
        "selector_reads_global_mode": any(
            ins.mnemonic == "mov" and "[0x85ec10]" in ins.op_str.lower()
            for ins in selector),
        "lifecycle_phase_2_dispatches_manager_selector": 0x0043CCA0 in lifecycle_targets,
        "lifecycle_dispatcher_routes_through_manager_lifecycle_wrappers": {
            0x00437790, 0x004377B0, 0x004377E0
        }.issubset(lifecycle_targets),
        "mode_setter_writes_first_argument_to_mode_global": any(
            ins.mnemonic == "mov" and "[0x85ec10]" in ins.op_str.lower()
            and ins.operands[1].type == 1 for ins in mode_setter
            if len(ins.operands) > 1),
        "mode_setter_stores_second_argument_as_state_2": any(
            ins.mnemonic == "mov" and "[0x85ec08]" in ins.op_str.lower()
            for ins in mode_setter),
        "candidate_path_sets_mode_6_and_state_2": candidate_pushes == [2, 6]
        and any(ins.mnemonic == "call" and ins.operands
                and ins.operands[0].type == X86_OP_IMM
                and (ins.operands[0].imm & 0xFFFFFFFF) == MODE_SETTER
                for ins in candidate_mode_path),
        "mode_6_setup_initializes_both_input_slots":
            "[esi + 0x1f0]" in input_manager_setup_text
            and "[esi + 0x1f8]" in input_manager_setup_text,
        "mode_6_setup_links_story_input_global": any(
            ins.mnemonic == "mov" and "[edx + 0x6bc]" in ins.op_str.lower()
            and "0x85ec98" in ins.op_str.lower() for ins in mode_6_tail),
        "mode_6_setup_schedules_lifecycle_state_2": any(
            ins.mnemonic == "push" and ins.operands
            and ins.operands[0].type == X86_OP_IMM and ins.operands[0].imm == 2
            for ins in mode_6_tail)
            and any(ins.mnemonic == "call" and ins.operands
                    and ins.operands[0].type == X86_OP_IMM
                    and (ins.operands[0].imm & 0xFFFFFFFF) == 0x0043D830
                    for ins in mode_6_tail),
        "input_backend_dispatcher_uses_mode_indexed_table": any(
            ins.mnemonic == "mov" and "[0x85ec10]" in ins.op_str.lower()
            for ins in input_backend_dispatcher)
            and any(ins.mnemonic == "jmp"
                    and "[eax*4 + 0x43e248]" in ins.op_str.lower()
                    for ins in input_backend_dispatcher),
        "input_backend_mode_6_uses_common_setup_path":
            input_backend_mode_6_target == 0x0043E122,
        "input_backend_mode_6_does_not_assign_source_pointer_slots":
            "[0x8602ac]" not in input_backend_mode_6_text.lower()
            and "[0x8602cc]" not in input_backend_mode_6_text.lower(),
        "input_backend_mode_3_assigns_two_source_pointer_slots":
            input_backend_mode_3_target == 0x0043E0A0
            and "[0x8602ac]" in input_backend_mode_3_text.lower()
            and "[0x8602cc]" in input_backend_mode_3_text.lower()
            and "0x85ef20" in input_backend_mode_3_text.lower()
            and "0x85f70c" in input_backend_mode_3_text.lower(),
        "input_backend_mode_table_matches_all_eight_entries":
            input_backend_targets == {
                1: 0x0043DFE4, 2: 0x0043DF20, 3: 0x0043E0A0,
                4: 0x0043DFF9, 5: 0x0043E05B, 6: 0x0043E122,
                7: 0x0043E122, 8: 0x0043DF7E,
            },
        "input_backend_single_source_modes_write_one_slot": all(
            "[0x8602ac]" in backend_branch_text[mode].lower()
            and "0x85ef20" in backend_branch_text[mode].lower()
            and "[0x8602cc]" in backend_branch_text[mode].lower()
            and ("0x8602cc], 0" in backend_branch_text[mode].lower()
                 or "[0x8602cc], ebx" in backend_branch_text[mode].lower())
            for mode in (1, 2, 8)),
        "input_backend_modes_4_and_5_write_manager_source_slots": all(
            "[0x8602ac]" in backend_branch_text[mode].lower()
            and "[0x8602cc]" in backend_branch_text[mode].lower()
            and "+ 0x1f0" in backend_branch_text[mode].lower()
            and "0x1f8" in backend_branch_text[mode].lower()
            for mode in (4, 5)),
        "input_backend_modes_6_and_7_preserve_source_slots_directly": all(
            "[0x8602ac]" not in backend_branch_text[mode].lower()
            and "[0x8602cc]" not in backend_branch_text[mode].lower()
            for mode in (6, 7)),
        "input_backend_direct_call_sites_match_observed_callers":
            input_backend_callers == [0x00420A91, 0x004258FE],
        "input_default_init_direct_call_sites_match_observed_callers":
            input_default_init_callers == [0x004258EC, 0x0044B091],
        "backend_state_handler_guards_dispatch_call":
            "mov eax, 1" in backend_state_handler_text.lower()
            and "[esi + 0x58], eax" in backend_state_handler_text.lower()
            and "[esi + 0x4f60], 0" in backend_state_handler_text.lower()
            and "call 0x41ffa0" in backend_state_handler_text.lower()
            and "00420a91: call 0x43dee0" in backend_state_handler_text.lower(),
        "backend_mode_handler_dispatches_only_for_selector_1":
            "mov ebx, 1" in backend_mode_handler_text.lower()
            and "004258e2: call 0x43ccd0" in backend_mode_handler_text.lower()
            and "004258f3: call 0x43ccd0" in backend_mode_handler_text.lower()
            and "004258fe: call 0x43dee0" in backend_mode_handler_text.lower()
            and input_backend_targets[1] == 0x0043DFE4,
        "backend_mode_handler_mode_0_uses_default_single_source_init":
            "004258eb: push eax" in backend_mode_handler_text.lower()
            and "004258ec: call 0x43ccf0" in backend_mode_handler_text.lower()
            and "004258e7: test eax, eax" in backend_mode_handler_text.lower(),
        "input_config_handler_sets_mode_7_state_1_before_single_source_init":
            "0044afe4: push 7" in input_config_handler_text.lower()
            and "0044afe6: call 0x43d8e0" in input_config_handler_text.lower()
            and "0044b091: call 0x43ccf0" in input_config_handler_text.lower()
            and "0044b07a: call 0x42ea50" in input_config_handler_text.lower()
            and "0044b08a: call 0x42c500" in input_config_handler_text.lower(),
        "title_rtti_and_update_vtable_slot_match":
            title_class_name == "CTitle"
            and title_base_classes == ["CTitle", "CSceneBase", "IScene"]
            and title_update_slot1_target == TITLE_UPDATE,
        "title_state_12_selects_mode_6_state_2":
            title_state_targets[12] == (4, 0x00426DE2)
            and candidate_pushes == [2, 6],
        "title_neighboring_states_select_mode_4_and_5":
            title_state_targets[8] == (2, 0x00426D9A)
            and title_state_targets[9] == (3, 0x00426DBE),
        "title_replay_selector_zero_requests_story_state_12":
            "00447c23: cmp eax, ebx" in replay_selector_text.lower()
            and "00447c25: je 0x447cbb" in replay_selector_text.lower()
            and "00447cc7: mov dword ptr [0x848a94], 0xc" in replay_selector_text.lower()
            and "00447cdb: call 0x447310" in replay_selector_text.lower(),
        "title_replay_selection_has_generic_replay_loader_path":
            "0044a13a: call 0x43cec0" in replay_load_text.lower()
            and "0044a141: call 0x42e030" in replay_load_text.lower()
            and "0044a158: mov dword ptr [0x848a94], 6" in replay_load_text.lower(),
        "story_replay_list_uses_timestamp_character_filename_template":
            replay_story_format == "replay\\story\\%02d%02d%02d_%02d%02d_%s_story"
            and "0x0042c34d" in [f"0x{ins.address:08x}" for ins in
                               disasm(0x0042C0A0, 0x500)]
            and "0x821394" in "\n".join(
                ins.op_str.lower() for ins in disasm(0x0042C0A0, 0x500)),
        "replay_browser_enumerates_rep_files": replay_enum_pattern == "*.rep",
        "replay_list_rtti_and_virtual_enumerator_match":
            replay_list_class_name == "CReplayList"
            and replay_list_slot1_target == REPLAY_LIST_ENUMERATOR,
        "replay_list_constructor_sets_rep_filter_and_root":
            "0042bbfd: push 5" in replay_list_constructor_text.lower()
            and "0042bc1c: push 0x821330" in replay_list_constructor_text.lower()
            and "0042bbff: push 0x821350" in replay_list_constructor_text.lower(),
        "replay_list_virtual_method_calls_directory_enumerator":
            "0043c217: call dword ptr [0x82005c]" in replay_list_enumerator_text.lower()
            and "test byte ptr [esp + 0x70], 0x10" in replay_list_enumerator_text.lower(),
        "replay_menu_update_gates_on_active_selection_and_row_type":
            "0044a061: cmp dword ptr [edi + 8], ebx" in replay_menu_update_text.lower()
            and "0044a07f: call 0x43ba50" in replay_menu_update_text.lower()
            and "0044a086: je 0x44a0de" in replay_menu_update_text.lower()
            and "0044a141: call 0x42e030" in replay_menu_update_text.lower(),
        "replay_menu_load_branch_reads_selected_row_components":
            "0044a0de: mov ecx, dword ptr [ebx]" in replay_menu_update_text.lower()
            and "0044a0e3: call 0x43b9f0" in replay_menu_update_text.lower()
            and "0044a10e: call 0x43b620" in replay_menu_update_text.lower()
            and "0044a12c: call dword ptr [0x8201d8]" in replay_menu_update_text.lower(),
        "replay_row_type_flag_is_read_from_indexed_list":
            "cmp eax, dword ptr [ecx + 0x28]" in replay_row_flag_text.lower()
            and "add ecx, 0x18" in replay_row_flag_text.lower()
            and "call 0x42ab00" in replay_row_flag_text.lower()
            and "mov al, byte ptr [eax]" in replay_row_flag_text.lower(),
        "lifecycle_state3_dispatches_global_manager_slot1":
            lifecycle_table == [0x0043D4A4, 0x0043D4B7, 0x0043D4CA,
                                0x0043D4E5, 0x0043D4F8]
            and "0043d49d: jmp dword ptr [eax*4 + 0x43d520]" in lifecycle_text.lower()
            and "0043d4db: call 0x437790" in lifecycle_text.lower()
            and "0043779c: mov eax, dword ptr [eax + 4]" in lifecycle_state3_text.lower()
            and "004377a0: call eax" in lifecycle_state3_text.lower(),
        "lifecycle_state5_dispatches_manager_slot2":
            lifecycle_table[4] == 0x0043D4F8
            and "004377f6: mov ecx, dword ptr [0x85eb64]" in lifecycle_state5_text.lower()
            and "004377fe: mov edx, dword ptr [eax + 8]" in lifecycle_state5_text.lower()
            and "00437801: jmp edx" in lifecycle_state5_text.lower(),
        "story_global_manager_slot1_is_47eaa0":
            u32(STORY_VTABLE + 4) == STORY_MANAGER_SLOT1_METHOD
            and "0047eae2: cmp eax, 2" in story_slot1_text.lower()
            and "0047eaf1: call 0x42d560" in story_slot1_text.lower(),
        "story_slot5_47f810_dispatches_slot16_47ee10":
            u32(STORY_VTABLE + 5 * 4) == STORY_MANAGER_SLOT5_METHOD
            and u32(STORY_VTABLE + 16 * 4) == STORY_REPLAY_CALLBACK
            and "0047f829: mov edx, dword ptr [esi]" in story_slot5_text.lower()
            and "0047f82b: mov eax, dword ptr [edx + 0x40]" in story_slot5_text.lower()
            and "0047f82e: call eax" in story_slot5_text.lower(),
        "story_slot5_decodes_then_dispatches_slot15_counter_once":
            u32(STORY_VTABLE + 15 * 4) == STORY_MANAGER_SLOT15_METHOD
            and "0047f82e: call eax" in story_slot5_text.lower()
            and "0047f84e: call 0x478640" in story_slot5_text.lower()
            and "00478645: mov edx, dword ptr [eax + 0x3c]" in story_slot15_helper_text.lower()
            and "00478648: call edx" in story_slot15_helper_text.lower()
            and "0047f7c0: mov word ptr [0x85d74c], 0" in story_slot15_text.lower()
            and "0047f7c9: jmp 0x4787f0" in story_slot15_text.lower()
            and "00478851: add dword ptr [0x85eb58], 1" in counter_callback_text.lower(),
        "counter_callback_candidate_uses_different_global_then_increments_counter":
            "00478839: mov ecx, dword ptr [0x85eb70]" in counter_callback_text.lower()
            and "00478841: mov edx, dword ptr [eax + 0x14]" in counter_callback_text.lower()
            and "00478844: call edx" in counter_callback_text.lower()
            and "00478851: add dword ptr [0x85eb58], 1" in counter_callback_text.lower()
            and MANAGER_GLOBAL != 0x0085EB70,
        "story_replay_callback_47ee10_is_a_distinct_vtable_method":
            u32(STORY_VTABLE + 16 * 4) == STORY_REPLAY_CALLBACK
            and "0047ee36: call 0x43ced0" in "\n".join(
                f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
                for ins in disasm(STORY_REPLAY_CALLBACK, 0x80)).lower()
            and "0047ee47: call 0x42a410" in "\n".join(
                f"{ins.address:08x}: {ins.mnemonic} {ins.op_str}"
                for ins in disasm(STORY_REPLAY_CALLBACK, 0x80)).lower(),
        "mode_0_selects_story_initializer": direct_jumps.get(0x0043CCC8) == 0x0043B440,
        "mode_6_selects_story_initializer": direct_jumps.get(0x0043CCBE) == 0x004378D0,
        "both_story_initializers_write_manager_global": all(
            row["manager_global_write"] for row in writes.values()),
        "both_story_initializers_write_story_vtable": all(
            row["story_vtable_write"] for row in writes.values()),
        "input_source_writer_sets_f0_from_two_source_presence":
            "[esi + 0xf0]" in writer_text and "[edi + 0x44]" in writer_text
            and "[edi + 0x24]" in writer_text and "setne" in writer_text,
        "input_source_writer_rebuilds_input_state": 0x0042D420 in [
            ins.operands[0].imm & 0xFFFFFFFF for ins in writer
            if ins.mnemonic == "call" and ins.operands
            and ins.operands[0].type == X86_OP_IMM],
        "observed_input_setup_calls_source_writer": any(
            row["target"] == f"0x{INPUT_SOURCE_WRITER:08x}" for row in caller_rows),
        "input_getter_returns_separate_global": any(
            ins.mnemonic == "mov" and "0x85ec98" in ins.op_str.lower()
            for ins in disasm(0x0043CEC0, 0x10)),
        "story_callback_gets_input_global_before_replay_decoder":
            replay_callback_targets[:3] == [0x0043CED0, 0x0043CEC0, 0x0042A410],
        "input_source_writer_uses_same_input_global": any(
            row["target"] == "0x0043cec0" for row in caller_rows)
            and any(row["target"] == f"0x{INPUT_SOURCE_WRITER:08x}"
                    for row in caller_rows),
    }
    if not all(checks.values()):
        raise RuntimeError(f"replay manager/source contract mismatch: {checks}; jumps={direct_jumps}")
    return {
        "schema": 1,
        "exe_sha256": digest,
        "profile": "provided-original-2009",
        "mode_dispatcher_va": f"0x{MODE_DISPATCHER:08x}",
        "mode_setter_va": f"0x{MODE_SETTER:08x}",
        "lifecycle_dispatcher_va": f"0x{LIFECYCLE_DISPATCHER:08x}",
        "manager_global_va": f"0x{MANAGER_GLOBAL:08x}",
        "story_modes_observed": writes,
        "manager_global_value": "Story manager instance written by the selected initializer",
        "input_source_writer_va": f"0x{INPUT_SOURCE_WRITER:08x}",
        "input_state_global_va": f"0x{INPUT_STATE_GLOBAL:08x}",
        "candidate_mode_path": {
            "callsite": "0x00426de6",
            "arguments_pushed": candidate_pushes,
            "interpretation": "first argument selects manager mode 6; second argument sets state 2, which the Story callback checks before decoding",
        },
        "mode_6_input_setup": {
            "helper_va": "0x0043d310",
            "manager_slots": ["+0x1f0", "+0x1f8"],
            "input_state_pointer": "0x0085ec98",
            "lifecycle_state": 2,
            "scope": "Both manager slots are initialized; this does not prove both source-presence flags used to derive input +0xf0 are nonzero.",
        },
        "input_backend_mode_6": {
            "dispatcher_va": f"0x{INPUT_BACKEND_DISPATCHER:08x}",
            "table_va": f"0x{INPUT_BACKEND_TABLE:08x}",
            "table_index": 5,
            "target_va": f"0x{input_backend_mode_6_target:08x}",
            "source_pointer_writes": [],
            "comparison_mode_3_target_va": f"0x{input_backend_mode_3_target:08x}",
            "comparison_mode_3_source_pointer_values": ["0x0085ef20", "0x0085f70c"],
            "scope": "Mode 6's backend table entry uses a common setup path that does not write either source-pointer slot. The two-slot assignment belongs to mode 3; mode 6's effective +0xf0 still depends on input state established elsewhere.",
        },
        "input_backend_modes": {
            str(mode): {
                "target_va": f"0x{target:08x}",
                "source_slot_effect": (
                    "one source: 0x85ef20 and null"
                    if mode in (1, 2, 8) else
                    "two fixed sources: 0x85ef20 and 0x85f70c"
                    if mode == 3 else
                    "two manager slots: +0x1f0 and +0x1f8"
                    if mode in (4, 5) else
                    "no direct source-slot write; prior values persist"
                ),
            }
            for mode, target in input_backend_targets.items()
        },
        "input_backend_callers": [
            {
                "callsite_va": f"0x{site:08x}",
                "context": (
                    "State handler at 0x4209c1: [this+0x58]==1 and [this+0x4f60]>=0, "
                    "then 0x41ffa0 before backend dispatch. Its mode value remains dynamic."
                    if site == 0x00420A91 else
                    "Handler at 0x425703 enters the backend dispatcher only when the global "
                    "selector returned by 0x43ccd0 equals local EBX=1. This selects backend "
                    "mode 1, not the Story selector-6 path."
                ),
            }
            for site in input_backend_callers
        ],
        "input_default_init_callers": [
            {
                "callsite_va": f"0x{site:08x}",
                "context": (
                    "Handler at 0x425703 calls the one-source initializer when the global "
                    "selector getter returns zero."
                    if site == 0x004258EC else
                    "Handler at 0x44af00 first sets manager mode 7/state 1, copies input/config "
                    "fields, then calls the one-source initializer. This is not evidence of "
                    "Story replay setup."
                ),
            }
            for site in input_default_init_callers
        ],
        "title_scene_transition": {
            "vtable_va": f"0x{TITLE_VTABLE:08x}",
            "class": title_class_name,
            "base_classes": title_base_classes,
            "update_slot_index": 1,
            "update_va": f"0x{title_update_slot1_target:08x}",
            "state_global_va": f"0x{TITLE_STATE_GLOBAL:08x}",
            "states": {
                str(state): {
                    "jump_table_tag": tag,
                    "target_va": f"0x{target:08x}",
                }
                for state, (tag, target) in title_state_targets.items()
            },
            "state_12_request": {"manager_mode": 6, "lifecycle_state": 2},
            "replay_selector_handler_va": f"0x{TITLE_REPLAY_SELECTOR:08x}",
            "replay_loader_handler_va": f"0x{TITLE_REPLAY_LOAD:08x}",
            "replay_selector_zero_branch": "state 12, associated value 6, transition helper 0x447310",
            "replay_loader_path": "0x44a120 calls 0x42e030 with a constructed replay path; on success it sets title state 6",
            "story_replay_filename_template_va": f"0x{REPLAY_STORY_DIR_FORMAT:08x}",
            "story_replay_filename_template": replay_story_format,
            "other_replay_filename_template": replay_format,
            "replay_browser_pattern": replay_enum_pattern,
            "replay_list_class": replay_list_class_name,
            "replay_list_vtable_va": f"0x{REPLAY_LIST_VTABLE:08x}",
            "replay_list_constructor_va": f"0x{REPLAY_LIST_CONSTRUCTOR:08x}",
            "replay_list_virtual_enumerator_va": f"0x{replay_list_slot1_target:08x}",
            "replay_menu_update_va": f"0x{REPLAY_MENU_UPDATE:08x}",
            "replay_row_flag_getter_va": f"0x{REPLAY_ROW_FLAG_GETTER:08x}",
            "replay_selection_gate": "active menu selection; a nonzero row flag takes the list-navigation branch, while a zero flag reads the selected row components, formats the path, and calls the replay loader",
            "active_lifecycle_dispatch": {
                "dispatcher_va": f"0x{LIFECYCLE_DISPATCHER:08x}",
                "state3_target_va": f"0x{lifecycle_table[2]:08x}",
                "manager_slot1_va": f"0x{u32(STORY_VTABLE + 4):08x}",
                "manager_slot5_va": f"0x{u32(STORY_VTABLE + 5 * 4):08x}",
                "manager_slot15_va": f"0x{u32(STORY_VTABLE + 15 * 4):08x}",
                "story_replay_callback_slot16_va": f"0x{STORY_REPLAY_CALLBACK:08x}",
                "slot5_to_slot16_callsite_va": "0x0047f82e",
                "slot5_to_slot15_helper_callsite_va": "0x0047f84e",
                "slot15_helper_dispatch_callsite_va": "0x00478648",
                "slot15_method_tailcall_va": "0x0047f7c9",
                "counter_callback_candidate_va": f"0x{REPLAY_COUNTER_CALLBACK_CANDIDATE:08x}",
                "counter_callback_candidate_global_va": "0x0085eb70",
                "counter_increment_va": "0x00478851",
                "scope": "Lifecycle case 3 dispatches Story slot 1 at 0x47eaa0; this differs from slot 5 at 0x47f810. Each static execution path through slot 5 calls the replay decoder via slot 16 once at 0x47f82e, then invokes helper 0x478640, which dispatches Story slot 15 at 0x478648. Story slot 15 (0x47f7c0) resets 0x85d74c and tail-calls 0x4787f0; that routine calls an offset +0x14 method from the separate global 0x85eb70 and increments the replay/record counter 0x85eb58 once. This proves one counter increment per slot-5 invocation, but not how many slot-5 invocations occur per simulation or rendered frame.",
            },
            "provided_sanae_replay_matches_story_template":
                "090815_2219_sanae_story".startswith("090815_2219_")
                and replay_story_format.endswith("_%s_story"),
            "scope": "Static CTitle control flow identifies a selector-index-zero branch that requests state 12 and a separate .rep-loading method that requests state 6. This is consistent with Story entry and replay selection/loading as distinct menu steps, but the visible label/index mapping and live reachability for the supplied Sanae replay remain unproven.",
        },
        "story_callback_input_path": [f"0x{address:08x}" for address in replay_callback_targets[:3]],
        "input_setup_call_window_calls": caller_rows,
        "checks": checks,
        "scope": ("Static control flow connects the mode-6 selector, the Story callback, the shared input global, "
                  "and the source-presence flags read by its decoder. It identifies a code path setting mode 6/state 2, "
                  "but does not prove that this branch is reached by the supplied replay or establish per-frame cadence."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(analyze(args.exe), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
