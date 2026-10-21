import csv
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "x86_suika_623c_dispatch_probe.py"
SPEC = importlib.util.spec_from_file_location("x86_suika_623c_dispatch_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Suika623CDispatchProbeTests(unittest.TestCase):
    def test_original_623c_selects_level_routes_and_pat_actions(self):
        report = MODULE.run(ROOT / "original/th123.exe")
        rows = report["cases"]
        self.assertEqual(report["passed"], True)
        self.assertEqual([row["selected_action"] for row in rows], [531, 526, 521, -1])
        self.assertEqual([row["move_lock_queries"] for row in rows],
                         [[531], [526], [521], [531, 526, 521]])
        self.assertEqual([row["event_skill_use_calls"] for row in rows], [1, 1, 1, 0])
        self.assertEqual([row["set_action_requests"] for row in rows],
                         [[531], [526], [521], []])
        self.assertEqual([row["use_skill_original_body_executed"] for row in rows],
                         [True, True, True, False])

        b_rows=report["623b_cases"]
        self.assertEqual(report["623b_entry"],"0x60a5b0")
        self.assertEqual([row["command_mask"] for row in b_rows],[0x200]*4)
        self.assertEqual([row["selected_action"] for row in b_rows],[530,525,520,-1])
        self.assertEqual([row["move_lock_queries"] for row in b_rows],
                         [[530],[525],[520],[530,525,520]])
        self.assertEqual([row["event_skill_use_calls"] for row in b_rows],[1,1,1,0])
        self.assertEqual([row["set_action_requests"] for row in b_rows],
                         [[530],[525],[520],[]])

        with (ROOT / "artifacts/pat-detail.tsv").open(encoding="cp932", newline="") as stream:
            pat = list(csv.DictReader(stream, delimiter="\t"))
        suika_actions = {
            int(row["action"]) for row in pat
            if row["path"].lower().startswith("data/character/suika/")
        }
        self.assertTrue(set((531, 526, 521)).issubset(suika_actions))


if __name__ == "__main__":
    unittest.main()
