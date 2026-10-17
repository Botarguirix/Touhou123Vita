import unittest
from pathlib import Path

from tools.x86_suwako_808_action_probe import Suwako808ActionProbe


class Suwako808ActionProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = Path("original/th123.exe")
        if not cls.exe.is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")

    def test_original_set_action_resolves_split_to_sequence_one_and_frame(self):
        result = Suwako808ActionProbe(self.exe).run()
        self.assertEqual(result["action"], 808)
        self.assertEqual(result["sequence"], 1)
        self.assertEqual(result["current_sequence"], "0x1104000")
        self.assertEqual(result["frame_pointer"], "0x1106000")
        self.assertEqual(result["velocity"], [-4.104241847991943, 11.276311874389648])
        self.assertEqual(result["constructor_render_color_hex"], "ffffffff")
        self.assertEqual(result["render_alpha"], 0xFF)

    def test_action_and_sequence_initializers_preserve_render_color_sentinel(self):
        result = Suwako808ActionProbe(self.exe).run(initial_color=0xA1B2C3D4)
        self.assertEqual(result["render_color_hex"], "d4c3b2a1")
        self.assertEqual(result["render_alpha"], 0xA1)
        self.assertEqual([log["sequence"] for log in result["frame_logs"]], [0, 1])


if __name__ == "__main__":
    unittest.main()
