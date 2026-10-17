import unittest
from pathlib import Path

from tools.x86_suwako_808_factory_probe import Suwako808FactoryProbe


class Suwako808FactoryProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = Path("original/th123.exe")
        if not cls.exe.is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")

    def test_original_factory_returns_initialized_action_808_object(self):
        result = Suwako808FactoryProbe(self.exe).run(ticks=0)
        self.assertTrue(result["factory_completed"])
        obj = result["factory_return_object"]
        self.assertEqual(obj["vtable"], "0x85f22c")
        self.assertEqual(obj["action"], 808)
        self.assertEqual(obj["sequence"], 1)
        self.assertEqual(obj["render_color_hex"], "ffffffff")
        self.assertEqual(obj["alpha"], 255)
        self.assertEqual(obj["position"], [300.0, 400.0])
        self.assertEqual(obj["field_34c_u32"], 1)
        pat = result["pat_fixture"]
        self.assertEqual(pat["archive"], "th123c.dat")
        self.assertEqual(pat["pat_sha256"], "1e7e06920e9a7a0e8b0ee0fc160a5b2dd3a19f2cdba2ba8144ab969d0a9dc906")
        self.assertEqual([(row["loop_mode"], [f["duration"] for f in row["frames"]])
                          for row in pat["sequences"]], [(1, [2] * 10), (1, [10])])
        seq0, seq1 = pat["sequences"]
        self.assertEqual(seq0["frames"][0]["damage"], 100)
        self.assertEqual(seq0["frames"][0]["collision_boxes"], [])
        self.assertEqual(seq0["frames"][0]["hurt_boxes"], [[-44, -44, 44, 44]])
        self.assertEqual(seq0["frames"][0]["attack_boxes"], [[-32, -32, 32, 32]])
        self.assertEqual(seq1["frames"][0]["damage"], 150)
        self.assertEqual(seq1["frames"][0]["collision_boxes"], [])
        self.assertEqual(seq1["frames"][0]["hurt_boxes"], [])
        self.assertEqual(seq1["frames"][0]["attack_boxes"], [])
        boxes = result["box_sync"]
        self.assertEqual((boxes["sequence_0"]["hit_box_count"],
                          boxes["sequence_0"]["hurt_box_count"]), (1, 1))
        self.assertEqual(boxes["sequence_0"]["hurt_boxes"], [[256, -444, 344, -356]])
        self.assertEqual(boxes["sequence_0"]["hit_boxes"], [[268, -432, 332, -368]])
        for key in ("sequence_1", "sequence_1_restored"):
            self.assertEqual(boxes[key]["frame_data_pointer"], "0x1041000")
            self.assertEqual(boxes[key]["hit_box_count"], 0)
            self.assertEqual(boxes[key]["hurt_box_count"], 0)
            self.assertEqual(boxes[key]["hit_boxes"], [])
            self.assertEqual(boxes[key]["hurt_boxes"], [])
        self.assertEqual({call["helper"] for call in result["box_transform_entries"]}, {"0x4640b0"})
        self.assertEqual(len(result["box_transform_entries"]), 2)
        self.assertEqual(result["box_transform_calls"], [])

    def test_original_update_dispatcher_runs_on_factory_object(self):
        result = Suwako808FactoryProbe(self.exe).run(ticks=40)
        self.assertTrue(result["factory_completed"])
        self.assertIsNone(result["update_error"])
        self.assertEqual(len(result["updates"]), 32)
        self.assertEqual(result["updates"][0]["sequence"], 1)
        self.assertEqual(result["updates"][0]["render_alpha"], 247)
        self.assertEqual(result["updates"][-1]["sequence"], 1)
        self.assertEqual(result["updates"][30]["render_alpha"], 7)
        self.assertEqual(result["updates"][30]["field_34c_u32"], 1)
        self.assertEqual(result["updates"][31]["field_34c_u32"], 0)
        self.assertEqual(result["updates"][31]["dispatcher_eax"], "0x7")
        self.assertTrue(result["dispatcher_reached_terminal_field_zero"])
        self.assertIsNone(result["manager_removed_object"])
        self.assertEqual(result["object_after_updates"]["sequence"], 1)
        self.assertEqual(result["object_after_updates"]["field_34c_u32"], 0)

    def test_remilia_801_crt_init_and_pat_sequence_layout(self):
        if not Path("original/th123c.dat").is_file():
            self.skipTest("local th123c.dat is unavailable")
        result = Suwako808FactoryProbe(
            self.exe, character="remilia", action_id=801).run(ticks=40)
        self.assertTrue(result["crt_init"]["completed"])
        self.assertNotEqual(result["crt_init"]["fiber_index"], "0xffffffff")
        self.assertNotEqual(result["crt_init"]["fiber_slot_value"], "0x0")
        self.assertEqual(result["crt_init"]["invalid_memory"], [])
        crt_tls_alloc = next(row for row in result["allocations"]
                             if row.get("kind") == "crt-HeapAlloc")
        self.assertEqual(crt_tls_alloc["size"], 0x214)
        self.assertTrue(result["factory_completed"])
        obj = result["factory_return_object"]
        self.assertEqual((obj["action"], obj["sequence"], obj["pose_count"]), (801, 1, 2))
        pat_seq1 = result["pat_fixture"]["sequences"][1]
        self.assertEqual(len(pat_seq1["frames"]), 2)
        self.assertEqual(pat_seq1["frames"][0]["damage"], 0)
        self.assertEqual(pat_seq1["frames"][0]["attack_boxes"], [])
        self.assertEqual(result["box_sync"]["sequence_0"]["hit_box_count"], 1)
        self.assertEqual(result["box_sync"]["sequence_1_restored"]["hit_box_count"], 0)
        self.assertIsNone(result["update_error"])
        self.assertEqual(len(result["updates"]), 18)
        self.assertTrue(result["dispatcher_reached_terminal_field_zero"])
        self.assertEqual(result["object_after_updates"]["alpha"], 0)
        self.assertEqual(result["object_after_updates"]["field_34c_u32"], 0)


if __name__ == "__main__":
    unittest.main()
