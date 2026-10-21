import unittest
from pathlib import Path

from tools.x86_suika_constructed_handler_probe import run


class SuikaConstructedHandlerProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path("original/th123.exe").is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")

    def test_original_constructor_setter_and_full_handler_reach_418(self):
        report = run()
        self.assertTrue(report["constructor"]["returned_to_stop"])
        self.assertEqual(report["constructor"]["player_vtable"], "0x85da84")
        self.assertEqual(report["action_before_handler"], 200)
        self.assertEqual(report["branch"], "0x60be83")
        self.assertEqual(report["setter_requests"], [418])
        self.assertEqual(report["action_after_handler"], 418)
        self.assertTrue(report["cleanup_entry_reached"])
        self.assertIsNone(report["original_cleanup_error"])
        self.assertEqual(report["character_update_entry"], "0x5ee620")
        self.assertEqual(len(report["pat_ticks"]), 16)
        self.assertEqual((report["pat_ticks"][-1]["sequence"],
                          report["pat_ticks"][-1]["pose"],
                          report["pat_ticks"][-1]["frame_damage"],
                          report["pat_ticks"][-1]["frame_attack_boxes"]),
                         (2, 0, 900, 1))
        self.assertIsNone(report["character_update_error"])
        self.assertEqual(report["geometry_after_transition"]["return_value"], 1)
        self.assertEqual(report["geometry_after_transition"]["attacker_hit_boxes"], 1)
        self.assertEqual(report["geometry_after_transition"]["defender_hurt_boxes"], 2)
        self.assertIsNone(report["damage_after_transition"]["resolver_error"])
        self.assertEqual(report["damage_after_transition"]["direct_damage_helper_value"], 900)
        self.assertEqual(report["damage_after_transition"]["reaction_inputs"][0]["trait_26"], 100)
        self.assertEqual(report["damage_after_transition"]["action_defender"], 74)
        self.assertEqual(report["damage_after_transition"]["hp_defender"], 800)
        self.assertEqual(report["damage_after_transition"]["damage_checkpoints"], [
            {"pc": "0x47b11c", "damage": 1200, "hp": 2000},
            {"pc": "0x47b123", "damage": 1200, "hp": 800},
        ])
        self.assertEqual(report["damage_after_transition"]["sequence_defender"], 0)
        self.assertEqual(report["damage_after_transition"]["action_setter_requests"], [
            {"player": "0x100a000", "action": 74, "callsite": "0x47b194"},
            {"player": "0x100a000", "action": 97, "callsite": "0x4846a7"},
        ])
        transition = report["damage_after_transition"]["defender_transition_checkpoint"]
        self.assertEqual((transition["action_before_input"], transition["action_after_input"],
                          transition["action_after_character_update"]), (74, 74, 97))
        route_pcs = [int(row["pc"], 16) for row in report["damage_after_transition"]
                     ["action_route_observations_tick10"]]
        expected_route = [0x483F40, 0x4849F6, 0x484A20, 0x484A80, 0x484AB0,
                          0x487EA0, 0x484AD1, 0x4847D4, 0x484807, 0x484696,
                          0x4846A1, 0x4846A5, 0x6086A0]
        next_route_index = 0
        for pc in route_pcs:
            if next_route_index < len(expected_route) and pc == expected_route[next_route_index]:
                next_route_index += 1
        self.assertEqual(next_route_index, len(expected_route), route_pcs)
        self.assertIn(0x48B85F, route_pcs)
        self.assertIn(0x48B8CF, route_pcs)
        self.assertTrue(all(tick["field_884"] == 0 for tick in
                            report["damage_after_transition"]["defender_hitstun_ticks"]))
        self.assertEqual(report["damage_after_transition"]["field_884_writes"], [])
        multi_tick_probe = report["damage_after_transition"]["multi_tick_input_recovery_probe"]
        self.assertEqual(len(multi_tick_probe), 8)
        self.assertTrue(all(case["ticks_completed"] == 24 and case["error"] is None
                            for case in multi_tick_probe))
        self.assertTrue(all(case["final_action"] == 97 and case["final_field_884"] == 0
                            and case["field_writes"] == [] and
                            case["action_setters"] == [] and
                            case["sequence_setters"] == [] for case in multi_tick_probe))
        forced_gate = report["damage_after_transition"]["field_884_positive_entry_probe"]
        self.assertEqual((forced_gate["field_before_force"], forced_gate["field_forced"],
                          forced_gate["action_after_update"]), (0, 1, 96))
        self.assertIsNone(forced_gate["error"])
        self.assertEqual(forced_gate["setter_requests"], [
            {"player": "0x100a000", "action": 97, "callsite": "0x4846a7"},
            {"player": "0x100a000", "action": 96, "callsite": "0x48b8ef"},
        ])
        ticks = report["damage_after_transition"]["defender_hitstun_ticks"]
        self.assertEqual([tick["hitstop"] for tick in ticks[:10]], list(range(9, -1, -1)))
        self.assertEqual([tick["action"] for tick in ticks[:9]], [74] * 9)
        self.assertEqual(ticks[9]["action"], 97)
        self.assertEqual(ticks[9]["position"][1], 0.0)
        self.assertEqual(len(ticks), 300)
        self.assertEqual(ticks[-1]["action"], 97)
        self.assertEqual(ticks[-1]["position"][1], 500.0)
        self.assertEqual(ticks[16]["authored_pat_sequence"], 3)
        self.assertEqual(ticks[42]["authored_pat_sequence"], 2)
        self.assertEqual(ticks[-1]["authored_pat_sequence"], 2)
        self.assertEqual(ticks[-1]["sequence_loop_mode"], 1)
        self.assertEqual(ticks[-1]["position"][1], 500.0)
        self.assertEqual(ticks[-1]["velocity"][1], 0.0)
        self.assertIsNone(ticks[-1]["error"])
        self.assertTrue(all(tick["input_error"] is None for tick in ticks))
        self.assertIsNone(report["damage_after_transition"]["defender_input_error"])
        self.assertEqual(report["damage_after_transition"]["sequence_setter_requests"], [
            {"tick": 17, "callsite": "0x4851e7", "action": 97,
             "sequence_argument": 3, "sequence_before": 1},
        ])
        action96 = report["damage_after_transition"]["action96_original_execution"]
        self.assertIsNone(action96["setter_error"])
        self.assertEqual(action96["action_before_ticks"], 96)
        self.assertEqual(len(action96["ticks"]), 1200)
        self.assertTrue(all(tick["action"] == 96 and tick["error"] is None
                            for tick in action96["ticks"][:-1]))
        self.assertEqual(action96["ticks"][0]["pat_sequence_for_node"], 0)
        self.assertTrue(all(tick["frame_in_pat_fixture"]
                            for tick in action96["ticks"][:-1]))
        self.assertEqual(action96["ticks"][-1]["action"], 96)
        self.assertFalse(action96["ticks"][-1]["invalid_code_fetch"])
        self.assertEqual(action96["invalid_code_fetches"], [])
        self.assertEqual(action96["invalid_fetch_context"], [])
        self.assertEqual(action96["info_manager_hud_shim"]["original_slot_6"],
                         "0x47eb70")
        self.assertEqual(len(action96["info_manager_hud_shim"]["callback_calls"]), 3)
        self.assertEqual(action96["info_manager_hud_shim"]["callback_calls"], [
            {"kind": "0x2", "player_id": "0x1", "timer_value": "0x0"},
            {"kind": "0x2", "player_id": "0x1", "timer_value": "0x1"},
            {"kind": "0x2", "player_id": "0x1", "timer_value": "0x2"},
        ])
        self.assertEqual(action96["action_setter_requests"], [
            {"player": "0x100a000", "action": 96, "callsite": "0x3000000"},
        ])
        self.assertEqual(len(action96["sequence_setter_requests"]), 1)
        self.assertEqual(action96["sequence_setter_requests"][0]["callsite"], "0x4851e7")
        self.assertEqual(action96["sequence_setter_requests"][0]["sequence_argument"], 3)
        self.assertEqual(action96["field_884_writes"], [])
        self.assertEqual(action96["final_action"], 96)
        self.assertEqual(action96["final_field_884"], 0)
        recovery_probe = report["damage_after_transition"]["recovery_gate_probe"]
        pat_graph = report["damage_after_transition"][
            "action97_pat_graph_before_diagnostic_mutation"]
        self.assertEqual([node["sequence"] for node in pat_graph], [0, 1, 2, 3])
        self.assertEqual([node["next_sequence"] for node in pat_graph], [1, 2, 3, 0])
        self.assertEqual([node["previous_sequence"] for node in pat_graph], [3, 0, 1, 2])
        self.assertEqual([node["loop_mode"] for node in pat_graph], [0, 0, 1, 0])
        self.assertTrue(all(node["previous_node"] and node["next_node"]
                            for node in pat_graph))
        self.assertEqual((recovery_probe["authored_loop_mode"],
                          recovery_probe["forced_loop_mode"]), (1, 0))
        self.assertEqual(len(recovery_probe["diagnostic_ticks"]), 120)
        self.assertEqual(recovery_probe["diagnostic_ticks"][0]["authored_pat_sequence"], 3)
        self.assertEqual(recovery_probe["diagnostic_ticks"][-1]["action"], 97)
        self.assertEqual(recovery_probe["action_after_diagnostic"], 97)
        self.assertEqual(recovery_probe["setter_requests"], [])
        input_probe = report["damage_after_transition"]["input_recovery_probe"]
        self.assertEqual(len(input_probe), 10)
        self.assertTrue(all(case["error"] is None for case in input_probe))
        self.assertTrue(all(case["input_update_error"] is None for case in input_probe))
        self.assertTrue(all(case["key_input_after_update"] == case["state"]
                            for case in input_probe))
        self.assertTrue(all(case["action"] == 97 for case in input_probe))
        self.assertTrue(all(case["field_884"] == 0 for case in input_probe))
        self.assertTrue(all(case["action_setters"] == [] and
                            case["sequence_setters"] == [] for case in input_probe))
        self.assertEqual(report["damage_after_transition"]["defender_timer_entry"], "0x46a330")
        self.assertIn(97, report["prepared_pat_actions"])
        self.assertEqual(report["invalid_memory"], [])


if __name__ == "__main__":
    unittest.main()
