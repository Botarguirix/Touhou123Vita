import unittest
from pathlib import Path

from tools.x86_replay_story_callback_probe import analyze, analyze_replay


class ReplayStoryCallbackProbeTests(unittest.TestCase):
    def test_story_callback_routes_same_input_object_only_in_state_two(self):
        exe = Path(r"F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe")
        if not exe.is_file():
            self.skipTest("the user-provided compatible 2009 executable is unavailable")
        report = analyze(exe)
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["runs"]["state_2"]["decoder_receivers"], ["0x0085ec98"])
        self.assertEqual(report["runs"]["control_state_1"]["decoder_call_count"], 0)
        self.assertIn("not input consumption", report["scope"])

    def test_original_story_update_and_decoder_consume_every_sanae_word_pair(self):
        exe = Path(r"F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe")
        replay = Path(
            r"C:\Users\Andy PC\AppData\Roaming\Vita3K\Vita3K\ux0\data\Touhou123Vita\replay\story\090815_2219_sanae_story.rep"
        )
        if not exe.is_file() or not replay.is_file():
            self.skipTest("the user-provided compatible executable or replay is unavailable")
        report = analyze_replay(exe, replay)
        self.assertEqual(report["total_story_callback_invocations"], 16910)
        self.assertEqual([row["story_callback_invocations"] for row in report["records"]],
                         [4360, 3466, 9084])
        self.assertTrue(all(report["checks"].values()))
        self.assertIn("not that the live menu configures f0=3", report["scope"])


if __name__ == "__main__":
    unittest.main()
