import unittest
from pathlib import Path

from tools.x86_replay_manager_vtable_probe import analyze


class ReplayManagerVtableProbeTests(unittest.TestCase):
    def test_original_2009_manager_rtti_and_replay_slots(self):
        exe = Path(r"F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe")
        if not exe.is_file():
            self.skipTest("the user-provided compatible 2009 executable is unavailable")
        report = analyze(exe)
        self.assertTrue(all(report["checks"].values()))
        managers = report["managers"]
        self.assertEqual(managers["CBattleManager_0x008218e4"]["slot_target"], "0x00481040")
        self.assertEqual(managers["CBattleManagerStory_0x0082192c"]["slot_target"], "0x0047ee10")
        self.assertEqual(managers["CBattleManagerArcade_0x00821994"]["slot_target"], "0x00481040")
        self.assertEqual(managers["CBattleManagerStory_0x0082192c"]["slot_5_target"], "0x0047f810")
        self.assertIsNotNone(managers["CBattleManagerStory_0x0082192c"]["slot_5_dispatches_slot_16_at"])
        self.assertIn("CBattleManager", managers["CBattleManagerArcade_0x00821994"]["base_classes"])


if __name__ == "__main__":
    unittest.main()
