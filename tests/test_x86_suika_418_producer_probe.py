import unittest
from pathlib import Path

from tools.x86_suika_418_producer_probe import probe


class Suika418ProducerProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = Path("original/th123.exe")
        if not cls.exe.is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")

    def test_original_motion_branch_requests_action_418_through_virtual_setter(self):
        report = probe(self.exe)
        self.assertEqual(report["action"], 418)
        self.assertEqual(report["producer_va"], "0x4b0ac2")
        self.assertEqual(report["action_push_va"], "0x4b0b04")
        self.assertEqual(report["virtual_setter_call_va"], "0x4b0b29")
        self.assertTrue(any("buffered horizontal KeyInput" in guard
                            for guard in report["observed_guards"]))
        self.assertIn("input update and matcher are not part", report["scope"])
        self.assertEqual(report["deque_layout"]["player_block_table"], "0x7b4")
        self.assertEqual(report["deque_layout"]["player_size"], "0x7c0")
        self.assertEqual(report["deque_layout"]["block_capacity"], 8)

    def test_original_action_418_guard_and_buffer_cleanup(self):
        from tools.x86_suika_418_producer_probe import dynamic_cases

        rows = dynamic_cases()
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["passed"] for row in rows))
        no_vertical_buffer = next(row for row in rows
                                  if row["case"] == "current_forward_without_vertical_buffer")
        self.assertEqual(no_vertical_buffer["setter_actions"], [418])
        self.assertEqual(no_vertical_buffer["buffered_after"], [0] * 8)


if __name__ == "__main__":
    unittest.main()
