import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Bg33StageContractTests(unittest.TestCase):
    def test_viewer_loads_the_original_24_tile_layout_and_constructor_sprites(self):
        source = (ROOT / "legacy/src/vita_main.c").read_text(encoding="utf-8")
        self.assertIn('!strcmp(stage_names[stage_index],"bg33")?24u:30u', source)
        self.assertIn('"data/background/bg33/0001.cv2","data/background/bg33/0002.cv2"', source)
        self.assertIn('t123_stage_animation_update(33u,&stage_bg33_counter)', source)
        self.assertIn('stage_bg33_counter>>8', source)
        self.assertIn('stage_layer=(stage_layer+1)%4;', source)
        self.assertIn('stage_bg33_tiles_loaded==24', source)
        self.assertIn('stage_bg33_layout_captured', source)
        self.assertIn('"BG33 6x4 source layout + constructor sprite anchors"', source)
        self.assertIn('stage_bg33_slot_mask==0x3fffffffu', source)
        self.assertIn("soft2d_draw_texture_quad(tile,qx,qy)", source)
        self.assertIn("stage_bg33_quad_draws==30u", source)
        self.assertIn('stage-bg33-scroll.bmp', source)

    def test_bg33_runtime_view_uses_slot_translation_without_double_anchors(self):
        source = (ROOT / "legacy/src/vita_main.c").read_text(encoding="utf-8")
        core = (ROOT / "legacy/src/stage.c").read_text(encoding="utf-8")
        self.assertIn('t123_bg33_project_slot_quad(&draw,0,0,1,0,0,0,0,1,1,&quad)', source)
        self.assertIn('soft2d_draw_texture_quad(tile,qx,qy)', source)
        self.assertIn('out->x = 0;', core)
        self.assertIn('out->y = scroll_y;', core)

    def test_update_contract_masks_the_1024_tick_cycle(self):
        source = (ROOT / "legacy/src/stage.c").read_text(encoding="utf-8")
        self.assertIn("if (stage_id == 33u)", source)
        self.assertIn("*counter = (*counter + 1u) & 0x3ffu;", source)

    def test_vita3k_gate_executes_the_shared_viewport_transform_contract(self):
        source = (ROOT / "legacy/src/vita_main.c").read_text(encoding="utf-8")
        runner = (ROOT / "tools/vita3k-test.ps1").read_text(encoding="utf-8")
        self.assertIn("stage_viewport_contract_seen=probe_stage_viewport_contract()", source)
        self.assertIn("stage_bg33_quad_contract_seen=probe_bg33_quad_contract()", source)
        self.assertIn("!$result.stage_bg33_quad_contract", runner)
        self.assertIn('schema\\":46', source)
        self.assertIn("!$result.stage_viewport_contract", runner)


if __name__ == "__main__":
    unittest.main()
