import unittest
from pathlib import Path

from tools.x86_player_pair_hit_probe import run


class PlayerPairHitProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dat_dir = Path("original")
        if not (cls.dat_dir / "th123.exe").is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")

    def test_original_two_player_hit_confirms_and_applies_pat_damage(self):
        report = run(self.dat_dir)

        self.assertEqual(report["fixture"]["attacker_trait_0x26"], 100)
        self.assertEqual(report["geometry"]["return_value"], 1)
        self.assertEqual(report["geometry"]["attacker_hit_boxes"], 4)
        self.assertEqual(report["geometry"]["defender_hurt_boxes"], 1)
        self.assertEqual(report["resolver"]["collision_type_attacker"], 1)
        self.assertEqual(report["resolver"]["collision_type_defender"], 0)
        self.assertEqual(report["fixture"]["attacker_damage"], 200)
        self.assertEqual(report["resolver"]["hp_defender_184"], 800)
        self.assertIsNone(report["resolver"]["error"])
        self.assertEqual(report["resolver"]["action_attacker_13c"], 320)
        self.assertEqual(report["resolver"]["action_defender_13c"], 50)
        self.assertEqual(report["resolver"]["sequence_defender_13e"], 0)
        self.assertEqual(report["resolver"]["pose_count_defender_148"], 3)
        self.assertEqual(report["reaction_selection"][1]["defender_vtable"], "0x85d284")
        self.assertEqual(report["reaction_selection"][1]["initialize_action_target"], "0x59aaa0")
        damage_points = {point["pc"]: point for point in report["resolver"]["damage_checkpoints"]}
        self.assertEqual(damage_points["0x47b11c"]["damage"], "200")
        self.assertEqual(damage_points["0x47b11c"]["hp"], "1000")
        self.assertEqual(damage_points["0x47b123"]["hp"], "800")
        self.assertEqual(report["resolver"]["account_counters_after"], [1000, 1000])
        self.assertGreaterEqual(len(report["effect_manager"]["requests"]), 1)
        self.assertEqual(report["effect_manager"]["requests"][0]["arguments_u32"][0], "0xc9")

    def test_original_suika_521_applies_authored_pat_damage_through_special_resolver(self):
        report = run(self.dat_dir, "suika", 521, 1, 0)

        self.assertEqual(report["fixture"]["attacker_damage"], 400)
        self.assertEqual(report["fixture"]["attacker_frame_runtime_damage"], 400)
        self.assertEqual(report["geometry"]["return_value"], 1)
        self.assertEqual(report["damage_scale_events"][0]["ax"], 90)
        self.assertEqual(report["resolver"]["damage_checkpoints"][0]["damage"], "533")
        self.assertEqual(report["resolver"]["hp_defender_184"], 467)
        self.assertEqual(report["resolver"]["action_defender_13c"], 74)
        self.assertIsNone(report["resolver"]["error"])

    def test_original_suika_526_applies_authored_pat_damage_through_special_resolver(self):
        report = run(self.dat_dir, "suika", 526, 0, 7)

        self.assertEqual(report["fixture"]["attacker_damage"], 500)
        self.assertEqual(report["fixture"]["attacker_frame_runtime_damage"], 500)
        self.assertEqual(report["geometry"]["return_value"], 1)
        self.assertEqual(report["resolver"]["damage_checkpoints"][0]["damage"], "666")
        self.assertEqual(report["resolver"]["hp_defender_184"], 334)
        self.assertEqual(report["resolver"]["action_defender_13c"], 74)
        self.assertIsNone(report["resolver"]["error"])

    def test_original_udonge_66c_pat_variant_reaches_pair_geometry_and_damage(self):
        report = run(self.dat_dir, "udonge", 418, 1, 0)

        self.assertEqual(report["fixture"]["attacker_damage"], 850)
        self.assertEqual(report["fixture"]["attacker_frame_runtime_damage"], 850)
        self.assertEqual(report["action_setters"][0]["restored_original_vtable"], "0x85dd5c")
        self.assertEqual(report["geometry"]["return_value"], 1)
        self.assertEqual(report["geometry"]["attacker_hit_boxes"], 1)
        self.assertEqual(report["geometry"]["defender_hurt_boxes"], 1)
        transforms = report["box_transforms"]
        self.assertEqual(len(transforms), 7)
        self.assertEqual({entry["helper"] for entry in transforms}, {"0x4640b0"})
        self.assertEqual(transforms[0]["input_box"], [25, -98, 108, -40])
        self.assertEqual(transforms[0]["output_box"], [345, -278, 428, -220])
        self.assertEqual(report["resolver"]["collision_type_attacker"], 1)
        self.assertEqual(report["resolver"]["damage_checkpoints"][0]["damage"], "1133")
        self.assertEqual(report["resolver"]["hp_defender_184"], 0)
        self.assertEqual(report["resolver"]["error"], "resolver returned at 0x0")

    def test_original_udonge_66c_geometry_uses_world_positions(self):
        attacker = (320.0, 180.0)
        below_near_edge = run(self.dat_dir, "udonge", 418, 1, 0,
                              (attacker, (318.0, 180.0)))
        at_near_edge = run(self.dat_dir, "udonge", 418, 1, 0,
                           (attacker, (320.0, 180.0)))
        at_far_edge = run(self.dat_dir, "udonge", 418, 1, 0,
                          (attacker, (458.0, 180.0)))
        beyond_far_edge = run(self.dat_dir, "udonge", 418, 1, 0,
                              (attacker, (460.0, 180.0)))
        mirrored_contact = run(self.dat_dir, "udonge", 418, 1, 0,
                               (attacker, (320.0, 180.0)), (-1, 1))
        mirrored_outside = run(self.dat_dir, "udonge", 418, 1, 0,
                               (attacker, (322.0, 180.0)), (-1, 1))

        self.assertEqual(below_near_edge["geometry"]["return_value"], 0)
        self.assertEqual(at_near_edge["geometry"]["return_value"], 1)
        self.assertEqual(at_far_edge["geometry"]["return_value"], 1)
        self.assertEqual(beyond_far_edge["geometry"]["return_value"], 0)
        self.assertEqual(mirrored_contact["geometry"]["return_value"], 1)
        self.assertEqual(mirrored_outside["geometry"]["return_value"], 0)
        defender_transforms = [entry for entry in at_near_edge["box_transforms"]
                               if entry["object"] == at_near_edge["fixture"]["defender"]]
        self.assertEqual({entry["helper"] for entry in defender_transforms}, {"0x4640b0"})
        self.assertTrue(all(entry["position"] == [320.0, 180.0]
                            for entry in defender_transforms))


if __name__ == "__main__":
    unittest.main()
