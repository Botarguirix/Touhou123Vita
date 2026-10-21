import hashlib
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))
import pefile

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


class Bg33PeVtableOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = ROOT / "original/th123.exe"
        cls.data = cls.exe.read_bytes()
        if hashlib.sha256(cls.data).hexdigest() != EXPECTED_SHA256:
            raise unittest.SkipTest("local reference PE is absent or has a different hash")
        cls.pe = pefile.PE(data=cls.data, fast_load=True)
        cls.stage_export = ROOT / "artifacts/kernel" / EXPECTED_SHA256 / "stage-layout"

    def dword(self, va):
        offset = self.pe.get_offset_from_rva(va - self.pe.OPTIONAL_HEADER.ImageBase)
        return int.from_bytes(self.data[offset:offset + 4], "little")

    def test_bg33_renderer_30_slot_loop_and_phase_are_present_in_the_pe(self):
        offset = self.pe.get_offset_from_rva(0x00473620 - self.pe.OPTIONAL_HEADER.ImageBase)
        code = self.data[offset:offset + 0x16f]
        # 30 draw iterations, six sources per 256-tick phase, 24-source wrap,
        # a +0x400 vertical wrap, sprite stride 0xe8, and +0x44/+0x48 origin.
        for opcode in (
            bytes.fromhex("83 fb 1e"),
            bytes.fromhex("99 81 e2 ff 00 00 00"),
            bytes.fromhex("8d 04 40 8d 3c 43"),
            bytes.fromhex("83 ff 18"),
            bytes.fromhex("81 44 24 0c 00 04 00 00"),
            bytes.fromhex("69 ff e8 00 00 00"),
            bytes.fromhex("d8 46 48"),
            bytes.fromhex("d9 46 44"),
        ):
            self.assertIn(opcode, code)

    def test_bg33_constructor_allocates_24_grid_sprites_and_two_auxiliaries(self):
        offset = self.pe.get_offset_from_rva(0x00473AF0 - self.pe.OPTIONAL_HEADER.ImageBase)
        code = self.data[offset:offset + 0x800]
        self.assertIn(bytes.fromhex("6a 18"), code)  # 24 base slots
        self.assertIn(bytes.fromhex("3b f1 72 05"), code)  # grid loop bound check
        strings = (
            b"data/background/BG33/0000[%02d][%02d].bmp\\0",
            b"data/background/BG33/0001.bmp\\0",
            b"data/background/BG33/0002.bmp\\0",
        )
        for value in strings:
            self.assertIn(value.replace(b"\\0", b"\0"), self.data)
        base_ctor = (self.stage_export / "0046f9c0.c").read_text(encoding="utf-8")
        self.assertIn("param_1[0x11] = 0;", base_ctor)  # Background+0x44 starts at zero
        self.assertIn("param_1[0x12] = 0;", base_ctor)  # Background+0x48 starts at zero

    def test_bg33_draw_pipeline_applies_object_time_stage_and_camera_transforms(self):
        render = self.data[self.pe.get_offset_from_rva(0x00473620 - self.pe.OPTIONAL_HEADER.ImageBase):]
        render = render[:0x16f]
        self.assertIn(bytes.fromhex("e8 c7 37 f9 ff"), render)  # object update
        self.assertIn(bytes.fromhex("d8 46 48 d9 5c 24 18"), render)  # local y + stage y
        self.assertIn(bytes.fromhex("d9 46 44 d9 1c 24"), render)  # stage x argument
        self.assertIn(bytes.fromhex("e8 de 37 f9 ff"), render)  # sprite-local translation
        self.assertIn(bytes.fromhex("e8 27 5d fb ff"), render)  # viewport/camera transform
        camera = self.data[self.pe.get_offset_from_rva(0x00429440 - self.pe.OPTIONAL_HEADER.ImageBase):]
        camera = camera[:0x70]
        self.assertIn(bytes.fromhex("d8 46 18"), camera)  # camera x offset
        self.assertIn(bytes.fromhex("d8 46 1c"), camera)  # camera y offset
        self.assertIn(bytes.fromhex("d9 46 30"), camera)  # viewport x offset
        self.assertIn(bytes.fromhex("d9 46 34"), camera)  # viewport y offset
        self.assertIn(bytes.fromhex("d9 46 14"), camera)  # sprite scale read

    def test_ported_viewport_translation_constants_match_the_pinned_pe(self):
        expected = {
            0x8581D0: 320.0,  # horizontal resolution constant
            0x8581C8: 420.0,  # vertical resolution constant
            0x8579A0: 640.0,  # viewport x center
        }
        for address, value in expected.items():
            offset = self.pe.get_offset_from_rva(address - self.pe.OPTIONAL_HEADER.ImageBase)
            self.assertEqual(struct.unpack('<d', self.data[offset:offset + 8])[0], value)
        source = (ROOT / 'legacy' / 'src' / 'stage.c').read_text(encoding='utf-8')
        self.assertIn('320.0f / zoom', source)
        self.assertIn('640.0f - (viewport_x + camera_x)', source)
        self.assertIn('420.0f / zoom - (viewport_y + camera_y)', source)

    def test_bg33_background_is_integrated_into_live_fight_and_vita3k_gate(self):
        source = (ROOT / "legacy" / "src" / "vita_main.c").read_text(encoding="utf-8")
        runner = (ROOT / "tools" / "vita3k-test.ps1").read_text(encoding="utf-8")
        prepare = source.split("static void prepare_battle_bg33", 1)[1].split(
            "static void stage_load_extras", 1)[0]
        draw = source.split("static void draw_battle_bg33", 1)[1].split(
            "static void stage_load_extras", 1)[0]
        self.assertIn('data/background/bg33/0000[%02u][%02u].cv2', prepare)
        self.assertIn("battle_bg33_assets[row][col]=soft2d_load_dat", prepare)
        self.assertIn("battle_bg33_tiles==24u", prepare)
        self.assertIn("t123_bg33_render_slot(battle_bg33_counter,slot", draw)
        self.assertIn("g->camera.zoom,g->camera.x", draw)
        self.assertIn("t123_bg33_project_slot_quad", draw)
        self.assertIn("battle_bg33_updates++", source)
        self.assertIn("draw_battle_bg33(g)", source)
        for field in ("battle_bg33_tiles", "battle_bg33_draws",
                      "battle_bg33_updates", "battle_bg33_slots"):
            self.assertIn(f"$result.{field}", runner)

    def test_bg33_update_and_render_slots_match_the_port_contract(self):
        self.assertEqual(self.dword(0x85AE44 + 1 * 4), 0x00473610)
        self.assertEqual(self.dword(0x85AE44 + 4 * 4), 0x00473620)
        update_offset = self.pe.get_offset_from_rva(0x00473610 - self.pe.OPTIONAL_HEADER.ImageBase)
        update = self.data[update_offset:update_offset + 15]
        self.assertEqual(update, bytes.fromhex("8b416483c00125ff030000894164c3"))


if __name__ == "__main__":
    unittest.main()
