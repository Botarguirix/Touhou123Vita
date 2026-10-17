import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import analyze_object_motion


class ObjectMotionAnalysisTest(unittest.TestCase):
    def test_pinned_executable_dispatch_and_suwako_808_contract(self):
        exe = Path("original/th123.exe")
        if not exe.is_file():
            self.skipTest("local reference original/th123.exe is unavailable")
        output = io.StringIO()
        with patch.object(sys, "argv", ["analyze_object_motion.py", str(exe)]):
            with contextlib.redirect_stdout(output):
                self.assertEqual(analyze_object_motion.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["update_dispatch"]["suwako_808_update"], {
            "action_id": "0x328", "group": 5, "handler": "0x788d3e",
        })
        self.assertEqual(report["update_dispatch"]["suwako_989_update"], {
            "action_id": "0x3dd", "group": 46, "handler": "0x797884",
        })
        self.assertEqual(report["update_dispatch"]["remilia_801_update"], {
            "action_id": "0x321", "group": 1, "handler": "0x7879da",
        })
        spread = report["remilia_801_spawn_contract"]
        self.assertEqual(spread["sequence_zero_handler"], "0x7879f1")
        self.assertIn("object+0x144 % 3 == 0", spread["cadence"])
        self.assertEqual(spread["factory_dispatch"], "object vtable +0x44")
        self.assertEqual(spread["spawned_action_id"], "0x321 (801)")
        reachable = report["suwako_808_reachable_calls"]
        self.assertEqual(reachable["entry"], "0x788d3e")
        self.assertEqual(reachable["reachable_instruction_count"], 219)
        targets = {call["target"] for call in reachable["direct_calls"]}
        self.assertIn("0x48ce90", targets)
        self.assertIn("0x4397f0", targets)
        self.assertNotIn("0x438fc0", targets)
        self.assertFalse(reachable["geometry_adapter_0x438fc0_reachable"])
        lifecycle = report["suwako_gameobject_manager_lifecycle"]
        self.assertEqual(lifecycle["vtable"], "0x85f28c")
        self.assertEqual(lifecycle["update_slot"], {
            "index": 4, "method": "0x633ce0", "object_callback": "0x004ae380",
        })
        self.assertEqual(lifecycle["iteration"], "0x00633c10")
        self.assertTrue(lifecycle["callback_then_termination_check"])
        self.assertEqual(lifecycle["termination_field"], "object+0x34c")
        self.assertIn("unlink node", lifecycle["zero_behavior"])
        self.assertEqual(lifecycle["evidence_level"],
                         "pinned disassembly plus dynamic Remilia 801 manager lifecycle in ITERATION112; full match and pair-response path remain unverified")
        frame_selection = report["generic_pat_frame_selection"]
        self.assertIn("stores pose at object+0x140", frame_selection["set_pose"])
        self.assertIn("object+0x158 and +0x150", frame_selection["selector"])
        self.assertIn("duration from descriptor+8", frame_selection["descriptor_side_effects"])
        self.assertFalse(frame_selection["copies_collision_boxes"])
        self.assertIn("not written by these functions", frame_selection["evidence_level"])
        box_sync = report["gameobject_box_sync"]
        self.assertEqual(box_sync["function"], "0x465e10")
        self.assertIn("object+0x1cb", box_sync["counts"]["hit_boxes"])
        self.assertIn("object+0x1cc", box_sync["counts"]["hurt_boxes"])
        self.assertEqual(box_sync["arrays"], {
            "hurt": "object+0x1d0", "hit": "object+0x220",
            "rotated_buffers": "object+0x270", "rotation_pointers": "object+0x320",
        })
        self.assertEqual(box_sync["known_object_manager_callsite"], "0x47d1a7")
        self.assertIn("collision resolution not established", box_sync["callsite_role"])
        collision = report["gameobject_collision_pipeline"]
        self.assertEqual(collision["manager_pair_phases"], {
            "projectile": "0x47cb70", "character": "0x47ce20",
        })
        self.assertEqual(collision["hitbox_vs_hurtbox"]["function"], "0x47a5b0")
        self.assertEqual(collision["hitbox_vs_hurtbox"]["hit_count"], "attacker+0x1cb")
        self.assertEqual(collision["hitbox_vs_hurtbox"]["hurt_count"], "target+0x1cc")
        self.assertEqual(collision["hitbox_vs_hurtbox"]["hurt_array"], "target+0x1d0")
        self.assertEqual(collision["hurtbox_vs_hurtbox"]["function"], "0x47a740")
        self.assertIn("exact damage/guard/priority response still needs dynamic pair trace",
                      collision["evidence_level"])
        motion = report["suwako_808_motion_evidence"]
        self.assertEqual(motion["action_initializer_handler"], "0x7997ae")
        self.assertEqual(motion["gravity_subtracted_from_vertical_velocity_per_tick"], 0.20000000298023224)
        self.assertEqual(motion["sequence_zero_object_11c_scalar_delta"], 0.07500000298023224)
        self.assertEqual(motion["sequence_one_object_11c_scalar_delta"], 0.004999999888241291)
        self.assertTrue(motion["sequence_zero_creates_two_child_action_808_objects"])
        gate = motion["owner_action_gate_0x48ce90"]
        self.assertEqual(gate["owner_action_range_when_first_argument_zero"], [0x32, 0x95])
        self.assertEqual(gate["effect_ids"], {
            "second_argument_count": "0xc8", "third_argument_count": "0xc9",
        })
        self.assertEqual(gate["action_808_call_arguments"], [0, 0, 3])
        self.assertIn("three 0xc9 effects", gate["effect_behavior"])
        self.assertFalse(gate["collision_geometry"])
        self.assertIn("owner-action gate", motion["sequence_zero_split_guard"])
        self.assertEqual(motion["split_latch_field"], "object+0x36c = 1")
        self.assertEqual(motion["split_custom_data"]["draws_per_child"], [160, 6])
        self.assertEqual(motion["split_custom_data"]["draw_ranges_if_rng_is_uniform_u32"], {
            "draw160": [0, 159], "draw6": [0, 5],
        })
        self.assertIn("angle and magnitude", motion["split_custom_data"]["initializer_use"])
        self.assertEqual(motion["split_custom_data"]["transform_components"]["object_plus_0xf4"],
                         "sin(angle_degrees) * magnitude")
        self.assertEqual(motion["split_custom_data"]["transform_components"]["object_plus_0xf8"],
                         "cos(angle_degrees) * magnitude")


if __name__ == "__main__":
    unittest.main()
