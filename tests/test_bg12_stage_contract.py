import hashlib
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


class Bg12StageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = (ROOT / "original" / "th123.exe").read_bytes()
        cls.digest = hashlib.sha256(cls.exe).hexdigest()
        cls.pe = pefile.PE(data=cls.exe, fast_load=True)
        cls.image_base = cls.pe.OPTIONAL_HEADER.ImageBase
        cls.disasm = Cs(CS_ARCH_X86, CS_MODE_32)
        cls.stage_export = (
            ROOT / "artifacts" / "kernel" / EXPECTED_SHA256 / "stage-layout"
        )

    @classmethod
    def bytes_at(cls, va, size):
        return cls.pe.get_data(va - cls.image_base, size)

    @classmethod
    def instructions(cls, va, size):
        return list(cls.disasm.disasm(cls.bytes_at(va, size), va))

    def test_vtable_selects_the_expected_bg12_update_and_render_methods(self):
        self.assertEqual(self.digest, EXPECTED_SHA256)
        table = self.bytes_at(0x85AC9C, 24)
        entries = struct.unpack("<6I", table)
        self.assertEqual(entries[1], 0x4723B0)
        self.assertEqual(entries[4], 0x4723F0)

    def test_original_update_counter_speed_cases_are_preserved(self):
        ins = self.instructions(0x4723B0, 0x36)
        ops = [(i.mnemonic, i.op_str) for i in ins]
        self.assertIn(("cmp", "dword ptr [0x8971c0], 0xe"), ops)
        self.assertIn(("add", "dword ptr [ecx + 0x64], 1"), ops)
        self.assertIn(("cmp", "edx, 0xa"), ops)
        self.assertIn(("cmp", "edx, 0xb"), ops)
        self.assertIn(("add", "eax, 3"), ops)
        self.assertIn(("cmp", "edx, 0xd"), ops)
        self.assertIn(("add", "dword ptr [ecx + 0x64], 0xa"), ops)

    def test_bg12_constructor_and_grid_loader_match_local_ghidra_export(self):
        constructor = (self.stage_export / "00472640.c").read_text(encoding="utf-8")
        loader = (self.stage_export / "0046fe40.c").read_text(encoding="utf-8")
        manifest = (self.stage_export / "manifest.tsv").read_text(encoding="utf-8")
        self.assertIn(f"sha256\t{EXPECTED_SHA256}", manifest)
        self.assertIn("FUN_0046fe40(0xc,0x56,0);", constructor)
        self.assertIn("data/background/BG12/tori1.bmp", constructor)
        self.assertIn("data/background/BG12/tori2.bmp", constructor)
        self.assertIn("(uVar5 % 6) * -0x100 + 700", loader)
        self.assertIn("(param_3 - iStack_210) + 0x35c", loader)

    def test_torii_constructor_uses_bottom_center_local_pivot_at_origin(self):
        constructor = (self.stage_export / "00472640.c").read_text(encoding="utf-8")
        sprite_transform = (self.stage_export / "00406d30.c").read_text(encoding="utf-8")
        self.assertIn("FUN_00406c60(*puVar3,0,0,uStack_fc,uStack_100,uStack_fc >> 1,uStack_100);", constructor)
        self.assertIn("FUN_00406c60(*(undefined4 *)(iVar1 + 4),0,0,uStack_fc,uStack_100,uStack_fc >> 1,uStack_100);", constructor)
        self.assertIn("*(float *)(param_1 + 0x80) = -param_6;", sprite_transform)
        self.assertIn("*(float *)(param_1 + 0x84) = -param_7;", sprite_transform)
        self.assertIn("*(float *)(param_1 + 0x8c) = param_4 - param_6;", sprite_transform)
        self.assertIn("*(float *)(param_1 + 0x9c) = param_5 - param_7;", sprite_transform)

    def test_render_time_arguments_advance_by_two_and_offset_by_45_ticks(self):
        ins = self.instructions(0x4723F0, 0x24D)
        rendered = [(i.address, i.mnemonic, i.op_str) for i in ins]
        self.assertIn((0x47246C, "mov", "eax, dword ptr [esi + 0x64]"), rendered)
        self.assertIn((0x472479, "add", "eax, ebp"), rendered)
        self.assertIn((0x47247F, "add", "eax, eax"), rendered)
        self.assertTrue(any(i.mnemonic == "call" and i.op_str == "0x407180" for i in ins))
        self.assertIn((0x472616, "add", "ebp, 0x2d"), rendered)
        self.assertIn((0x472622, "cmp", "ebp, 0x5a"), rendered)

    def test_both_torii_receive_shared_base_translation_before_stage_offsets(self):
        render = self.instructions(0x4723F0, 0x260)
        ops = [(i.address, i.mnemonic, i.op_str) for i in render]
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85AC4C, 4))[0], 492.0)
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85AC50, 4))[0], -401.0)
        self.assertIn((0x47252D, "add", "ecx, ebx"), ops)
        self.assertIn((0x472533, "fld", "dword ptr [0x85ac4c]"), ops)
        self.assertIn((0x47253C, "call", "0x406ee0"), ops)
        self.assertIn((0x472578, "add", "ecx, ebx"), ops)
        self.assertIn((0x472584, "call", "0x406ee0"), ops)
        helper = (self.stage_export / "00406ee0.c").read_text(encoding="utf-8")
        self.assertIn("*(float *)(param_1 + 0xb0) = param_2 + *(float *)(param_1 + 0xb0);", helper)
        source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        self.assertIn("*x = 492.0f", source)
        self.assertIn("*y = -401.0f", source)

    def test_bg12_layout_layer_retains_base_tiles_for_the_composition_map(self):
        source = (ROOT / "legacy" / "src" / "vita_main.c").read_text(encoding="utf-8")
        self.assertIn('if(stage_layer&&strcmp(stage_names[stage_index],"bg12")&&strcmp(stage_names[stage_index],"bg02"))continue;', source)


if __name__ == "__main__":
    unittest.main()
