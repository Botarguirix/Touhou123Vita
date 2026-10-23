"""Contracts recovered from executed original font setup and bitmap adapters."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("find_font_requests", ROOT / "tools/find_font_requests.py")
font = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(font)
EXE = ROOT / "original/th123.exe"


class PureFontMetadataTests(unittest.TestCase):
    def test_cv_text_decryption_known_vector_and_roundtrip(self):
        self.assertEqual(font.decode_cv_text(bytes.fromhex("cad04097")), b"A,B\n")
        data = bytes(range(256)) * 3
        self.assertEqual(font.decode_cv_text(font.decode_cv_text(data)), data)

    def test_encoding_identifies_japanese_cp932_without_publishing_text(self):
        metadata = font.encoding_metadata(bytes.fromhex("82a082a2"))
        self.assertEqual(metadata["cp932"], {"valid": True, "characters": 2, "japanese_characters": 2})
        self.assertFalse(metadata["utf-8"]["valid"])
        self.assertNotIn("text", metadata)

    def test_rejects_other_executable_before_pe_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "other.exe"
            bad.write_bytes(b"not the user reference")
            with self.assertRaisesRegex(ValueError, "reference SHA256 mismatch"):
                font.load_pe(bad)

    def test_cli_mismatch_fails_without_writing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            bad, out = Path(directory) / "bad.exe", Path(directory) / "report.json"
            bad.write_bytes(b"MZ wrong PE")
            result = subprocess.run([sys.executable, str(ROOT / "tools/find_font_requests.py"),
                                     "--exe", str(bad), "--no-dat", "--output", str(out)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("reference SHA256 mismatch", result.stderr)
            self.assertFalse(out.exists())


@unittest.skipUnless(EXE.is_file(), "local original/th123.exe is absent")
class OriginalFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = font.analyze(EXE)
        cls.pe, _ = font.load_pe(EXE)

    def test_all_gdi_import_sites_are_accounted_for(self):
        sites = self.report["static"]["import_sites"]
        self.assertEqual(sites["CreateFontA"], [{"address": "0x00411c75", "kind": "call"}])
        self.assertEqual([row["address"] for row in sites["GetGlyphOutlineA"]],
                         ["0x00411e53", "0x00411f1a", "0x004120c2", "0x0041213b"])
        self.assertEqual(len(self.report["static"]["set_indirect_calls"]), 14)
        self.assertEqual(len(self.report["static"]["create_text_texture_calls"]), 19)

    def test_create_font_keeps_dynamic_height_weight_italic_and_fixed_ansi_flags(self):
        for row, request in zip(self.report["create_font_requests"], [(14, 300, 0), (24, 400, 0), (-17, 700, 1)]):
            self.assertEqual((row["height"], row["weight"], row["italic"]), request)
            self.assertEqual((row["charset"], row["out_precision"], row["clip_precision"], row["quality"], row["pitch_and_family"]),
                             (128, 4, 0, 2, 0x31))
            self.assertEqual((row["width"], row["escapement"], row["orientation"], row["underline"], row["strikeout"]), (0, 0, 0, 0, 0))
        self.assertEqual(self.report["default_face"]["name"], "ＭＳ ゴシック")

    def test_scene_descriptors_and_name_length_shrinking(self):
        rows = self.report["descriptor_probes"]
        plain = [row for row in rows if row["context"] != "profile_name_shrink"]
        self.assertEqual([(r["height_measured"], r["weight_measured"]) for r in plain], [(14, 300)] * 6 + [(24, 400)])
        shrunk = [row for row in rows if row["context"] == "profile_name_shrink"]
        self.assertEqual([r["height_measured"] for r in shrunk], [14, 12, 6, 14, 12, 6])
        # Odd byte-length differences distinguish truncation from floor.
        for row in shrunk:
            threshold = 16 if row["callsite"] == "0x00453cd1" else 15
            self.assertEqual(row["height_measured"], 14 - max(int((row["byte_length"] - threshold) / 2), 0))

    def test_script_can_override_face_size_and_spacing(self):
        row = self.report["script_font_probe"]
        self.assertEqual((row["face"], row["height"], row["weight"], row["char_space_x"], row["char_space_y"]),
                         ("FixtureFace", 18, 400, 0, 2))

    def test_ruby_height_is_one_third_not_half(self):
        rows = self.report["ruby_font_probes"]
        self.assertEqual([r["base_ruby_height"] for r in rows], [4, 8, 5])
        self.assertEqual([r["weight"] for r in rows], [400, 400, 400])

    def test_get_glyph_uses_gray4_identity_and_two_stage_buffer_query(self):
        for row in self.report["glyph_bitmap_probes"]:
            calls = row["calls"]
            self.assertEqual([(c["buffer_size"], c["buffer_is_null"]) for c in calls], [(0, True), (8, False)])
            for call in calls:
                self.assertEqual(call["format"], 5)
                self.assertEqual(call["format_name"], "GGO_GRAY4_BITMAP")
                self.assertEqual(call["matrix_fixed16_16"], [65536, 0, 0, 65536])
                self.assertEqual(call["character"], 46 if row["mode"] == "period" else 0x82A0)

    def test_original_copy_scales_17_coverage_levels_and_skips_padding(self):
        for row in self.report["glyph_bitmap_probes"]:
            pixels = row["output_pixels"]
            x0 = 3 if row["mode"] == "period" else 0
            self.assertEqual([(p["x"], p["y"]) for p in pixels],
                             [(x0, 6), (x0 + 1, 6), (x0 + 2, 6), (x0, 7), (x0 + 1, 7), (x0 + 2, 7)])
            self.assertEqual([p["argb"] for p in pixels],
                             ["0x00123456", "0x7f123456", "0xff123456", "0xff123456", "0x0f123456", "0xef123456"])
            self.assertEqual(row["cursor_x"], 0 if row["mode"] == "period" else 4)

    def test_dbcs_byte_order_and_single_byte_sign_extension(self):
        self.assertEqual(self.report["dbcs_probes"], [
            {"input_hex": "41", "gdi_character": 0x41, "bytes_consumed": 1},
            {"input_hex": "82a0", "gdi_character": 0x82A0, "bytes_consumed": 2},
            {"input_hex": "b1", "gdi_character": 0xFFFFFFB1, "bytes_consumed": 1},
        ])
        for value, consumed in [(0x80, 1), (0x81, 2), (0x9F, 2), (0xA0, 1), (0xDF, 1), (0xE0, 2), (0xFE, 2), (0xFF, 1)]:
            with self.subTest(value=value):
                self.assertEqual(font.dbcs_probe(self.pe, bytes([value, 0x41]))["bytes_consumed"], consumed)

    def test_text_comes_from_both_dat_paths_and_embedded_pe_literal(self):
        refs = self.report["static"]["text_resource_path_refs"]
        self.assertTrue(any(r["path"] == "data/csv/%s/spellcard.csv" for r in refs))
        self.assertTrue(any(r["path"] == "data/scenario/%s/%03d.txt" for r in refs))
        row = self.report["embedded_text_probe"]
        self.assertEqual(row["text_address"], "0x00859338")
        self.assertEqual(row["texture_size"], [256, 256])
        self.assertTrue(row["text_metadata"]["cp932"]["valid"])
        self.assertEqual(row["text_metadata"]["cp932"]["characters"], 35)
        self.assertFalse(row["text_metadata"]["utf-8"]["valid"])

    def test_text_texture_uses_argb8888_and_one_managed_level(self):
        row = self.report["text_texture_probe"]
        self.assertEqual((row["format"], row["format_name"]), (21, "D3DFMT_A8R8G8B8"))
        self.assertEqual((row["levels"], row["usage"], row["pool"]), (1, 0, 1))
        self.assertEqual((row["width_seeded"], row["height_seeded"]), (256, 128))

    def test_report_is_deterministic(self):
        again = font.analyze(EXE)
        self.assertEqual(json.dumps(self.report, sort_keys=True), json.dumps(again, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
