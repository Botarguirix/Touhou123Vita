import csv
import tempfile
import unittest
from pathlib import Path

from tools.summarize_pat_attack_flags import summarize


class PatAttackFlagsTests(unittest.TestCase):
    def test_groups_unboxed_damaging_poses_by_character_action_and_flag(self):
        rows = [
            ("data/character/remilia/remilia.pat", 412, 0, 750, "-", "0x00204002"),
            ("data/character/remilia/remilia.pat", 412, 0, 750, "-", "0x00204002"),
            ("data/character/remilia/remilia.pat", 416, 1, 800, "-", "0x0000240a"),
            ("data/character/alice/alice.pat", 418, 0, 900, "-", "0x00088404"),
            ("data/character/reimu/reimu.pat", 408, 1, 300, "0,0,1,1", "0x0000240a"),
            ("data/character/common/common.pat", 412, 0, 600, "-", "0x00204002"),
            ("data/character/remilia/remilia.pat", 412, 0, 0, "-", "0x00204002"),
        ]
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "pat-detail.tsv"
            with source.open("w", encoding="cp1252", newline="") as stream:
                writer = csv.writer(stream, delimiter="\t")
                writer.writerow(("path", "action", "index", "damage", "attack_boxes", "attack_flags"))
                writer.writerows(rows)
            report = summarize(source)

        self.assertIn("`remilia` | 412 | 0 | `0x00204002` | 2 | 750", report)
        self.assertIn("`remilia` | 416 | 1 | `0x0000240a` | 1 | 800", report)
        self.assertIn("`alice` | 418 | 0 | `0x00088404` | 1 | 900", report)
        self.assertIn("Combinaciones personaje/acción/índice/flags sin cajas explícitas: **3** (4 poses).", report)
        self.assertNotIn("common", report)
        self.assertNotIn("`reimu`", report)


if __name__ == "__main__":
    unittest.main()
