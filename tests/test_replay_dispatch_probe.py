import unittest
from pathlib import Path

from tools.x86_replay_dispatch_probe import analyze


class ReplayDispatchProbeTests(unittest.TestCase):
    def test_original_2009_replay_dispatch_contract(self):
        exe = Path(r"F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe")
        if not exe.is_file():
            self.skipTest("the user-provided 2009 executable is unavailable")
        report = analyze(exe)
        self.assertTrue(all(report["checks"].values()))
        self.assertIn("not how often the sync method runs",
                      report["finding"]["limit"])
        self.assertIn("not a busy wait", report["finding"]["frame_sync"])
        self.assertEqual(report["profile"], "provided-original-2009")


if __name__ == "__main__":
    unittest.main()
