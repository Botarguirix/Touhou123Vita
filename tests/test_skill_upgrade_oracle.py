import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "x86_skill_upgrade_oracle.py"
SPEC = importlib.util.spec_from_file_location("x86_skill_upgrade_oracle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SkillUpgradeOracleTests(unittest.TestCase):
    def test_original_helper_updates_all_reimu_skill_cards_and_level_boundaries(self):
        report = MODULE.analyze(
            ROOT / "original/th123.exe",
            ROOT / "artifacts/extracted/data/csv/reimu/spellcard.csv",
        )
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["card_cases"]), 12)
        for row in report["card_cases"]:
            index = row["skill_index"]
            self.assertEqual(row["skill_level_after"], 1)
            self.assertEqual(row["invalidated_skill_indices"],
                             [candidate for candidate in range(index % 4, 16, 4)
                              if candidate != index])
            self.assertEqual(row["spawn_actions"], [0x47, 0x83])
            self.assertEqual(row["consume_card_args"], [0, 0, 60])
            self.assertTrue(row["stack_balanced_at_return"])
        self.assertEqual(
            [(row["before"], row["after"]) for row in report["level_boundary_cases"]],
            [(0xFF, 1), (0, 1), (2, 3), (3, 4), (4, 4)],
        )


if __name__ == "__main__":
    unittest.main()
