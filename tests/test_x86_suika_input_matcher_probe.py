import unittest

from tools.x86_suika_input_matcher_probe import run


class SuikaInputMatcherProbeTests(unittest.TestCase):
    def test_original_updates_form_nrnr_in_abi_correct_deque(self):
        report = run()
        self.assertTrue(report["passed"])
        self.assertEqual(report["matcher_calls"], 4)
        self.assertEqual([row["sample"] for row in report["trace"]],
                         [0x00, 0x02, 0x00, 0x02])
        self.assertEqual([row["size"] for row in report["trace"]], [90] * 4)
        self.assertEqual(report["final_motion_bits"] & 1, 1)
        handler = report["suika_handler"]
        self.assertEqual(handler["entry"], "0x609dc0")
        self.assertEqual(handler["seeded_precondition_action"], 200)
        self.assertTrue(handler["branch_reached"])
        self.assertEqual(handler["current_key_input"], [1, 0])
        self.assertEqual(handler["setter_actions"], [418])
        self.assertEqual(handler["action_after"], 418)
        self.assertTrue(handler["cleanup_entry_reached"])


if __name__ == "__main__":
    unittest.main()
