import unittest
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX,
                               UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESI,
                               UC_X86_REG_ESP)

from tools.scan_player_field_884 import ROOT, scan


class PlayerField884JumpTableTests(unittest.TestCase):
    def test_character_slot10_jump_tables_seed_300_count(self):
        report = scan(
            ROOT / "original/th123.exe",
            ROOT / "artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/character-input/vtable-handlers.tsv",
        )
        self.assertEqual(report["case_count"], 10)
        self.assertEqual(
            {case["character"] for case in report["cases"]},
            {"Reimu", "Marisa", "Alice", "Patchouli", "Chirno",
             "Meirin", "Sanae", "Suwako", "Utsuho", "Namazu"},
        )
        self.assertTrue(all(case["seed_300_register_present"]
                            for case in report["cases"]))
        self.assertTrue(all(case["input_type_gate_value"] == 2 and
                            case["hand_count_gate_instruction"].endswith(", 1") and
                            case["deque_element_index"] == 0 and
                            case["deque_indexer"] == "0x456c80"
                            for case in report["cases"]))
        self.assertTrue(all(case["assignment"].startswith("mov word ptr [esi + 0x884]")
                            for case in report["cases"]))
        ranges = {case["character"]: case["dequeued_values_selecting_seed_case"]
                  for case in report["cases"]}
        self.assertEqual(ranges["Reimu"], list(range(16)))
        self.assertEqual(ranges["Marisa"], list(range(12)))
        self.assertEqual(ranges["Alice"], list(range(12)))
        self.assertEqual(ranges["Patchouli"], list(range(12)))
        self.assertEqual(ranges["Chirno"], list(range(8)))
        self.assertEqual(ranges["Meirin"], list(range(8)))
        self.assertEqual(ranges["Sanae"], list(range(8)))
        self.assertEqual(ranges["Suwako"], list(range(20)))
        self.assertEqual(ranges["Utsuho"], list(range(16)))
        self.assertEqual(ranges["Namazu"], list(range(16)))
        self.assertTrue(all(case["mapping_base"] ==
                            hex(int(case["jump_table"], 16) + 4)
                            for case in report["cases"]))
        self.assertTrue(all(set(case["mapping_bytes_through_maximum"]) == {0}
                            for case in report["cases"]))
        self.assertEqual(report["common_type_zero_card_ids"], list(range(21)))
        self.assertTrue(all(
            case["system_card_ids_in_dispatch_range"] ==
            list(range(len(case["dequeued_values_selecting_seed_case"])))
            for case in report["cases"]))
        namazu = next(case for case in report["cases"]
                      if case["character"] == "Namazu")
        self.assertEqual(namazu["rtti_name"], ".?AVNamazu@@")
        self.assertEqual(namazu["vtable"], "0x85f824")
        self.assertEqual(namazu["jump_table_targets"], 1)
        pe = pefile.PE(str(ROOT / "original/th123.exe"), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        ctor = {(ins.mnemonic, ins.op_str) for ins in md.disasm(
            pe.get_data(0x7EC4C0 - base, 0x80), 0x7EC4C0)}
        self.assertIn(("mov", "dword ptr [esi], 0x85f824"), ctor)
        self.assertIn(("call", "0x46c330"), ctor)
        self.assertIn(("call", "0x7ec2a0"), ctor)
        character_dispatch = struct.unpack(
            "<22I", pe.get_data(0x46DE64 - base, 22 * 4))
        self.assertEqual(character_dispatch[21], 0x46DDFC)
        self.assertEqual(character_dispatch[20], 0x46DE2F)
        factory = {(ins.mnemonic, ins.op_str) for ins in md.disasm(
            pe.get_data(0x46DDFC - base, 0x44), 0x46DDFC)}
        self.assertIn(("push", "0x8a0"), factory)
        self.assertIn(("call", "0x7ec4c0"), factory)
        linear_seeds = {
            row["address"] for row in report["linear_text_field_references"]
            if row["address"] in {"0x490795", "0x4bd6f2", "0x51026a",
                                   "0x5414cd", "0x6e33ce", "0x71a81e",
                                   "0x73c3dd", "0x765ebb", "0x79f78b",
                                   "0x7d47b2"}
        }
        self.assertEqual(len(linear_seeds), 10)

    def test_reimu_timer_expiry_spawns_common_spell_break_gauge(self):
        exe = ROOT / "original/th123.exe"
        pe = pefile.PE(str(exe), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        md.detail = True
        instructions = list(md.disasm(
            pe.get_data(0x490795 - base, 0x180), 0x490795))
        rendered = {(ins.mnemonic, ins.op_str) for ins in instructions}
        self.assertIn(("mov", "word ptr [esi + 0x884], bx"), rendered)
        self.assertIn(("mov", "word ptr [esi + 0x886], bx"), rendered)
        self.assertIn(("mov", "eax, 1"), rendered)
        self.assertIn(("cmp", "word ptr [esi + 0x884], ax"), rendered)
        self.assertIn(("mov", "word ptr [esi + 0x884], cx"), rendered)
        spawn = next(i for i, ins in enumerate(instructions)
                     if ins.mnemonic == "push" and ins.operands and
                     ins.operands[0].type == X86_OP_IMM and
                     ins.operands[0].imm == 0x4B1)
        factory = next(i for i, ins in enumerate(instructions)
                       if ins.mnemonic == "call" and ins.operands and
                       ins.operands[0].type == X86_OP_IMM and
                       ins.operands[0].imm == 0x46EB30)
        self.assertLess(spawn, factory)
        with (ROOT / "artifacts/pat-detail.tsv").open(encoding="cp932") as stream:
            rows = [line.rstrip("\n").split("\t") for line in stream]
        gauge_images = {row[8] for row in rows
                        if len(row) > 8 and row[0] == "data/character/common/common.pat"
                        and row[1] == "1201"}
        self.assertTrue({"spellBreakGage.bmp", "spellBreakGageR.bmp",
                         "spellBreakBar.bmp"}.issubset(gauge_images))

    def test_original_reimu_expiry_path_runs_to_action_1201_factory(self):
        exe = ROOT / "original/th123.exe"
        pe = pefile.PE(str(exe))
        base = pe.OPTIONAL_HEADER.ImageBase
        image = pe.get_memory_mapped_image()
        uc = Uc(UC_ARCH_X86, UC_MODE_32)
        uc.mem_map(base, (len(image) + 0xFFF) & ~0xFFF)
        uc.mem_write(base, image)
        player, stack, stop = 0x01000000, 0x02000000, 0x03000000
        uc.mem_map(player, 0x1000)
        uc.mem_map(stack, 0x10000)
        uc.mem_write(player, bytes(0x1000))
        uc.mem_write(player + 0x184, struct.pack("<H", 1000))
        uc.mem_write(player + 0x4BE, struct.pack("<H", 0))
        uc.mem_write(player + 0x884, struct.pack("<H", 1))
        writes = []
        factory = {"entered": False, "action": None, "player_hp": None,
                   "timer": None, "aux_timer": None}

        def on_write(_uc, _access, address, size, value, _user):
            if player <= address < player + 0x1000:
                writes.append({"offset": address - player,
                               "size": size, "value": value})

        def on_code(machine, address, _size, _user):
            if address == 0x0046EB30:
                factory["entered"] = True
                factory["action"] = struct.unpack("<I", machine.mem_read(
                    machine.reg_read(UC_X86_REG_ESP) + 4, 4))[0]
                factory["player_hp"] = struct.unpack("<H", machine.mem_read(
                    player + 0x184, 2))[0]
                factory["timer"] = struct.unpack("<H", machine.mem_read(
                    player + 0x884, 2))[0]
                factory["aux_timer"] = struct.unpack("<H", machine.mem_read(
                    player + 0x886, 2))[0]
                machine.emu_stop()

        uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
        uc.hook_add(UC_HOOK_CODE, on_code)
        uc.mem_write(stack + 0xEFF0, struct.pack("<I", stop))
        uc.reg_write(UC_X86_REG_ESI, player)
        uc.reg_write(UC_X86_REG_EAX, 0)
        uc.reg_write(UC_X86_REG_EBX, 0)
        uc.reg_write(UC_X86_REG_ECX, 0)
        uc.reg_write(UC_X86_REG_EBP, 0)
        uc.reg_write(UC_X86_REG_ESP, stack + 0xEFF0)
        uc.reg_write(UC_X86_REG_EIP, 0x004907BA)
        uc.emu_start(0x004907BA, stop, count=1000)
        self.assertTrue(factory["entered"])
        self.assertEqual(factory["action"], 0x4B1)
        self.assertEqual(factory["player_hp"], 1000)
        self.assertEqual(factory["timer"], 0)
        self.assertEqual(factory["aux_timer"], 0)
        written_offsets = {row["offset"] for row in writes}
        self.assertTrue({0x884, 0x4AA, 0x4BA, 0x188, 0x820}.issubset(written_offsets))

    def test_player_input_type_is_copied_and_dispatched_separately(self):
        exe = ROOT / "original/th123.exe"
        pe = pefile.PE(str(exe), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        ctor = {ins.op_str for ins in md.disasm(
            pe.get_data(0x46C539 - base, 0x35), 0x46C539)}
        self.assertIn("eax, dword ptr [ebp + 0x1c]", ctor)
        self.assertIn("cl, byte ptr [ebp + 6]", ctor)
        self.assertIn("byte ptr [esi + 0x7cc], cl", ctor)
        self.assertIn("byte ptr [esi + 0x7cc], bl", ctor)
        dispatcher = {ins.op_str for ins in md.disasm(
            pe.get_data(0x46D7D0 - base, 0x28), 0x46D7D0)}
        self.assertIn("eax, byte ptr [esi + 0x7cc]", dispatcher)
        self.assertIn("eax, 2", dispatcher)
        self.assertIn("edx, dword ptr [eax + 0x5c]", dispatcher)
        self.assertIn("edx, dword ptr [eax + 0x58]", dispatcher)

    def test_input_setup_assigns_distinct_left_and_right_player_slots(self):
        """The 43dec0 setup uses PlayerInfo+6 as the input-side selector."""
        exe = ROOT / "original/th123.exe"
        pe = pefile.PE(str(exe), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        setup = list(md.disasm(pe.get_data(0x43DEC0 - base, 0x50), 0x43DEC0))
        assignments = {
            ins.address: (ins.mnemonic, ins.op_str)
            for ins in setup if ins.address in (0x43DECE, 0x43DEEE)
        }
        self.assertEqual(assignments[0x43DECE],
                         ("mov", "byte ptr [0x899d16], al"))
        self.assertEqual(assignments[0x43DEEE],
                         ("mov", "byte ptr [0x899d36], 2"))
        self.assertIn(("mov", "byte ptr [0x899d14], bl"),
                      {(ins.mnemonic, ins.op_str) for ins in setup})
        self.assertIn(("mov", "byte ptr [0x899d34], al"),
                      {(ins.mnemonic, ins.op_str) for ins in setup})
        # PlayerInfo starts at 0x899d10 (left) and 0x899d30 (right): +4 is
        # isRight, while +6 is independently populated with input slot 1/2.
        self.assertEqual(0x899D16 - 0x899D10, 6)
        self.assertEqual(0x899D36 - 0x899D30, 6)

    def test_game_data_player_creation_queue_feeds_character_factory(self):
        exe = ROOT / "original/th123.exe"
        pe = pefile.PE(str(exe), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        md.detail = True
        queue_drain = list(md.disasm(
            pe.get_data(0x46E5C0 - base, 0x90), 0x46E5C0))
        drain_calls = {ins.op_str for ins in queue_drain
                       if ins.mnemonic == "call"}
        self.assertIn("0x46da40", drain_calls)
        player_factory = list(md.disasm(
            pe.get_data(0x46DA40 - base, 0x520), 0x46DA40))
        self.assertTrue(any(ins.mnemonic == "mov" and
                            ins.op_str == "dword ptr [ebx + eax*4 + 0x28], esi"
                            for ins in player_factory))

        creator = list(md.disasm(pe.get_data(0x46EAD0 - base, 0x60), 0x46EAD0))
        self.assertIn("0x46da40", {ins.op_str for ins in creator
                                   if ins.mnemonic == "call"})
        worker = {ins.op_str for ins in md.disasm(
            pe.get_data(0x46E6D0 - base, 0x25), 0x46E6D0)
                  if ins.mnemonic == "call"}
        self.assertIn("0x46e5c0", worker)

        game_data = (ROOT / "local/SokuLib/src/GameData.hpp").read_text(
            encoding="utf-8")
        self.assertIn("List<std::pair<int, PlayerInfo*>> createQueue;", game_data)
        self.assertIn("Player* players[4];", game_data)
        self.assertIn("// 0x28", game_data)

    def test_saved_character_unlock_table_excludes_random_and_namazu(self):
        exe = ROOT / "original/th123.exe"
        pe = pefile.PE(str(exe), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        md.detail = True
        unlock = list(md.disasm(
            pe.get_data(0x42EE80 - base, 0x28), 0x42EE80))
        self.assertIn(("cmp", "eax, 0x14"),
                      {(ins.mnemonic, ins.op_str) for ins in unlock})
        self.assertIn(("jge", "0x42eea4"),
                      {(ins.mnemonic, ins.op_str) for ins in unlock})
        self.assertIn(("mov", "byte ptr [eax + esi + 0x30], 1"),
                      {(ins.mnemonic, ins.op_str) for ins in unlock})
        factory = {(ins.mnemonic, ins.op_str) for ins in md.disasm(
            pe.get_data(0x46DE3E - base, 0x20), 0x46DE3E)}
        self.assertIn(("call", "0x42ee80"), factory)

        character = (ROOT / "local/SokuLib/src/Character.hpp").read_text(
            encoding="utf-8")
        game_data = (ROOT / "local/SokuLib/src/GameData.hpp").read_text(
            encoding="utf-8")
        self.assertIn("/* 20 */ CHARACTER_RANDOM", character)
        self.assertIn("/* 21 */ CHARACTER_NAMAZU", character)
        self.assertIn("bool enabledCharacters[20];", game_data)


if __name__ == "__main__":
    unittest.main()
