from pathlib import Path
import tempfile
import unittest

from tools.x87_mode_probe import (ROOT, EXPECTED_SHA256, classify, cw_fields,
                                 load_pe, report, trace_word)


class HelpersTest(unittest.TestCase):
    def test_control_word_fields(self):
        self.assertEqual(cw_fields(0x7F)["significand_bits"], 24)
        self.assertEqual(cw_fields(0x27F)["significand_bits"], 53)
        self.assertEqual(cw_fields(0x37F)["significand_bits"], 64)
        self.assertEqual(cw_fields(0xC7F)["rc"], 3)
        self.assertIsNone(cw_fields(0x17F)["significand_bits"])

    def test_rejects_wrong_hash_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong.exe"
            path.write_bytes(b"not the reference")
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                load_pe(path)

    def test_local_slice_distinguishes_modified_and_saved_slots(self):
        rows = [(1, 4, "fnstcw", "word ptr [esp + 4]"),
                (5, 4, "movzx", "eax, word ptr [esp + 4]"),
                (9, 5, "or", "eax, 0xc00"),
                (14, 4, "mov", "dword ptr [esp + 8], eax"),
                (18, 4, "fldcw", "word ptr [esp + 8]"),
                (22, 4, "fldcw", "word ptr [esp + 4]")]
        self.assertEqual(classify(trace_word(rows, 4, rows[4][3])),
                         "round_toward_zero_pc_preserved")
        self.assertEqual(classify(trace_word(rows, 5, rows[5][3])), "restore_saved")

    def test_unknown_write_is_not_treated_as_saved_cw(self):
        rows = [(1, 4, "fnstcw", "word ptr [esp]"),
                (5, 4, "fistp", "dword ptr [esp]"),
                (9, 4, "fldcw", "word ptr [esp]")]
        self.assertEqual(classify(trace_word(rows, 2, rows[2][3])), "unresolved")


@unittest.skipUnless((ROOT / "original/th123.exe").is_file(), "falta el PE local")
class ReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = report()

    def test_all_device_fallbacks_and_window_modes(self):
        for case in self.result["device_cases"]:
            with self.subTest(failures=case["failures"], argument=case["boolean_argument"]):
                calls = case["calls"]
                self.assertEqual([row["call_va"] for row in calls],
                                 [0x415028, 0x415049, 0x41506B][:len(calls)])
                self.assertEqual([row["behavior_flags"] for row in calls],
                                 [0x44, 0x24, 0x24][:len(calls)])
                self.assertEqual([row["device_type"] for row in calls],
                                 [1, 1, 2][:len(calls)])
                self.assertTrue(all(not row["fpu_preserve"] for row in calls))
                self.assertTrue(all(row["windowed"] == 1
                                    for row in calls))

    def test_game_controlfp_call_sets_rounding_up_not_precision(self):
        for case in self.result["controlfp_cases"]:
            self.assertEqual(case["errno_result"], 0)
            if case["mask"] == 0x300:
                self.assertEqual(case["final_cw"] & 0xF00,
                                 (case["initial_cw"] & 0x300) | 0x800)
            elif case["mask"] == 0x30000:
                self.assertEqual(case["final_cw"] & 0xF00, 0)
            else:
                self.assertEqual(case["final_cw"], case["initial_cw"])

    def test_import_and_global_provenance(self):
        pe = load_pe(ROOT / "original/th123.exe")
        iat = next(i.address for d in pe.DIRECTORY_ENTRY_IMPORT
                   for i in d.imports if i.name == b"Direct3DCreate9")
        self.assertEqual(iat, 0x8572A0)
        self.assertEqual(pe.get_data(0x81F6B8 - 0x400000, 6), bytes.fromhex("ff25a0728500"))
        self.assertEqual(pe.get_data(0x414EF7 - 0x400000, 5), bytes.fromhex("a32c0e8a00"))
        self.assertEqual(self.result["sha256"], EXPECTED_SHA256)
        self.assertFalse(self.result["d3d_runtime_control_word_measured"])

    def test_census_has_every_linear_fldcw_in_stable_order(self):
        rows = self.result["fldcw"]
        self.assertEqual(len(rows), 290)
        self.assertEqual(sum(self.result["classification_counts"].values()), 290)
        self.assertEqual([r["va"] for r in rows], sorted(r["va"] for r in rows))
        by_va = {r["va"]: r for r in rows}
        self.assertEqual(by_va[0x4201F9]["classification"], "round_toward_zero_pc_preserved")
        self.assertEqual(by_va[0x420214]["classification"], "restore_saved")
        self.assertEqual(by_va[0x8215B7]["source"]["word"], 0x27F)
        self.assertEqual(by_va[0x781D34]["classification"], "unresolved")

    def test_crt_control_references_are_not_omitted(self):
        refs = {(r["va"], r["target_va"]) for r in self.result["crt_control_references"]}
        self.assertIn((0x407E02, 0x82198E), refs)
        self.assertIn((0x8219B3, 0x82C962), refs)
        self.assertIn((0x821AD4, 0x82D67C), refs)


if __name__ == "__main__":
    unittest.main()
