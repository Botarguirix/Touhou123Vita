import unittest
from pathlib import Path

from tools.x86_remilia_412_spawn_probe import run_case
from tools.find_pat_vulnerability_frames import scan_character


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

    def test_original_pair_dispatch_applies_pat_damage_on_real_vulnerable_pose(self):
        report = run_case(self.dat_dir, 320.0, 180.0, 1, 1,
                          real_factory=True, resolve_damage=True)
        pair = report["pair_dispatch"]
        self.assertIn("0x0", pair["error"])
        self.assertTrue(pair["reached_projectile_filter"])
        self.assertTrue(pair["reached_character_resolver"])
        self.assertEqual(pair["defender_pat_action"], 602)
        self.assertEqual((pair["defender_pat_sequence"], pair["defender_pat_frame"]), (0, 0))
        self.assertEqual(pair["defender_frame_flags"], "0x3041")
        action_state = pair["defender_action_setter_state"]
        self.assertEqual((action_state["action"], action_state["sequence"],
                          action_state["pose"], action_state["pose_count"]),
                         (602, 0, 0, 8))
        self.assertTrue(action_state["original_pose_selector_reached"])
        self.assertIn("0x59aaa0", action_state["trace"])
        self.assertEqual(pair["defender_field_1ac_after_original_constructor"], 1)
        self.assertEqual(report["defender_constructor"], {
            "function": "0x46b7f0", "field_1ac_after_constructor": 1,
        })
        update = report["defender_original_update"]
        self.assertFalse(update["completed"])
        self.assertEqual(update["host_termination"]["api"], "TerminateProcess")
        self.assertEqual(update["host_termination"]["exit_code"], "0xc000000d")
        self.assertEqual(update["host_termination"]["return_address"], "0x81ff36")
        self.assertEqual(update["termination_context"], {
            "exception_code": "0xc000000d", "exception_address": "0x81ff7c",
        })
        crt_event = next(event for event in update["events"]
                         if event["address"] == "crt-handler-entry")
        self.assertEqual((crt_event["entry"], crt_event["return_address"]),
                         ("0x81ff70", "0x44be42"))
        self.assertEqual(crt_event["stack_args"], [
            "0x1008f2c", "0x1008800", "0x0", "0x1", "0x46b3a9", "0x6",
        ])
        self.assertIn("0x594009", update["trace"])
        self.assertIn("0x46b370", update["trace"])
        self.assertIn("0x44be10", update["trace"])
        self.assertEqual((update["action"], update["sequence"], update["pose"]),
                         (602, 0, 0))
        self.assertEqual(pair["defender_hp_after"], 880)
        # This isolated projectile damage path does not produce the player's
        # hit-confirm CollisionType required by Remilia's 5AA->5AAA handler.
        self.assertEqual(pair["defender_collision_type_after"], 0)
        self.assertNotIn("gate_open_trial", pair)
        response = report["damage_response"]
        self.assertEqual(response["function"], "pair-dispatch")
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

    def test_original_player_update_advances_pat_action_5aaa(self):
        report = run_case(self.dat_dir, 320.0, 180.0, 1, 1,
                          real_factory=True, resolve_damage=True,
                          defender_action_id=321)
        self.assertEqual(report["defender_action_setter"]["action"], 321)
        update = report["defender_original_update"]
        self.assertTrue(update["completed"])
        self.assertEqual(update["exit"], "0x599fb0")
        self.assertIsNone(update["host_termination"])
        self.assertEqual((update["action"], update["sequence"], update["pose"],
                          update["subframe"]), (321, 0, 0, 1))
        self.assertEqual(update["events"], [])
        pair = report["pair_dispatch"]
        self.assertEqual(pair["defender_pat_action"], 321)
        self.assertEqual(pair["defender_frame_flags"], "0x41")
        self.assertEqual(pair["defender_hp_after"], 880)
        self.assertTrue(report["damage_response"]["damage_applied"])

    def test_remilia_pat_inventory_has_vulnerable_hurtbox_frames(self):
        report = scan_character(self.dat_dir, "remilia")
        self.assertEqual(report["archive"], "th123c.dat")
        self.assertEqual(report["poses_with_hurt_boxes"], 3052)
        self.assertEqual(report["poses_with_flag_0x40"], 781)
        self.assertEqual(report["poses_with_hurt_and_flag_0x40"], 762)
        example = report["actions"]["602"]["examples"][0]
        self.assertEqual((example["sequence"], example["frame"], example["frame_flags"]),
                         (0, 0, "0x00003041"))


if __name__ == "__main__":
    unittest.main()
