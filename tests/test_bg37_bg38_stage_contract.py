import hashlib
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))
import pefile

PE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


class Bg37Bg38StageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = (ROOT / "original" / "th123.exe").read_bytes()
        if hashlib.sha256(data).hexdigest() != PE_SHA256:
            raise unittest.SkipTest("hash-pinned TH123 PE is unavailable")
        cls.pe = pefile.PE(data=data, fast_load=True)
        cls.image_base = cls.pe.OPTIONAL_HEADER.ImageBase

    def bytes_at(self, va, size):
        return self.pe.get_data(va - self.image_base, size)

    def test_vtables_bind_the_expected_update_and_render_methods(self):
        bg37 = struct.unpack("<6I", self.bytes_at(0x85B138, 24))
        bg38 = struct.unpack("<6I", self.bytes_at(0x85B1BC, 24))
        self.assertEqual(bg37[1], 0x476260)
        self.assertEqual(bg37[4], 0x4762C0)
        self.assertEqual(bg38[1], 0x476C90)
        self.assertEqual(bg38[4], 0x476D60)

    def test_cloud_update_rates_wraps_and_bg37_counter_match_the_pe(self):
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85B004, 4))[0], -400.0)
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85B000, 4))[0], -300.0)
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85AFEC, 4))[0], -1200.0)
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85AFE8, 4))[0], 800.0)
        self.assertEqual(struct.unpack("<d", self.bytes_at(0x85AFE0, 8))[0], -800.0)
        self.assertEqual(struct.unpack("<d", self.bytes_at(0x8581B8, 8))[0], 1.5)
        self.assertEqual(struct.unpack("<d", self.bytes_at(0x8677C8, 8))[0], 1.0)

        bg37_update = self.bytes_at(0x476260, 0x60)
        bg38_update = self.bytes_at(0x476C90, 0x55)
        self.assertIn(bytes.fromhex("83 41 64 01"), bg37_update)
        self.assertNotIn(bytes.fromhex("83 41 64 01"), bg38_update)
        for update in (bg37_update, bg38_update):
            self.assertIn(bytes.fromhex("dc 25 b8 81 85 00"), update)
            self.assertIn(bytes.fromhex("dc 25 c8 77 86 00"), update)

        source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        bg37 = source.split("void t123_bg37_scroll_update", 1)[1].split("void t123_bg38_scroll_init", 1)[0]
        bg38 = source.split("void t123_bg38_scroll_update", 1)[1].split("void t123_stage_animation_update", 1)[0]
        for statement in ("scroll->counter += 1u", "scroll->tori1_x -= 1.5f",
                          "scroll->tori1_x < -1200.0f", "scroll->clowd_l_x -= 1.0f",
                          "scroll->clowd_l_x < -800.0f", "scroll->tori1_x = 800.0f",
                          "scroll->clowd_l_x = 800.0f"):
            self.assertIn(statement, bg37)
        for statement in ("scroll->clowd_l_x -= 1.5f", "scroll->clowd_l_x < -1200.0f",
                          "scroll->clowd_s_x -= 1.0f", "scroll->clowd_s_x < -800.0f",
                          "scroll->clowd_l_x = 800.0f", "scroll->clowd_s_x = 800.0f"):
            self.assertIn(statement, bg38)

    def test_renderers_map_offsets_to_constructor_ordered_assets(self):
        export = ROOT / "artifacts/kernel" / PE_SHA256 / "stage-layout"
        bg37_ctor = (export / "00476990.c").read_text(encoding="utf-8")
        bg38_ctor = (export / "00477310.c").read_text(encoding="utf-8")
        self.assertLess(bg37_ctor.index("BG37/tori1.bmp"), bg37_ctor.index("BG37/clowd_l.bmp"))
        self.assertLess(bg37_ctor.index("BG37/clowd_l.bmp"), bg37_ctor.index("BG37/clowd_s.bmp"))
        self.assertLess(bg38_ctor.index("BG38/clowd_l.bmp"), bg38_ctor.index("BG38/clowd_s.bmp"))

        bg37 = self.bytes_at(0x4762C0, 0x730)
        bg38 = self.bytes_at(0x476D60, 0x520)
        self.assertIn(bytes.fromhex("81 c1 d0 01 00 00"), bg37)  # slot 0 tori1
        self.assertIn(bytes.fromhex("d9 05 f4 af 85 00"), bg37)  # y=-750
        self.assertIn(bytes.fromhex("d9 46 68"), bg37)  # tori1 x
        self.assertIn(bytes.fromhex("81 c1 b8 02 00 00"), bg37)  # slot 1 clowd_l
        self.assertIn(bytes.fromhex("d9 05 f0 af 85 00"), bg37)  # y=-320
        self.assertIn(bytes.fromhex("d9 46 6c"), bg37)  # clowd_l x
        self.assertIn(bytes.fromhex("d9 05 4c ac 85 00"), bg37)  # fixed x=492
        self.assertIn(bytes.fromhex("d9 05 50 ac 85 00"), bg37)  # fixed y=-401
        for instruction in ("d9 46 68", "d9 46 6c", "d9 05 f4 af 85 00", "d9 05 f0 af 85 00"):
            self.assertIn(bytes.fromhex(instruction), bg38)

        source = (ROOT / "legacy" / "src" / "vita_main.c").read_text(encoding="utf-8")
        self.assertIn("stage_bg37_tori1_x", source)
        self.assertIn("stage_bg37_clowd_l_x", source)
        self.assertIn("unsigned asset_index=i", source)

    def test_vita_gallery_updates_and_reports_both_stage_clouds(self):
        source = (ROOT / "legacy" / "src" / "vita_main.c").read_text(encoding="utf-8")
        self.assertIn("t123_bg37_scroll_update(&stage_bg37_scroll)", source)
        self.assertIn("t123_bg38_scroll_update(&stage_bg38_scroll)", source)
        self.assertIn('!strcmp(stage_names[stage_index],"bg37")||!strcmp(stage_names[stage_index],"bg38")', source)
        self.assertIn("stage_bg37_tori1_x", source)
        self.assertIn("stage_bg38_cloud_s_x", source)


if __name__ == "__main__":
    unittest.main()
