import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "x86_skill_handler_dispatch_oracle.py"
SPEC = importlib.util.spec_from_file_location("x86_skill_handler_dispatch_oracle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SkillHandlerDispatchTests(unittest.TestCase):
    def test_original_switch_blocks_dispatch_ground_and_air_routes(self):
        root = Path(__file__).resolve().parents[1]
        report = MODULE.run(root / "original/th123.exe")
        self.assertEqual(report["executed_dispatches"], 20)
        self.assertEqual(len([r for r in report["rows"] if r["context"] == "grounded"]), 12)
        self.assertEqual(len([r for r in report["rows"] if r["context"] == "airborne"]), 8)
        self.assertTrue(all(r["event_skill_use_calls"] == 1 for r in report["rows"]))
        self.assertTrue(all(r["upgrade_calls"] == 1 for r in report["rows"]))
        self.assertTrue(all(r["use_skill_action_lock"] == 23 for r in report["rows"]))


if __name__ == "__main__":
    unittest.main()
