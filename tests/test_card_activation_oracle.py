import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "x86_card_activation_oracle.py"
SPEC = importlib.util.spec_from_file_location("x86_card_activation_oracle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CardActivationOracleTests(unittest.TestCase):
    def test_original_card_gate_checks_hand_cost_and_weather_adjustments(self):
        report = MODULE.analyze(ROOT / "original/th123.exe")
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["cases"]), 8)
        cases = {row["case"]: row for row in report["cases"]}
        self.assertFalse(cases["empty_hand"]["can_activate"])
        self.assertFalse(cases["hand_count_below_slot"]["can_activate"])
        self.assertFalse(cases["cost_exceeds_hand"]["can_activate"])
        self.assertTrue(cases["cost_exactly_met"]["can_activate"])
        self.assertTrue(cases["weather_2_reduces_cost"]["can_activate"])
        self.assertFalse(cases["weather_2_still_requires_one"]["can_activate"])
        self.assertTrue(cases["weather_11_allows_one_card"]["can_activate"])
        self.assertEqual(cases["slot_1_uses_second_hand_card"]["deque_indices"], [1, 1])
        self.assertTrue(all(row["stack_balanced"] for row in cases.values()))


if __name__ == "__main__":
    unittest.main()
