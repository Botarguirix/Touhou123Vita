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


class Bg02StageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = (ROOT / "original" / "th123.exe").read_bytes()
        cls.digest = hashlib.sha256(cls.exe).hexdigest()
        cls.pe = pefile.PE(data=cls.exe, fast_load=True)
        cls.base = cls.pe.OPTIONAL_HEADER.ImageBase
        cls.disasm = Cs(CS_ARCH_X86, CS_MODE_32)
        cls.export = ROOT / "artifacts" / "kernel" / EXPECTED_SHA256 / "stage-layout"

    @classmethod
    def instructions(cls, va, size):
        return list(cls.disasm.disasm(cls.pe.get_data(va - cls.base, size), va))

    def test_bg02_vtable_resolves_update_and_render(self):
        self.assertEqual(self.digest, EXPECTED_SHA256)
        table = self.pe.get_data(0x85ABAC - self.base, 24)
        slots = struct.unpack("<6I", table)
        self.assertEqual(slots[1], 0x473F40)
        self.assertEqual(slots[4], 0x4716D0)

    def test_update_is_one_counter_tick_per_callback(self):
        ins = self.instructions(0x473F40, 5)
        self.assertEqual([(i.mnemonic, i.op_str) for i in ins], [
            ("add", "dword ptr [ecx + 0x64], 1"), ("ret", "")
        ])

    def test_renderer_selects_three_adjacent_sprites_per_16_frame_cycle(self):
        ins = self.instructions(0x4716D0, 0x60)
        ops = [(i.mnemonic, i.op_str) for i in ins]
        self.assertIn(("mov", "eax, 0x2aaaaaab"), ops)
        self.assertIn(("and", "eax, 0x8000000f"), ops)
        self.assertIn(("lea", "ebp, [eax + eax*2]"), ops)
        constructor = (self.export / "00471c50.c").read_text(encoding="utf-8")
        self.assertIn("data/background/BG02/left/a%02d.bmp", constructor)
        self.assertIn("data/background/BG02/center/b%02d.bmp", constructor)
        self.assertIn("data/background/BG02/right/c%02d.bmp", constructor)
        self.assertIn("iStack_138 = iStack_138 + 0xc", constructor)

    def test_renderer_uses_constructor_derived_segment_offsets(self):
        ins = self.instructions(0x4716D0, 0x580)
        operands = [i.op_str for i in ins]
        self.assertIn("dword ptr [0x85ab2c]", operands)
        self.assertIn("dword ptr [0x85ab24]", operands)
        self.assertIn("dword ptr [0x85ab30]", operands)
        self.assertIn("dword ptr [esi + 0x44]", operands)
        self.assertIn("dword ptr [esi + 0x48]", operands)
        self.assertEqual(struct.unpack("<f", self.pe.get_data(0x85AB24 - self.base, 4))[0], 312.0)
        self.assertEqual(struct.unpack("<f", self.pe.get_data(0x85AB2C - self.base, 4))[0], -332.0)
        self.assertEqual(struct.unpack("<f", self.pe.get_data(0x85AB30 - self.base, 4))[0], -472.0)

    def test_ported_segment_offsets_match_original_renderer(self):
        source = (ROOT / "src" / "stage.c").read_text(encoding="utf-8")
        for offset in ("{-332.0f, -472.0f}", "{0.0f, 0.0f}", "{312.0f, -472.0f}"):
            self.assertIn(offset, source)
        header = (ROOT / "include" / "t123" / "stage.h").read_text(encoding="utf-8")
        self.assertIn("t123_bg02_sprite_offset", header)

    def test_ported_frame_and_sprite_index_helpers_match_pe_cycle(self):
        source = (ROOT / "src" / "stage.c").read_text(encoding="utf-8")
        self.assertIn("return (counter / 3u) % 16u;", source)
        self.assertIn("t123_bg02_frame(counter) * 3u + segment", source)
        header = (ROOT / "include" / "t123" / "stage.h").read_text(encoding="utf-8")
        self.assertIn("t123_bg02_sprite_index", header)


if __name__ == "__main__":
    unittest.main()
