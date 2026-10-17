import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARIZER = ROOT / "tools" / "summarize_dash_dispatch.py"
HEADER = "path\taction\tindex\tmove_lock\taction_lock\tpose\tdamage\tattack_flags\tattack_boxes\n"


class DashDispatchSummary(unittest.TestCase):
    def test_tracks_variant_locks_and_missing_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "pat-detail.tsv"
            target = Path(directory) / "coverage.md"
            source.write_text(
                HEADER
                + "data/character/reimu/reimu.pat\t200\t0\t5\t50\t0\t0\t0x00000000\t-\n"
                + "data/character/reimu/reimu.pat\t408\t0\t50\t100\t0\t0\t0x00000000\t-\n"
                + "data/character/reimu/reimu.pat\t408\t1\t50\t100\t0\t200\t0x00204002\t0,0,10,10\n"
                + "data/character/reimu/reimu.pat\t418\t0\t50\t100\t0\t300\t0x00204002\t0,0,10,10\n"
                + "data/character/remilia/remilia.pat\t200\t0\t5\t10\t0\t0\t0x00000000\t-\n"
                + "data/character/remilia/remilia.pat\t412\t0\t40\t50\t5\t750\t0x00204002\t-\n",
                encoding="ascii",
            )
            result = subprocess.run(
                [sys.executable, str(SUMMARIZER), str(source), str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = target.read_text(encoding="utf-8")
            self.assertIn("| `reimu` | 0:5/50", report)
            self.assertIn("1:50/100 (hit)", report)
            self.assertIn("| `remilia` | 0:5/10", report)
            self.assertIn("| `remilia` | 0:5/10 (sin hitbox dañina) | — | — |", report)
            self.assertIn("acción 200", report)
            self.assertIn("412 (2C): índice 0: move/action lock 40/50, 1 poses con daño y flags, 0 con caja ofensiva explícita", report)
            self.assertIn("flags 0x00204002", report)
            self.assertIn("Los 20 PAT tienen una definición explícita", report)


if __name__ == "__main__":
    unittest.main()
