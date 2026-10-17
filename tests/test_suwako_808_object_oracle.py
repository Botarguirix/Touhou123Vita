import unittest
from pathlib import Path

from tools.x86_suwako_808_object_oracle import Suwako808Oracle


class Suwako808ObjectOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exe = Path("original/th123.exe")
        if not exe.is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")
        cls.exe = exe

    def test_clear_airborne_route_creates_two_children_with_original_custom_data(self):
        report = Suwako808Oracle(self.exe).run(
            x=300.0, y=400.0, floor_y=500.0,
            random_values=(10, 2, 20, 4),
        )
        self.assertEqual(report["random_bounds"], [160, 6, 160, 6])
        self.assertEqual(report["children"], [
            {"object_id": 0x328, "x": 300.0, "y": 400.0, "facing": 1,
             "arg4": 1, "custom_data": [-20.0, 12.0, 1.0], "flags": 3},
            {"object_id": 0x328, "x": 300.0, "y": 400.0, "facing": 1,
             "arg4": 1, "custom_data": [-30.0, 14.0, 1.0], "flags": 3},
        ])
        self.assertEqual(report["parent"]["split_latch"], 1)
        self.assertAlmostEqual(report["parent"]["vy"], -0.2, places=6)

    def test_floor_branch_suppresses_split_when_parent_is_below_returned_floor(self):
        report = Suwako808Oracle(self.exe).run(y=400.0, floor_y=300.0)
        self.assertEqual(report["children"], [])
        self.assertEqual(report["parent"]["split_latch"], 0)

    def test_collision_probe_suppresses_split(self):
        report = Suwako808Oracle(self.exe).run(collision=True)
        self.assertEqual(report["children"], [])
        self.assertEqual(report["parent"]["split_latch"], 0)

    def test_existing_split_latch_prevents_duplicate_children(self):
        report = Suwako808Oracle(self.exe).run(latch=1)
        self.assertEqual(report["children"], [])
        self.assertEqual(report["parent"]["split_latch"], 1)
        self.assertEqual(report["parent"]["vx"], 0.0)
        self.assertEqual(report["parent"]["vy"], 0.0)

    def test_sequence_one_uses_radial_horizontal_component_and_gravity(self):
        report = Suwako808Oracle(self.exe).run(
            x=300.0, y=400.0, sequence=1, initial_alpha=0xFF,
            initial_vx=-4.1042417199,
        )
        self.assertEqual(report["children"], [])
        self.assertAlmostEqual(report["parent"]["x"], 295.89576, places=3)
        self.assertAlmostEqual(report["parent"]["y"], 399.8, places=3)
        self.assertAlmostEqual(report["parent"]["vy"], -0.2, places=6)

    def test_original_initializer_sets_radial_velocity_and_first_update_consumes_it(self):
        oracle = Suwako808Oracle(self.exe)
        result = oracle.initialize_and_update_child((-20.0, 12.0, 1.0))
        initialized = result["initializer"]["initialized"]
        self.assertAlmostEqual(initialized["vx"], -4.1042418, places=5)
        self.assertAlmostEqual(initialized["vy"], 11.2763119, places=5)
        tick = result["updates"][0]
        self.assertAlmostEqual(tick["x"], 295.89576, places=3)
        self.assertAlmostEqual(tick["y"], 411.0763, places=3)
        self.assertAlmostEqual(tick["vy"], 11.07631, places=4)
        self.assertEqual(result["sequence_source"].split(",")[0], "custom_data[2]")

    def test_parent_split_chains_into_initializers_and_render_alpha_gated_motion(self):
        report = Suwako808Oracle(self.exe).split_and_update_children(ticks=12)
        self.assertEqual(len(report["children"]), 2)
        first, second = report["children"]
        self.assertEqual(first["factory_call"]["custom_data"], [-20.0, 12.0, 1.0])
        self.assertEqual(second["factory_call"]["custom_data"], [-30.0, 14.0, 1.0])
        self.assertEqual(first["initializer"]["sequence"], 1)
        self.assertEqual(second["initializer"]["sequence"], 1)
        self.assertEqual(len(first["updates"]), 12)
        self.assertEqual(len(second["updates"]), 12)
        self.assertAlmostEqual(first["updates"][0]["y"], 411.0763, places=3)
        self.assertAlmostEqual(first["updates"][3]["y"], 443.1053, places=3)
        self.assertAlmostEqual(first["updates"][8]["y"], 492.4868, places=3)
        self.assertAlmostEqual(second["updates"][0]["x"], 293.0, places=3)
        self.assertAlmostEqual(second["updates"][3]["y"], 446.4974, places=3)
        self.assertEqual(first["updates"][0]["render_alpha"], 247)
        self.assertEqual(first["final_state"]["render_alpha"], 159)
        self.assertAlmostEqual(first["final_state"]["scalar_11c"], 0.81, places=5)
        self.assertIn("custom_data[2]", first["sequence_source"])
        faded = Suwako808Oracle(self.exe).initialize_and_update_child(
            (-20.0, 12.0, 1.0), ticks=32,
        )
        self.assertEqual(faded["final_state"]["render_alpha"], 7)
        self.assertEqual(faded["updates"][30]["x"], faded["updates"][31]["x"])
        self.assertEqual(faded["updates"][30]["y"], faded["updates"][31]["y"])


if __name__ == "__main__":
    unittest.main()
