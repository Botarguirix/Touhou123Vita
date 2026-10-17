import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "x86_reimu_505_object_oracle.py"
SPEC = importlib.util.spec_from_file_location("x86_reimu_505_object_oracle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Reimu505ObjectOracleTests(unittest.TestCase):
    def test_all_projectile_routes_and_facing_directions(self):
        counts = {0: 3, 1: 4, 2: 5}
        velocities = {
            0: [(10.0, 22.0), (0.0, 24.0), (-10.0, 22.0)],
            1: [(15.0, 24.0), (5.0, 26.0), (-5.0, 26.0), (-15.0, 24.0)],
            2: [(20.0, 25.0), (10.0, 26.0), (0.0, 28.0), (-10.0, 26.0), (-20.0, 25.0)],
        }
        oracle = MODULE.Reimu505Oracle(ROOT / "original/th123.exe")
        for facing in (-1, 1):
            for route in range(3):
                with self.subTest(facing=facing, route=route):
                    result = oracle.run(190.0, 0.0, facing, route)
                    self.assertEqual(result["object_count"], counts[route])
                    self.assertEqual(
                        [tuple(obj["velocity"]) for obj in result["objects"]],
                        velocities[route],
                    )
                    self.assertTrue(all(obj["object_id"] == 811 for obj in result["objects"]))
                    expected_x = 304.0 if facing > 0 else 76.0
                    self.assertTrue(all(obj["x"] == expected_x for obj in result["objects"]))


if __name__ == "__main__":
    unittest.main()
