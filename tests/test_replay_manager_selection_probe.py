import unittest
from pathlib import Path

from tools.x86_replay_manager_selection_probe import analyze


class ReplayManagerSelectionProbeTests(unittest.TestCase):
    def test_story_modes_and_separate_input_source_setup(self):
        exe = Path(r"F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe")
        if not exe.is_file():
            self.skipTest("the user-provided compatible 2009 executable is unavailable")
        report = analyze(exe)
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["story_modes_observed"]["0"]["initializer"], "0x0043b440")
        self.assertEqual(report["story_modes_observed"]["6"]["initializer"], "0x004378d0")
        self.assertEqual(report["input_state_global_va"], "0x0085ec98")
        self.assertTrue(report["checks"]["mode_6_setup_initializes_both_input_slots"])
        self.assertTrue(report["checks"]["mode_6_setup_links_story_input_global"])
        self.assertTrue(report["checks"]["mode_6_setup_schedules_lifecycle_state_2"])
        self.assertIn("does not prove both source-presence flags",
                      report["mode_6_input_setup"]["scope"])
        self.assertTrue(report["checks"]["input_backend_dispatcher_uses_mode_indexed_table"])
        self.assertTrue(report["checks"]["input_backend_mode_6_uses_common_setup_path"])
        self.assertTrue(report["checks"]["input_backend_mode_6_does_not_assign_source_pointer_slots"])
        self.assertTrue(report["checks"]["input_backend_mode_3_assigns_two_source_pointer_slots"])
        self.assertEqual(report["input_backend_mode_6"]["target_va"], "0x0043e122")
        self.assertEqual(report["input_backend_mode_6"]["comparison_mode_3_target_va"],
                         "0x0043e0a0")
        self.assertIn("mode 6's effective +0xf0 still depends",
                      report["input_backend_mode_6"]["scope"])
        self.assertTrue(report["checks"]["input_backend_mode_table_matches_all_eight_entries"])
        self.assertTrue(report["checks"]["input_backend_single_source_modes_write_one_slot"])
        self.assertTrue(report["checks"]["input_backend_modes_4_and_5_write_manager_source_slots"])
        self.assertTrue(report["checks"]["input_backend_modes_6_and_7_preserve_source_slots_directly"])
        self.assertEqual(report["input_backend_modes"]["1"]["source_slot_effect"],
                         "one source: 0x85ef20 and null")
        self.assertEqual(report["input_backend_modes"]["4"]["source_slot_effect"],
                         "two manager slots: +0x1f0 and +0x1f8")
        self.assertEqual(report["input_backend_modes"]["6"]["source_slot_effect"],
                         "no direct source-slot write; prior values persist")
        self.assertTrue(report["checks"]["input_backend_direct_call_sites_match_observed_callers"])
        self.assertTrue(report["checks"]["input_default_init_direct_call_sites_match_observed_callers"])
        self.assertTrue(report["checks"]["backend_state_handler_guards_dispatch_call"])
        self.assertTrue(report["checks"]["backend_mode_handler_dispatches_only_for_selector_1"])
        self.assertTrue(report["checks"]["backend_mode_handler_mode_0_uses_default_single_source_init"])
        self.assertTrue(report["checks"]["input_config_handler_sets_mode_7_state_1_before_single_source_init"])
        self.assertTrue(report["checks"]["title_rtti_and_update_vtable_slot_match"])
        self.assertTrue(report["checks"]["title_state_12_selects_mode_6_state_2"])
        self.assertTrue(report["checks"]["title_neighboring_states_select_mode_4_and_5"])
        self.assertTrue(report["checks"]["title_replay_selector_zero_requests_story_state_12"])
        self.assertTrue(report["checks"]["title_replay_selection_has_generic_replay_loader_path"])
        self.assertTrue(report["checks"]["story_replay_list_uses_timestamp_character_filename_template"])
        self.assertTrue(report["checks"]["replay_browser_enumerates_rep_files"])
        self.assertTrue(report["checks"]["replay_list_rtti_and_virtual_enumerator_match"])
        self.assertTrue(report["checks"]["replay_list_constructor_sets_rep_filter_and_root"])
        self.assertTrue(report["checks"]["replay_list_virtual_method_calls_directory_enumerator"])
        self.assertTrue(report["checks"]["replay_menu_update_gates_on_active_selection_and_row_type"])
        self.assertTrue(report["checks"]["replay_menu_load_branch_reads_selected_row_components"])
        self.assertTrue(report["checks"]["replay_row_type_flag_is_read_from_indexed_list"])
        self.assertTrue(report["checks"]["lifecycle_state3_dispatches_global_manager_slot1"])
        self.assertTrue(report["checks"]["lifecycle_state5_dispatches_manager_slot2"])
        self.assertTrue(report["checks"]["story_global_manager_slot1_is_47eaa0"])
        self.assertTrue(report["checks"]["story_slot5_47f810_dispatches_slot16_47ee10"])
        self.assertTrue(report["checks"]["story_slot5_decodes_then_dispatches_slot15_counter_once"])
        self.assertTrue(report["checks"]["counter_callback_candidate_uses_different_global_then_increments_counter"])
        self.assertTrue(report["checks"]["story_replay_callback_47ee10_is_a_distinct_vtable_method"])
        title = report["title_scene_transition"]
        self.assertEqual(title["class"], "CTitle")
        self.assertEqual(title["base_classes"], ["CTitle", "CSceneBase", "IScene"])
        self.assertEqual(title["states"]["12"]["target_va"], "0x00426de2")
        self.assertEqual(title["state_12_request"],
                         {"manager_mode": 6, "lifecycle_state": 2})
        self.assertEqual(title["replay_selector_handler_va"], "0x00447c0c")
        self.assertEqual(title["replay_loader_handler_va"], "0x0044a120")
        self.assertEqual(title["story_replay_filename_template"],
                         "replay\\story\\%02d%02d%02d_%02d%02d_%s_story")
        self.assertTrue(title["provided_sanae_replay_matches_story_template"])
        self.assertEqual(title["replay_list_class"], "CReplayList")
        self.assertEqual(title["replay_list_virtual_enumerator_va"], "0x0043c140")
        self.assertEqual(title["replay_menu_update_va"], "0x00449fe0")
        self.assertIn("zero flag reads the selected row components",
                      title["replay_selection_gate"])
        lifecycle = title["active_lifecycle_dispatch"]
        self.assertEqual(lifecycle["state3_target_va"], "0x0043d4ca")
        self.assertEqual(lifecycle["manager_slot1_va"], "0x0047eaa0")
        self.assertEqual(lifecycle["manager_slot5_va"], "0x0047f810")
        self.assertEqual(lifecycle["manager_slot15_va"], "0x0047f7c0")
        self.assertEqual(lifecycle["story_replay_callback_slot16_va"], "0x0047ee10")
        self.assertEqual(lifecycle["slot5_to_slot16_callsite_va"], "0x0047f82e")
        self.assertEqual(lifecycle["slot5_to_slot15_helper_callsite_va"], "0x0047f84e")
        self.assertEqual(lifecycle["slot15_helper_dispatch_callsite_va"], "0x00478648")
        self.assertEqual(lifecycle["slot15_method_tailcall_va"], "0x0047f7c9")
        self.assertEqual(lifecycle["counter_callback_candidate_global_va"], "0x0085eb70")
        self.assertIn("not how many slot-5 invocations occur per simulation",
                      lifecycle["scope"])
        self.assertIn("visible label/index mapping", title["scope"])
        self.assertEqual([row["callsite_va"] for row in report["input_backend_callers"]],
                         ["0x00420a91", "0x004258fe"])
        self.assertEqual([row["callsite_va"] for row in report["input_default_init_callers"]],
                         ["0x004258ec", "0x0044b091"])
        self.assertIn("dynamic", report["input_backend_callers"][0]["context"])
        self.assertIn("not the Story selector-6 path",
                      report["input_backend_callers"][1]["context"])
        self.assertIn("not evidence of Story replay setup",
                      report["input_default_init_callers"][1]["context"])
        self.assertTrue(report["checks"]["story_callback_gets_input_global_before_replay_decoder"])
        self.assertTrue(report["checks"]["input_source_writer_uses_same_input_global"])
        self.assertEqual(report["candidate_mode_path"]["arguments_pushed"], [2, 6])
        self.assertIn("does not prove that this branch is reached", report["scope"])


if __name__ == "__main__":
    unittest.main()
