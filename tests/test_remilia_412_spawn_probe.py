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

        self.assertEqual(plus["initialized_action"]["action"], 412)
        self.assertEqual(plus["initialized_action"]["sequence"], 0)
        self.assertEqual(plus["initialized_action"]["pose"], 0)
        self.assertEqual(plus["initialized_action"]["pose_count"], 12)
        self.assertEqual(plus["initialized_action"]["initializer_chain"], [
            "0x464930", "0x438ca0", "0x465370", "0x59aaa0", "0x59ad64", "0x4636b0"]
        )
        self.assertEqual(len(plus["main_update_dispatch_trace"]), 16 * 3)
        self.assertTrue(all(plus["main_update_dispatch_trace"][i:i + 3] ==
                            ["0x587bab", "0x58a3a1", "0x58cce7"]
                            for i in range(0, 16 * 3, 3)))
        self.assertEqual(plus["ticks_until_spawn"], 16)
        self.assertEqual([state["pose"] for state in plus["animation_tick_states"]],
                         [0] * 3 + [1] * 4 + [2] * 4 + [3] * 4 + [4])
        self.assertEqual([state["subframe"] for state in plus["animation_tick_states"][:4]],
                         [1, 2, 3, 0])
        self.assertEqual(plus["animation_tick_states"][-1]["duration"], 4)
        self.assertEqual(plus["spawn_call"]["object_id"], 801)
        self.assertEqual(plus["spawn_call"]["x"], 403.0)
        self.assertEqual(minus["spawn_call"]["x"], 237.0)
        self.assertEqual(plus["spawn_call"]["y"], 360.0)
        self.assertEqual(minus["spawn_call"]["y"], 360.0)
        self.assertEqual(plus["spawn_call"]["temporary_float_block"], [-70.0, 12.0, 0.0])
        self.assertEqual(plus["callback_dispatch"]["index"], 1)
        self.assertEqual(plus["callback_dispatch"]["selected_function_pointer"], "0x12345678")
        self.assertEqual(plus["original_helpers_reached"].count("0x438c60"), 16)
        self.assertEqual(plus["original_helpers_reached"][-3:], ["0x47a9e0", "0x487870", "0x820230"])
        self.assertEqual(plus["post_spawn_fields"], {"meter_49e": 800, "gauge_5e4": 50})
        self.assertEqual(minus["callback_dispatch"]["action"], 412)
        self.assertEqual(minus["callback_dispatch"]["substate"], 4)

    def test_real_factory_hitbox_reaches_original_pair_geometry(self):
        report = run_case(self.dat_dir, 320.0, 180.0, 1, 1, real_factory=True)
        child = report["child_factory_result"]
        self.assertEqual((child["action"], child["sequence"], child["pose_count"]),
                         (801, 0, 20))
        self.assertEqual(report["child_box_sync"]["hit_box_count"], 1)
        self.assertEqual(report["child_box_sync"]["hit_boxes"],
                         [[368, -395, 438, -325]])
        self.assertEqual(len(report["child_updates"]), 55)
        self.assertIsNone(report["child_update_error"])
        self.assertEqual([row["contact"] for row in report["collision_matrix"]],
                         [True, True, True, False, False, False, False])
        self.assertEqual([row["center_distance_x"] for row in report["collision_matrix"]],
                         [0.0, 40.0, 60.0, 70.0, 71.0, 100.0, 200.0])
        manager = report["manager_tick"]
        completed = [row for row in manager["ticks"] if row["completed"]]
        self.assertEqual(manager["interface"], hex(0x01000000 - 4))
        self.assertEqual(manager["update_slot"], "vtable[4] -> 0x633ce0")
        self.assertEqual(len(completed), 55)
        self.assertEqual(completed[-1]["field_34c"], 0)
        self.assertTrue(manager["object_retired"])
        self.assertFalse(manager["original_child_still_linked"])
        self.assertEqual(manager["live_node_count"], 6)
        self.assertEqual(manager["live_node_actions"], ["801"] * 6)
        self.assertEqual(len(report["factory_returns"]), 19)
        helper_calls = report["create_object_helper_calls"]
        self.assertEqual(len(helper_calls), 19)
        self.assertTrue(all(row["this"] == child["pointer"] for row in helper_calls))
        self.assertTrue(all(row["return_address"] == "0x787a85" for row in helper_calls))
        self.assertTrue(all(row["this_action"] == 801 and row["this_mode_190"] == 0
                            for row in helper_calls))
        self.assertEqual([row["this_pose"] for row in helper_calls],
                         [0, 3, 6, 9, 12, 15, 18, 1, 4, 7, 10, 13, 16, 19, 2, 5, 8, 11, 14])

    def test_original_pair_dispatch_reaches_pat_damage_after_opening_observed_gates(self):
        report = run_case(self.dat_dir, 320.0, 180.0, 1, 1,
                          real_factory=True, resolve_damage=True)
        pair = report["pair_dispatch"]
        self.assertIsNone(pair["error"])
        self.assertTrue(pair["reached_projectile_filter"])
        self.assertTrue(pair["reached_character_resolver"])
        self.assertEqual(pair["defender_frame_flags"], "0x31")
        self.assertEqual(pair["defender_hp_after"], 1000)
        gate_trial = pair["gate_open_trial"]
        self.assertTrue(gate_trial["synthetic"])
        self.assertEqual(gate_trial["geometry_after_dispatch"]["return_value"], 1)
        self.assertTrue(gate_trial["reached_hit_response"])
        self.assertEqual(gate_trial["defender_hp_after"], 880)
        self.assertIn("0x47a5b0", gate_trial["call_sites"])
        response = report["damage_response"]
        self.assertEqual(response["function"], "pair-dispatch-gate-open")
        self.assertTrue(response["damage_applied"])
        self.assertEqual(response["pat_damage"], 120)
        self.assertEqual((response["defender_hp_before"], response["defender_hp_after"]),
                         (1000, 880))
        self.assertEqual(response["attacker_frame_damage_field"], 120)
        self.assertEqual(response["attacker_frame_flags"], "0x1000000")
        self.assertEqual(response["attacker_attack_flags"], "0x41040e")
        self.assertEqual(response["attacker_cooldown_190"], 9)
        self.assertTrue(response["failure_after_damage"])
        self.assertEqual(response["external_callback_pointer"], "0x0")
        self.assertIn("0x479cb0", response["trace"])


if __name__ == "__main__":
    unittest.main()
