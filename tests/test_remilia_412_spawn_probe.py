import unittest
from pathlib import Path

from tools.x86_remilia_412_spawn_probe import run_case


class Remilia412SpawnProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dat_dir = Path("original")
        if not (cls.dat_dir / "th123.exe").is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")

    def test_original_state4_callsite_uses_facing_and_indexed_callback(self):
        plus = run_case(self.dat_dir, 320.0, 180.0, 1, 1)
        minus = run_case(self.dat_dir, 320.0, 180.0, -1, 1)

        self.assertEqual(plus["spawn_call"]["object_id"], 801)
        self.assertEqual(plus["spawn_call"]["x"], 403.0)
        self.assertEqual(minus["spawn_call"]["x"], 237.0)
        self.assertEqual(plus["spawn_call"]["y"], 360.0)
        self.assertEqual(minus["spawn_call"]["y"], 360.0)
        self.assertEqual(plus["spawn_call"]["temporary_float_block"], [-70.0, 12.0, 0.0])
        self.assertEqual(plus["callback_dispatch"]["index"], 1)
        self.assertEqual(plus["callback_dispatch"]["selected_function_pointer"], "0x12345678")
        self.assertEqual(plus["original_helpers_reached"], ["0x47a9e0", "0x487870", "0x820230"])
        self.assertEqual(plus["post_spawn_fields"], {"meter_49e": 800, "gauge_5e4": 50})
        self.assertEqual(minus["callback_dispatch"]["action"], 412)
        self.assertEqual(minus["callback_dispatch"]["substate"], 4)


if __name__ == "__main__":
    unittest.main()
