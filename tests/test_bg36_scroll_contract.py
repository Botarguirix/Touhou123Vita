import hashlib
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))
import pefile

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


class Bg36ScrollContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe_path = ROOT / "original" / "th123.exe"
        cls.exe = cls.exe_path.read_bytes()
        cls.digest = hashlib.sha256(cls.exe).hexdigest()
        cls.pe = pefile.PE(data=cls.exe, fast_load=True)
        cls.image_base = cls.pe.OPTIONAL_HEADER.ImageBase

    def bytes_at(self, va, size):
        return self.pe.get_data(va - self.image_base, size)

    def test_constructor_and_update_constants_match_the_pinned_pe(self):
        self.assertEqual(self.digest, EXPECTED_SHA256)
        vtable = struct.unpack("<6I", self.bytes_at(0x85B094, 24))
        self.assertEqual(vtable[1], 0x476260)
        self.assertEqual(vtable[4], 0x4757A0)
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85B004, 4))[0], -400.0)
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85B000, 4))[0], -300.0)
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85AFEC, 4))[0], -1200.0)
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85AFE8, 4))[0], 800.0)
        self.assertEqual(struct.unpack("<d", self.bytes_at(0x85AFE0, 8))[0], -800.0)
        self.assertEqual(struct.unpack("<d", self.bytes_at(0x8581B8, 8))[0], 1.5)
        self.assertEqual(struct.unpack("<d", self.bytes_at(0x8677C8, 8))[0], 1.0)

        constructor = self.bytes_at(0x4761EE, 0x2E)
        self.assertIn(bytes.fromhex("d9 05 04 b0 85 00 d9 5b 68"), constructor)
        self.assertIn(bytes.fromhex("d9 05 00 b0 85 00 8b c3 d9 5b 6c"), constructor)
        update = self.bytes_at(0x476260, 0x60)
        self.assertIn(bytes.fromhex("dc 25 b8 81 85 00"), update)
        self.assertIn(bytes.fromhex("dc 25 c8 77 86 00"), update)

    def test_render_method_animates_the_two_cloud_layers(self):
        render = self.bytes_at(0x4759DC, 0x1A0)
        self.assertIn(bytes.fromhex("d9 46 68"), render)
        self.assertIn(bytes.fromhex("d9 05 f4 af 85 00"), render)
        self.assertIn(bytes.fromhex("81 c1 d0 01 00 00"), render)  # slot 2: clowd_l
        self.assertIn(bytes.fromhex("d9 46 6c"), render)
        self.assertIn(bytes.fromhex("d9 05 f0 af 85 00"), render)
        self.assertIn(bytes.fromhex("81 c1 b8 02 00 00"), render)  # slot 3: clowd_s
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85AFF4, 4))[0], -750.0)
        self.assertEqual(struct.unpack("<f", self.bytes_at(0x85AFF0, 4))[0], -320.0)

        bg36_render = self.bytes_at(0x4757A0, 0x400)
        self.assertIn(bytes.fromhex("81 c1 d0 01 00 00"), bg36_render)  # clowd_l at +0x1d0
        self.assertIn(bytes.fromhex("81 c1 b8 02 00 00"), bg36_render)  # clowd_s at +0x2b8
        self.assertIn(bytes.fromhex("d9 46 68"), bg36_render)  # clowd_l x +0x68
        self.assertIn(bytes.fromhex("d9 46 6c"), bg36_render)  # clowd_s x +0x6c
        self.assertIn(bytes.fromhex("d9 05 f4 af 85 00"), bg36_render)  # y=-750
        self.assertIn(bytes.fromhex("d9 05 f0 af 85 00"), bg36_render)  # y=-320
        full_bg36_render = self.bytes_at(0x4757A0, 0x710)
        cloud_l_pass = full_bg36_render.index(bytes.fromhex("e8 99 55 38 00"))
        cloud_s_pass = full_bg36_render.index(bytes.fromhex("e8 2f 54 38 00"))
        tile_pass = full_bg36_render.index(bytes.fromhex("e8 1c 97 ff ff"))
        torii_pass = full_bg36_render.index(bytes.fromhex("e8 04 52 38 00"))
        self.assertLess(cloud_l_pass, cloud_s_pass)
        self.assertLess(cloud_s_pass, tile_pass)
        self.assertLess(tile_pass, torii_pass)

        source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        vita_source = (ROOT / "legacy" / "src" / "vita_main.c").read_text(encoding="utf-8")
        bg36_page = vita_source.split('stage_layer==2&&!strcmp(stage_names[stage_index],"bg36")', 1)[1].split('stage_layer==2&&(!strcmp(stage_names[stage_index],"bg37")', 1)[0]
        self.assertIn("for(unsigned i=0;i<4;i++)if(stage_extras[i])", bg36_page)
        self.assertIn("t123_bg36_project_aux_quad(i", bg36_page)
        self.assertIn("const float anchor_x[4]={0.0f,0.0f,stage_bg36_scroll.clowd_l_x,stage_bg36_scroll.clowd_s_x}", bg36_page)
        self.assertIn("const float anchor_y[4]={0.0f,0.0f,-750.0f,-320.0f}", bg36_page)
        self.assertIn("float fit_x=extent_x>0.0f?139.0f/extent_x:1.0f", bg36_page)
        self.assertIn("stage_bg36_aux_projection_contract_seen=probe_bg36_aux_projection_contract()", vita_source)
        self.assertIn("stage_camera_pair_contract_seen=probe_stage_camera_pair_contract()", vita_source)
        self.assertIn("stage_camera_pair_contract", (ROOT / "tools" / "vita3k-test.ps1").read_text(encoding="utf-8"))
        self.assertIn("stage_bg36_aux_projection_contract_seen&&", vita_source)
        self.assertIn("stage_bg36_aux_projection_contract", (ROOT / "tools" / "vita3k-test.ps1").read_text(encoding="utf-8"))
        self.assertIn("stage_bg36_cloud_quads_projected>=2", vita_source)
        self.assertIn("stage_bg36_cloud_quads_projected -lt 2", (ROOT / "tools" / "vita3k-test.ps1").read_text(encoding="utf-8"))
        battle_bg36 = vita_source.split("static void draw_battle_bg36", 1)[1].split("static void stage_load_extras", 1)[0]
        self.assertIn("if(!battle_bg33_ready&&!battle_bg36_ready){", vita_source)
        self.assertIn("RGBA8(126,206,244,255)", vita_source)
        battle_draw_order = vita_source.split("static void draw_battle_bg36(const Fight *g){", 1)[1].split("static void stage_load_extras", 1)[0]
        self.assertLess(battle_draw_order.index("draw_battle_bg36_aux(g,2u"), battle_draw_order.index("for(unsigned slot=0;slot<30;slot++)"))
        self.assertLess(battle_draw_order.index("draw_battle_bg36_aux(g,3u"), battle_draw_order.index("for(unsigned slot=0;slot<30;slot++)"))
        self.assertLess(battle_draw_order.index("for(unsigned slot=0;slot<30;slot++)"), battle_draw_order.index("draw_battle_bg36_aux(g,0u"))
        self.assertLess(battle_draw_order.index("draw_battle_bg36_aux(g,0u"), battle_draw_order.index("draw_battle_bg36_aux(g,1u"))
        self.assertIn("t123_bg36_project_aux_quad(i", battle_bg36)
        self.assertIn("g->camera.zoom", battle_bg36)
        self.assertIn("if(i==2u)x=battle_bg36_scroll.clowd_l_x", battle_bg36)
        self.assertIn("else if(i==3u)x=battle_bg36_scroll.clowd_s_x", battle_bg36)
        self.assertNotIn("else if(i==0u)x=", battle_bg36)
        self.assertIn("battle_bg36_capture_camera_x=g.camera.x", vita_source)
        self.assertIn("battle_bg36_capture_camera_y=g.camera.y", vita_source)
        self.assertIn("battle_bg36_capture_camera_zoom=g.camera.zoom", vita_source)
        self.assertIn("battle_bg36_capture_camera_x", vita_source)
        self.assertIn("battle_bg36_capture_camera_zoom", vita_source)
        self.assertIn("battle_bg36_capture_camera_zoom", (ROOT / "tools" / "vita3k-test.ps1").read_text(encoding="utf-8"))
        self.assertIn("battle_bg36_draw_mask==15u", vita_source)
        self.assertIn("battle_bg36_draw_mask -ne 15", (ROOT / "tools" / "vita3k-test.ps1").read_text(encoding="utf-8"))
        # Projection evidence is a sticky run-wide diagnostic: stage navigation
        # reinitializes scroll state, but must not erase an already rendered page.
        stage_step = vita_source.split("static int stage_step", 1)[1].split("static int gallery_step", 1)[0]
        self.assertNotIn("stage_bg36_cloud_quads_projected=0", stage_step)
        stage_source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        self.assertIn("float pivot_x = (aux_slot == 0u || aux_slot == 1u || aux_slot == 3u) ? width * 0.5f : 0.0f", stage_source)
        self.assertIn("float pivot_y = (aux_slot == 0u || aux_slot == 1u || aux_slot == 3u) ? height : 0.0f", stage_source)
        self.assertIn("(local_x + translation.x) * zoom", stage_source)
        self.assertIn("(local_y + translation.y) * zoom", stage_source)
        self.assertIn("stage_bg36_scroll.clowd_l_x", bg36_page)
        self.assertIn("stage_bg36_scroll.clowd_s_x", bg36_page)
        bg36_constructor = (ROOT / "artifacts" / "kernel" / EXPECTED_SHA256 / "stage-layout" / "00475eb0.c").read_text(encoding="utf-8")
        self.assertLess(bg36_constructor.index("BG36/clowd_l.bmp"), bg36_constructor.index("BG36/clowd_s.bmp"))
        self.assertIn("FUN_00406c60(*(undefined4 *)(iVar1 + 8),0,0,uStack_fc,uStack_100,0,0)", bg36_constructor)
        self.assertIn("FUN_00406c60(*(undefined4 *)(iVar1 + 0xc),0,0,uStack_fc,uStack_100,uStack_fc >> 1,uStack_100)", bg36_constructor)
        self.assertIn("FUN_00406c60(*puVar3,0,0,uStack_fc,uStack_100,uStack_fc >> 1,uStack_100)", bg36_constructor)
        self.assertIn("FUN_00406c60(*(undefined4 *)(iVar1 + 4),0,0,uStack_fc,uStack_100,uStack_fc >> 1,uStack_100)", bg36_constructor)
        renderer_cloud_l = self.bytes_at(0x475A2C, 0xD0)
        renderer_cloud_s = self.bytes_at(0x475B97, 0xD0)
        for render_pass, slot in ((renderer_cloud_l, bytes.fromhex("81 c1 d0 01 00 00")),
                                  (renderer_cloud_s, bytes.fromhex("81 c1 b8 02 00 00"))):
            self.assertIn(bytes.fromhex("d9 46 44"), render_pass)  # shared stage x anchor
            self.assertIn(bytes.fromhex("d9 46 48"), render_pass)  # shared stage y anchor
            self.assertIn(slot, render_pass)
        for statement in (
            "scroll->clowd_l_x = -400.0f",
            "scroll->clowd_s_x = -300.0f",
            "scroll->clowd_l_x -= 1.5f",
            "scroll->clowd_s_x -= 1.0f",
            "scroll->clowd_l_x < -1200.0f",
            "scroll->clowd_s_x < -800.0f",
            "scroll->clowd_l_x = 800.0f",
            "scroll->clowd_s_x = 800.0f",
        ):
            self.assertIn(statement, source)

    def test_missing_edge_tiles_are_requested_by_pe_but_null_safe(self):
        stage_dir = (ROOT / "artifacts" / "kernel" / EXPECTED_SHA256 /
                     "stage-layout")
        constructor = (stage_dir / "00475eb0.c").read_text(encoding="utf-8")
        common_loader = (stage_dir / "0046fe40.c").read_text(encoding="utf-8")
        stage_source = (ROOT / "legacy" / "src" / "stage.c").read_text(encoding="utf-8")
        vita_source = (ROOT / "legacy" / "src" / "vita_main.c").read_text(encoding="utf-8")
        resource_loader = (ROOT / "artifacts" / "kernel" / EXPECTED_SHA256 /
                           "resource-loader" / "00405030.c").read_text(encoding="utf-8")
        self.assertIn("FUN_0046fe40(0x24,0x56,1)", constructor)
        self.assertIn("while ((int)uVar5 < 0x1e)", common_loader)
        self.assertIn("((int)uVar5 % 6) * -0x100 + 700", common_loader)
        self.assertIn("(param_3 - iStack_210) + 0x35c", common_loader)
        self.assertIn("*stage_x = 700.0f - (float)(slot % 6u) * 256.0f", stage_source)
        self.assertIn("*stage_y = 946.0f - (float)(slot / 6u) * 256.0f", stage_source)
        self.assertIn("t123_bg36_project_tile_quad(slot,&g->camera,&quad)", vita_source)
        self.assertIn("row+1u,col+1u", vita_source)
        self.assertIn("battle_bg36_base_tiles,battle_bg36_base_draws,battle_bg36_base_slot_mask,battle_bg36_capture_seen,battle_bg36_loaded", vita_source)
        self.assertIn("battle_bg36_base_tiles==25u", vita_source)
        self.assertIn("battle_bg36_base_draws==25u", vita_source)
        self.assertIn("battle_bg36_base_slot_mask==0x3ffff79cu", vita_source)
        self.assertIn("if (*(int *)(iVar1 + uVar5 * 4) != 0)", common_loader)
        self.assertIn("if (iVar2 < 0)", resource_loader)
        self.assertIn("*param_1 = 0;", resource_loader)

        manifests = (ROOT / "artifacts" / "th105-resource-manifest.tsv",
                     ROOT / "artifacts" / "th123-resource-manifest.tsv")
        from tools.audit_stage_resources import audit
        report = audit(manifests)
        bg36 = next(stage for stage in report["stages"] if stage["stage"] == "bg36")
        self.assertEqual(bg36["missing_base_names"], [
            "0000[01][01].cv2", "0000[01][02].cv2", "0000[01][06].cv2",
            "0000[02][01].cv2", "0000[02][06].cv2",
        ])


if __name__ == "__main__":
    unittest.main()

