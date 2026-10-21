import unittest
from pathlib import Path

from tools.x86_replay_update_method_probe import analyze


class ReplayUpdateMethodProbeTests(unittest.TestCase):
    def test_original_update_method_over_full_sanae_replay(self):
        exe = Path(r"F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe")
        replay = Path(
            r"C:\Users\Andy PC\AppData\Roaming\Vita3K\Vita3K\ux0\data\Touhou123Vita\replay\story\090815_2219_sanae_story.rep"
        )
        if not exe.is_file() or not replay.is_file():
            self.skipTest("the user-provided 2009 executable or replay is unavailable")
        report = analyze(exe, replay, all_words=True)
        self.assertTrue(report["all_words_executed"])
        self.assertEqual(report["total_invocations_executed"], 33820)
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual([r["invocations_executed"] for r in report["records"]],
                         [8720, 6932, 18168])
        self.assertGreater(sum(r["words_with_0x2000_or_0x4000_flags"]
                               for r in report["records"]), 0)


if __name__ == "__main__":
    unittest.main()
