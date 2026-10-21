import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from x86_stage_camera_oracle import (original_camera_state,
                                     original_camera_constructor,
                                     original_camera_update,
                                     original_target_zoom,
                                     EXPECTED_SHA256)
from x86_sprite_vtable_probe import probe as sprite_vtable_probe
from x86_sprite_quad_probe import probe as sprite_quad_probe
from x86_sprite_component_probe import probe as sprite_component_probe


class StageCameraOracleTests(unittest.TestCase):
    def test_vita_formula_matches_original_x86_camera_method(self):
        vectors = (
            ((200.0, 200.0, 0.0, 0.0), 1.0),
            ((200.0, 300.0, 0.0, 100.0), 0.97361630),
            ((200.0, 900.0, 0.0, 0.0), 0.82051283),
            ((200.0, 2200.0, 0.0, 0.0), 0.5),
            ((200.0, 440.0, 100.0, 200.0), 0.97361630),
        )
        for points, expected in vectors:
            with self.subTest(points=points):
                actual = original_target_zoom(*points)
                self.assertTrue(math.isclose(actual, expected, rel_tol=2e-6, abs_tol=2e-6))

    def test_core_uses_x86_horizontal_floor_vertical_weight_and_zoom_floor(self):
        source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        camera = source.split("int t123_stage_camera_pair_target", 1)[1].split("void t123_bg36_scroll_init", 1)[0]
        for expression in (
            "fabsf(player0_x - player1_x) + 80.0f",
            "if (horizontal < 640.0f) horizontal = 640.0f",
            "fabsf(player0_y - player1_y) * 1.5f",
            "sqrtf(horizontal * horizontal + vertical * vertical)",
            "640.0f / out->distance",
            "if (out->zoom < 0.5f) out->zoom = 0.5f",
        ):
            self.assertIn(expression, camera)

    def test_vertical_target_weight_uses_current_zoom_and_stage_clamp(self):
        cases = ((1.0, -100.0), (0.8, -60.0),
                 (0.59145278, -18.29055595), (0.5, 0.0))
        for zoom, expected in cases:
            with self.subTest(zoom=zoom):
                observed = original_camera_state(
                    200, 900, 0, -500,
                    initial=(0, 0, .5, zoom, .5, 0, 0))[1]
                self.assertTrue(math.isclose(observed, expected, abs_tol=2e-5))
        for y0, y1, expected in ((271, 300, -271.0), (500, 500, -420.0),
                                 (3000, 3500, -420.0)):
            observed = original_camera_state(
                300, 400, y0, y1,
                initial=(0, 0, .5, 1.0, .5, 0, 0))[1]
            self.assertAlmostEqual(observed, expected)
        source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        camera = source.split("int t123_stage_camera_y_target", 1)[1].split("int t123_stage_camera_zoom_step", 1)[0]
        self.assertIn("2.0f * current_zoom - 1.0f", camera)
        self.assertIn("minimum_y > 270.0f", camera)

    def test_vertical_easing_snap_and_zoom_bounds_match_x86(self):
        cases = (
            ((200, 900, 0, -500),
             (-100.0, -18.29055595, 0.59145278, 0, -500), -76.820335),
            ((200, 900, 0, -500),
             (-76.820335, -18.29055595, 0.59145278, 0, -500), -72.8938446),
            ((200, 900, 500, 500),
             (0.0, -269.23077, 0.82051283, 500, 500), -27.9230766),
            ((200, 900, 0, 0),
             (-1.0, 0.0, 1.0, 0, 0), 0.0),
        )
        for points, state, expected in cases:
            x0, x1, y0, y1 = points
            current_y, target_y, zoom, player0_y, player1_y = state
            actual = original_camera_update(
                x0, x1, y0, y1,
                state=(550, target_y, zoom, zoom, 550, current_y))[2]
            self.assertTrue(math.isclose(actual, expected, abs_tol=3e-4))
        source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        easing = source.split("int t123_stage_camera_y_step", 1)[1].split("int t123_stage_camera_zoom_step", 1)[0]
        self.assertIn("? 10.0f : 20.0f", easing)
        self.assertIn("difference / divisor + 1.0f", easing)
        self.assertIn("difference / divisor - 1.0f", easing)
        self.assertIn("-420.0f * zoom_factor", easing)

    def test_horizontal_center_limits_match_original_target_method(self):
        cases = (
            ((200, 200, 0, 0), 320.0),
            ((200, 300, 0, 100), 328.67157),
            ((300, 400, 400, 600), 353.41193),
            ((300, 400, 500, 500), 350.0),
            ((200, 900, 0, 0), 550.0),
            ((200, 2200, 0, 0), 960.0),
        )
        for points, expected in cases:
            with self.subTest(points=points):
                center_x, *_ = original_camera_state(*points)
                self.assertTrue(math.isclose(center_x, expected, abs_tol=2e-5))

    def test_full_constructor_sequence_produces_vertical_camera_state(self):
        cases = (
            ((200, 0, 200, 0), (0.0, 0.0, 420.0)),
            ((200, 0, 900, -500), (-18.29056, -76.82034, 786.93622)),
            ((200, 500, 900, 500), (-269.23077, -269.23077, 781.10577)),
        )
        for positions, expected in cases:
            with self.subTest(positions=positions):
                state = original_camera_constructor(*positions)
                # target_y, current_y and final viewport translation Y
                for actual, target in zip((state[1], state[7], state[4]), expected):
                    self.assertTrue(math.isclose(actual, target, abs_tol=3e-4))

    def test_camera_override_flags_read_the_constructor_targets(self):
        x_override = original_camera_state(
            300, 400, 0, 100, flags=(1, 0, 0),
            initial=(0, 0, .5, 0, .5, 700, 0))
        y_override = original_camera_state(
            300, 400, 0, 100, flags=(0, 1, 0),
            initial=(0, 0, .5, 0, .5, 0, 600))
        self.assertEqual(x_override[0:2], (700.0, 420.0))
        self.assertEqual(y_override[0:2], (350.0, 600.0))

    def test_zoom_easing_matches_original_update_method(self):
        zoom_out = original_camera_update(
            200, 900, 0, 0, state=(550, 420, 0.82051283, 1.0, 550, 420))[0]
        zoom_in = original_camera_update(
            200, 200, 0, 0, state=(320, 420, 1.0, 0.5, 320, 420))[0]
        self.assertTrue(math.isclose(zoom_out, 0.96210259, abs_tol=2e-6))
        self.assertTrue(math.isclose(zoom_in, 0.50825, abs_tol=2e-6))
        source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        easing = source.split("int t123_stage_camera_zoom_step", 1)[1].split("void t123_bg36_scroll_init", 1)[0]
        self.assertIn("(target_zoom - current_zoom) / 5.0f - 0.002f", easing)
        self.assertIn("(target_zoom - current_zoom) / 80.0f + 0.002f", easing)

    def test_horizontal_easing_and_zoom_dependent_stage_clamps_match_x86(self):
        vectors = (
            ((200, 900, 0, 0), (550, 420, 0.82051283, 1.0, 400, 0), 410.0),
            ((200, 900, 0, 0), (550, 420, 0.82051283, 1.0, 200, 420), 332.60486),
            ((200, 900, 0, 0), (550, 420, 0.82051283, 1.0, 1000, 0), 947.39514),
        )
        for points, state, expected in vectors:
            with self.subTest(state=state):
                actual = original_camera_update(*points, state=state)[1]
                self.assertTrue(math.isclose(actual, expected, abs_tol=2e-4))
        source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        easing = source.split("int t123_stage_camera_x_step", 1)[1].split("void t123_bg36_scroll_init", 1)[0]
        self.assertIn("difference / 30.0f + 5.0f", easing)
        self.assertIn("difference / 30.0f - 5.0f", easing)
        self.assertIn("1280.0f - half_view", easing)

    def test_player_sprite_renderer_uses_camera_translation_then_zoom(self):
        vtables = sprite_vtable_probe(ROOT / "original" / "th123.exe")
        self.assertTrue(vtables["shared_render_slot"])
        self.assertEqual(vtables["render_target"], "0x00438d20")
        self.assertEqual({entry["target"] for entry in vtables["tables"].values()},
                         {"0x00438d20"})
        quad = sprite_quad_probe(ROOT / "original" / "th123.exe")
        self.assertEqual(quad["resolved_semantics"]["runtime_plus_0x04_plus_0x06"],
                         "PAT ox/oy; sign-extended into sprite component +0xf0/+0xf4")
        self.assertEqual(quad["resolved_semantics"]["runtime_plus_0x0c_through_0x12"],
                         "PAT tx/ty/tw/th; source rectangle passed to texture-quad setup")
        component = sprite_component_probe(ROOT / "original" / "th123.exe")
        self.assertEqual(component["samples"][1]["local_quad"]["top_right"], [64.0, -0.0])
        self.assertEqual(component["samples"][1]["local_quad"]["bottom_left"], [-0.0, 32.0])
        self.assertAlmostEqual(component["samples"][1]["uv_edges"]["right"], 76 / 256)
        self.assertAlmostEqual(component["samples"][1]["uv_edges"]["bottom"], 56 / 256)
        probe = (ROOT / "artifacts" / "kernel" / EXPECTED_SHA256 /
                 "character-camera-transform-probe.tsv").read_text(encoding="utf-8")
        self.assertTrue(probe.startswith(f"# sha256={EXPECTED_SHA256}"))
        self.assertIn("00438b56\te8 85 e3 fc ff\tcall\t0x406ee0", probe)
        self.assertIn("00438b5b\t56\tpush\tesi", probe)
        self.assertIn("00438b5c\tb9 00 86 89 00\tmov\tecx, 0x898600", probe)
        self.assertIn("00438b61\te8 8a 08 ff ff\tcall\t0x4293f0", probe)
        caller = (ROOT / "artifacts" / "kernel" / EXPECTED_SHA256 / "character-render-camera-probe.tsv").read_text(encoding="utf-8")
        self.assertIn("00438d2e\te8 9d fc ff ff\tcall\t0x4389d0", caller)
        self.assertIn("vtable\t0085bf4c\t11\t00438d20", (ROOT / "artifacts" / "kernel" / EXPECTED_SHA256 / "manifest.tsv").read_text(encoding="utf-8"))
        self.assertIn("00438b1a\td8 a6 f4 00 00 00\tfsub\tdword ptr [esi + 0xf4]", caller)
        self.assertIn("00438b43\td8 8e f0 00 00 00\tfmul\tdword ptr [esi + 0xf0]", caller)
        init = (ROOT / "artifacts" / "kernel" / EXPECTED_SHA256 / "player-render-init-full.tsv").read_text(encoding="utf-8")
        self.assertIn("004666b4\t89 87 54 01 00 00\tmov\tdword ptr [edi + 0x154], eax", init)
        self.assertIn("00466761\te8 fa 04 fa ff\tcall\t0x406c60", init)
        self.assertIn("00466778\td9 99 f0 00 00 00\tfstp\tdword ptr [ecx + 0xf0]", init)
        self.assertIn("00466790\td9 98 f4 00 00 00\tfstp\tdword ptr [eax + 0xf4]", init)
        self.assertIn("00438d24\t8b 8e 54 01 00 00\tmov\tecx, dword ptr [esi + 0x154]", caller)
        self.assertIn("00429401\td9 46 10\tfld\tdword ptr [esi + 0x10]", probe)
        self.assertIn("00429415\td9 46 14\tfld\tdword ptr [esi + 0x14]", probe)
        stage = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        projection = stage.split("int t123_stage_camera_project", 1)[1].split("void t123_bg36_scroll_init", 1)[0]
        self.assertIn("(world_x - camera->x - viewport_x) * camera->zoom + 320.0f", projection)
        self.assertIn("(world_y - camera->y - viewport_y) * camera->zoom + 420.0f", projection)
        fight = (ROOT / "legacy" / "src" / "fight.c").read_text(encoding="utf-8")
        self.assertIn("t123_stage_camera_step(&g->camera", fight)
        self.assertIn("-(float)g->p[0].y", fight)
        vita = (ROOT / "legacy" / "src" / "vita_main.c").read_text(encoding="utf-8")
        self.assertIn("T123StageCamera camera=g->scene==SCENE_FIGHT?g->camera", vita)
        self.assertIn("t123_stage_camera_project(&camera,world_x,world_y", vita)
        self.assertIn("float world_x=g->scene==SCENE_FIGHT?(float)p->x:", vita)
        self.assertIn("float world_y=g->scene==SCENE_FIGHT?-(float)p->y:0.0f", vita)
        # Remilia 801, like Suika 821, now carries full fractional world
        # coordinates. Both must reach the same camera projection unrounded.
        self.assertIn("float object_x=(o->action==821||o->action==801)?o->world_x:(float)o->x", vita)
        self.assertIn("float object_y=(o->action==821||o->action==801)?o->world_y:(float)o->y", vita)
        self.assertIn("t123_stage_camera_project(&camera,object_x,-object_y", vita)
        self.assertIn("screen_x-p->face*(float)pose->ox*zoom", vita)
        self.assertIn("screen_y-(float)pose->oy*zoom", vita)
        self.assertIn("soft2d_draw_texture_region_scale_alpha(t,pose->tx,pose->ty,(int)pose->tx+pose->tw", vita)
        self.assertIn("sprite_region_crop_contract_seen=soft2d_texture_region_crop_contract()", vita)
        self.assertIn("&&sprite_region_crop_contract_seen&&", vita)
        soft2d = (ROOT / "legacy" / "src" / "soft2d.c").read_text(encoding="utf-8")
        self.assertIn("soft2d_draw_texture_region_scale(&texture,1,1,3,3,20,20,1,1)", soft2d)
        self.assertIn("soft2d_draw_texture_region_scale_alpha(&texture,0,0,1,1,40,40,1,1,128)", soft2d)
        runner = (ROOT / "tools" / "vita3k-test.ps1").read_text(encoding="utf-8")
        self.assertIn("!$result.sprite_region_crop_contract", runner)
        pattern = (ROOT / "legacy" / "src" / "pattern.c").read_text(encoding="utf-8")
        self.assertIn("f->tx=(int16_t)get16(v+4);f->ty=(int16_t)get16(v+6);f->tw=(int16_t)get16(v+8);f->th=(int16_t)get16(v+10)", pattern)


if __name__ == "__main__":
    unittest.main()
