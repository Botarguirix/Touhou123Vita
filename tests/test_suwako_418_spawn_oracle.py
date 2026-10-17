import unittest
from pathlib import Path

from tools.x86_suwako_418_spawn_oracle import Suwako418Oracle


class Suwako418SpawnOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exe = Path("original/th123.exe")
        if not exe.is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")
        cls.oracle = Suwako418Oracle(exe)

    def test_original_handler_applies_signed_facing_and_vertical_offsets(self):
        for facing, expected_x in ((1, 227.0), (-1, 153.0)):
            with self.subTest(facing=facing):
                result = self.oracle.run(190.0, 420.0, facing, 37, 24)
                obj = result["objects"][0]
                self.assertEqual(obj["object_id"], 0x328)
                self.assertEqual(obj["x"], expected_x)
                self.assertEqual(obj["y"], 396.0)

    def test_negative_horizontal_record_reverses_offset_direction(self):
        result = self.oracle.run(200.0, 300.0, -1, -12, -9)
        obj = result["objects"][0]
        self.assertEqual(obj["x"], 212.0)
        self.assertEqual(obj["y"], 309.0)


if __name__ == "__main__":
    unittest.main()
