import unittest
from pathlib import Path

from tools.x86_suika_dash_sequence_probe import probe


class SuikaDashSequenceProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dat_dir = Path("original")
        if not (cls.dat_dir / "th123.exe").is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")

    def test_original_418_setter_starts_at_zero_and_update_reaches_active_sequence(self):
        report = probe(self.dat_dir)

        self.assertEqual(report["action"], 418)
        self.assertIsNone(report["setter"]["error"])
        self.assertEqual(report["setter"]["sequence"], 0)
        self.assertEqual(len(report["effective_sequences"]), 6)
        self.assertEqual(report["update"]["stop_reason"], "returned-to-stop")
        self.assertEqual(report["update"]["ticks_completed"], 40)
        self.assertEqual(report["active_attack_ticks"][0], 16)

        tick15 = report["update"]["ticks"][14]
        tick16 = report["update"]["ticks"][15]
        self.assertEqual((tick15["sequence"], tick15["pose"], tick15["frame_damage"]), (1, 3, 0))
        self.assertEqual((tick16["sequence"], tick16["pose"], tick16["frame_damage"],
                          tick16["frame_attack_box_count"]), (2, 0, 900, 1))
        gate = next(row for row in report["update"]["landing_gate_observations"]
                    if row["tick"] == 27)
        self.assertEqual(gate["return_address"], "0x5f4a5d")
        self.assertEqual(gate["vertical_velocity"], -0.5)
        self.assertTrue(gate["returns_true"])
        transition = next(row for row in report["update"]["sequence_setter_calls"]
                          if row["tick"] == 27)
        self.assertEqual((transition["caller_return"], transition["current_sequence"],
                          transition["requested_sequence"]), ("0x603646", 2, 5))
        self.assertIn("no natural dash/input producer", report["scope"])


if __name__ == "__main__":
    unittest.main()
