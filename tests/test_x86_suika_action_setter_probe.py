import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "x86_suika_action_setter_probe.py"
SPEC = importlib.util.spec_from_file_location("x86_suika_action_setter_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SuikaActionSetterProbeTests(unittest.TestCase):
    def test_623b_level9_original_factory_creates_821_and_authored_hit_is_800(self):
        report = MODULE.run_action(530, ROOT / "original", (821,),
                                   resolve_child_pair=True,
                                   execute_original_rng=True)
        self.assertIsNone(report["error"])
        self.assertEqual(report["update"]["stop_reason"], "returned-to-stop")
        self.assertEqual(len(report["object_create_calls"]), 1)
        self.assertEqual(report["object_create_calls"][0]["requested_action_object"], "0x335")
        self.assertEqual(report["factory_entry_observations"][0]["custom_data_floats"],
                         [-80.0, 25.0, 0.0])
        self.assertEqual(len(report["factory_entry_observations"]), 1)
        spawn_tick = report["update"]["ticks"][19]
        self.assertEqual((spawn_tick["tick"], spawn_tick["pose"]), (20, 7))
        self.assertEqual(len(spawn_tick["object_create_calls"]), 1)
        self.assertEqual(spawn_tick["object_create_calls"][0]["requested_action_object"], "0x335")
        self.assertEqual([(row["limit"], row["result"]) for row in report["rng_observations"]
                          if row["tick"] == 20], [(60, 48), (5, 0), (5, 4), (360, 300)])
        self.assertEqual(report["factory_action_observations"][0]["random_state"],
                         [-18.0, -2.0, 1.2000000476837158, 1.2000000476837158, 300.0])
        child = report["spawned_object"]["all_factory_children"][0]
        self.assertEqual(child["factory_return"]["action"], 821)
        self.assertEqual(child["factory_return"]["sequence"], 0)
        self.assertEqual(child["factory_return"]["pose_count"], 9)
        self.assertEqual(child["factory_return"]["alpha"], 0)
        self.assertEqual(child["factory_return"]["anchor_position"], [320.0, 180.0])
        self.assertAlmostEqual(child["factory_return"]["position"][0],
                               320 + 25 * 0.984807753, places=3)
        self.assertAlmostEqual(child["factory_return"]["position"][1],
                               180 + 100 - 18 - 25 * 0.173648178 * 0.2, places=3)
        self.assertEqual(child["updates"][0]["frame_damage"], 800)
        pair = report["spawned_object"]["pair_dispatch"]
        self.assertEqual(pair["defender"]["hp_before"], 1000)
        self.assertEqual(pair["defender"]["hp_after"], 200)
        self.assertTrue(pair["pair_phase"]["reached_hit_response"])
        self.assertIsNone(pair["pair_phase"]["error"])

        # The successful hit above deliberately pins the actors together.
        # Without that controlled contact, this fixture's factory child starts
        # at its authored spawn coordinates and retires after two updates;
        # this probe does not claim natural target-acquisition parity.
        natural = MODULE.run_action(530, ROOT / "original", (821,),
                                    resolve_child_pair=False,
                                    execute_original_rng=True)
        natural_child = natural["spawned_object"]["all_factory_children"][0]
        self.assertEqual(natural_child["factory_return"]["position"],
                         [344.62017822265625, 261.1317443847656])
        self.assertEqual(natural_child["stop_reason"], "object-inactive")
        self.assertEqual(len(natural_child["updates"]), 2)

        # Keep the PE-created 821 at its natural spawn point and sweep only
        # the defender. Box coordinates use the affine transform verified
        # against the original PE at the pinned regression coordinates.
        sweep = MODULE.run_action(
            530, ROOT / "original", (821,),
            defender_x=344.62017822265625,
            defender_y=261.1317443847656,
            resolve_child_pair=True,
            execute_original_rng=True,
            pin_attacker=False,
            contact_grid=True)
        sweep_child = sweep["spawned_object"]["all_factory_children"][0]
        pair = sweep["spawned_object"]["pair_dispatch"]
        self.assertEqual(sweep_child["factory_return"]["position"],
                         [344.62017822265625, 261.1317443847656])
        self.assertEqual(len(pair["collision_matrix"]), 121)
        center = next(row for row in pair["collision_matrix"]
                      if row["center_offset_x"] == 0 and row["center_offset_y"] == 0)
        self.assertTrue(center["contact"])
        self.assertEqual(pair["actual_geometry_at_spawn"]["return_value"], 1)
        self.assertTrue(pair["pair_phase"]["reached_hit_response"])
        self.assertEqual(pair["pair_phase"]["defender_hp_after"], 200)
        self.assertEqual(sum(row["contact"] for row in pair["collision_matrix"]), 56)

    def test_original_suika_constructor_setter_and_updates_reach_authored_pat_frames(self):
        report = MODULE.run(ROOT / "original")
        rows = report["actions"]
        self.assertEqual([row["action"] for row in rows], [521, 526, 531])
        self.assertEqual([row["sequence"] for row in rows], [0, 0, 0])
        self.assertEqual([row["pose"] for row in rows], [0, 0, 0])
        self.assertEqual([row["pose_count"] for row in rows], [6, 12, 16])
        for row in rows:
            self.assertIsNone(row["error"])
            self.assertEqual(row["eip_after"], "0x3000000")
            self.assertTrue({"0x464930", "0x438ca0", "0x465370", "0x43f2f0", "0x6086a0"}
                            .issubset(row["functions_reached"]))
            self.assertIsNone(row["player_constructor"]["error"])
            self.assertEqual(row["player_constructor"]["eip_after"], "0x3000000")
            self.assertTrue(row["object_manager"]["completed"])
            self.assertEqual(row["object_manager"]["vtable"], "0x85da54")
            seq0 = next(seq for seq in row["pat_fixture"]["sequences"]
                        if seq["sequence"] == 0)
            self.assertEqual(row["pose_count"], len(seq0["frames"]))

        for row, tick_count in zip(rows, (31, 29, 40)):
            if row["action_requested"] == 531:
                self.assertEqual(row["update"]["stop_reason"], "returned-to-stop")
                self.assertIsNone(row["update"]["host_termination"])
                self.assertEqual(row["update"]["ticks"][-1]["eip_after"], "0x3000000")
                self.assertEqual(row["update"]["ticks"][-1]["action"], 531)
                self.assertEqual(row["update"]["ticks"][-1]["pose"], 9)
                self.assertEqual(row["object_create_calls"][0]["requested_action_object"], "0x335")
                self.assertIn("0x6086a0", row["functions_reached"])
            else:
                self.assertEqual(row["update"]["stop_reason"], "host-termination")
                self.assertEqual(row["update"]["host_termination"]["exit_code"], "0xc000000d")
            self.assertEqual(row["update"]["ticks_completed"], tick_count)

        action_521 = next(row for row in rows if row["action_requested"] == 521)
        by_tick = {tick["tick"]: tick for tick in action_521["update"]["ticks"]}
        self.assertEqual((by_tick[12]["sequence"], by_tick[12]["pose"],
                          by_tick[12]["frame_damage"], by_tick[12]["frame_attack_box_count"]),
                         (1, 0, 400, 1))
        self.assertEqual((by_tick[30]["sequence"], by_tick[30]["pose"],
                          by_tick[30]["frame_damage"], by_tick[30]["frame_attack_box_count"]),
                         (3, 0, 600, 1))
        action_531 = next(row for row in rows if row["action_requested"] == 531)
        self.assertEqual((action_531["update"]["sequence"], action_531["update"]["pose"]),
                         (0, 9))
        self.assertEqual(action_531["update"]["ticks"][-1]["frame_damage"], 0)
        self.assertEqual(action_531["update"]["ticks"][-1]["frame_attack_box_count"], 0)
        self.assertEqual(action_531["object_create_calls"][0]["requested_action_object"], "0x335")
        self.assertEqual(action_531["object_create_calls"][0]["stack_args"][1:4],
                         ["0x43d20000", "0x43340000", "0x1"])
        child = action_531["spawned_object"]
        self.assertEqual(child["factory_return"]["action"], 821)
        self.assertEqual(child["factory_return"]["sequence"], 0)
        self.assertEqual(child["factory_return"]["pose_count"], 9)
        self.assertEqual(child["factory_return"]["position"], [420.0, 180.0])
        self.assertEqual(child["box_sync"]["hit_boxes"], [[-50, -50, 50, 50]])
        self.assertEqual(child["pair_dispatch"]["attacker"]["transform_mode"],
                         "original 0x465e10 box synchronization; both combatants synchronized consistently")
        self.assertEqual(child["box_sync"]["hit_box_count"], 1)
        self.assertEqual(child["updates"][0]["frame_damage"], 800)
        self.assertEqual(child["updates"][-1]["frame_damage"], 800)
        self.assertEqual(child["updates"][-1]["alpha"], 5)
        self.assertEqual(child["updates"][-1]["active"], 0)
        self.assertEqual(len(child["updates"]), 27)
        self.assertTrue(all(tick["eip_after"] == "0x3000000" and tick["error"] is None
                            for tick in child["updates"]))
        self.assertEqual(child["updates"][0]["tick"], 1)
        self.assertEqual(child["updates"][0]["active"], 1)
        self.assertEqual(child["updates"][0]["position"], [420.0, 180.0])
        visual = child["secondary_visual"]
        self.assertEqual(visual["setter_return"]["action"], 821)
        self.assertEqual(visual["setter_return"]["sequence"], 1)
        self.assertEqual(visual["setter_return"]["pose_count"], 1)
        self.assertEqual(visual["stop_reason"], "object-inactive")
        self.assertEqual(len(visual["updates"]), 27)
        self.assertEqual(visual["updates"][0]["position"], [420.0, 180.0])
        self.assertEqual(visual["updates"][0]["alpha"], 255)
        self.assertEqual(visual["updates"][1]["position"], [420.0, 179.5])
        self.assertEqual(visual["updates"][1]["alpha"], 245)
        self.assertEqual(visual["updates"][25]["position"], [420.0, 17.5])
        self.assertEqual(visual["updates"][25]["alpha"], 5)
        self.assertEqual(visual["updates"][25]["active"], 1)
        self.assertEqual(visual["updates"][26]["position"], [420.0, 17.5])
        self.assertEqual(visual["updates"][26]["active"], 0)
        self.assertTrue(all(tick["eip_after"] == "0x3000000" and tick["error"] is None
                            for tick in visual["updates"]))
        pair = child["pair_dispatch"]
        self.assertEqual(pair["geometry"]["return_value"], 1)
        self.assertEqual(pair["actual_geometry_at_spawn"]["return_value"], 1)
        self.assertIn("same world-space mode", pair["geometry_scope"])
        self.assertEqual(pair["collision_matrix"][6]["attacker_boxes_world"],
                         [[370, -230, 470, -130]])
        self.assertEqual(pair["collision_matrix"][6]["defender_boxes_world"],
                         [[393, -338, 448, -180]])
        self.assertEqual([row["center_offset_y"] for row in pair["collision_matrix"]],
                         [-300.0, -250.0, -200.0, -150.0, -100.0, -50.0, 0.0,
                          50.0, 100.0, 150.0, 200.0, 250.0, 300.0])
        self.assertEqual([row["contact"] for row in pair["collision_matrix"]],
                         [False] * 6 + [True] * 5 + [False] * 2)
        self.assertTrue(pair["pair_phase"]["reached_projectile_filter"])
        self.assertTrue(pair["pair_phase"]["reached_character_resolver"])
        self.assertTrue(pair["pair_phase"]["reached_hit_response"])
        self.assertEqual(pair["pair_phase"]["defender_hp_before"], 1000)
        self.assertEqual(pair["pair_phase"]["defender_hp_after"], 200)
        self.assertEqual(pair["pair_phase"]["hp_writes"][0]["eip"], "0x47b6ad")
        self.assertEqual(pair["pair_phase"]["defender_action_after"], 602)
        self.assertEqual(pair["pair_phase"]["defender_collision_type_after"], 0)
        self.assertEqual(pair["pair_phase"]["defender_reaction_timer_194"], 20)
        self.assertEqual(pair["pair_phase"]["projectile_collision_type_190"], 9)
        self.assertIsNone(pair["pair_phase"]["error"])
        self.assertEqual(len(pair["effect_manager"]["requests"]), 3)
        reaction = pair["defender_reaction_update"]
        self.assertEqual(reaction["before"]["timer_194"], 20)
        self.assertEqual(reaction["baseline_update_without_spell_bg"]["host_termination"]["exit_code"],
                         "0xc000000d")
        self.assertEqual(reaction["spell_bg_deque_fixture"]["member"],
                         "Player+0x72c (spellBgTextures)")
        self.assertTrue(reaction["spell_bg_deque_fixture"]["synthetic_handles"])
        self.assertEqual(len(reaction["updates"]), 50)
        self.assertTrue(all(tick["completed"] and tick["exit"] == "0x599fb0"
                            for tick in reaction["updates"]))
        self.assertTrue(all(tick["timer_194"] == 20 for tick in reaction["updates"]))
        self.assertEqual(reaction["updates"][0]["spell_bg_id_742"], 6)
        self.assertEqual(reaction["updates"][0]["spell_bg_timer_740"], 2)
        self.assertEqual((reaction["updates"][49]["action"],
                          reaction["updates"][49]["pose"]), (0, 0))
        self.assertEqual(reaction["after"]["action"], 0)
        self.assertEqual(reaction["after"]["timer_194"], 20)
        self.assertTrue(reaction["updates"][49]["completed"])


if __name__ == "__main__":
    unittest.main()

