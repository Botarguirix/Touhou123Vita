import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "x86_skill_sequence_oracle.py"
SPEC = importlib.util.spec_from_file_location("x86_skill_sequence_oracle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SkillSequenceOracleTests(unittest.TestCase):
    def test_original_set_sequence_selects_all_reimu_560_pat_nodes(self):
        oracle = MODULE.SkillSequenceOracle(ROOT / "original" / "th123.exe")
        rows = [oracle.run_set_sequence(sequence) for sequence in range(4)]
        self.assertEqual([row["selected_sequence"] for row in rows], [0, 1, 2, 3])
        self.assertEqual([row["pose_count"] for row in rows], [4, 7, 2, 3])
        self.assertEqual([row["loop_flag"] for row in rows], [0, 0, 1, 0])

    def test_original_next_pose_reports_end_only_for_nonloop_sequence(self):
        oracle = MODULE.SkillSequenceOracle(ROOT / "original" / "th123.exe")
        rows = [
            oracle.run_next_pose_boundary(loop=False, pose_count=3),
            oracle.run_next_pose_boundary(loop=True, pose_count=2),
        ]
        self.assertEqual([row["pose_after_advance"] for row in rows], [0, 0])
        self.assertEqual([row["reports_sequence_end"] for row in rows], [1, 0])

    def test_skill_560_landing_gate_requests_recovery_sequence_three(self):
        oracle = MODULE.SkillSequenceOracle(ROOT / "original" / "th123.exe")
        landed = oracle.run_skill_560_landing_transition(
            height=0.0, vertical_velocity=-1.0, ground_height=0.0
        )
        airborne = oracle.run_skill_560_landing_transition(
            height=1.0, vertical_velocity=-1.0, ground_height=0.0
        )
        stopped = oracle.run_skill_560_landing_transition(
            height=0.0, vertical_velocity=0.0, ground_height=0.0
        )
        self.assertEqual(landed["requested_recovery_sequence"], 3)
        self.assertIsNone(airborne["requested_recovery_sequence"])
        self.assertIsNone(stopped["requested_recovery_sequence"])


if __name__ == "__main__":
    unittest.main()
