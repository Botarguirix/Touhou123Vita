import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "analyze_skill_card_routes.py"
SPEC = importlib.util.spec_from_file_location("analyze_skill_card_routes", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SkillCardRouteTests(unittest.TestCase):
    def test_extracts_separate_secondary_and_complete_card_switches(self):
        source = """void handler() {
 switch(*puVar8) {
 case 100:
   FUN_00487ba0(502, iVar11);
   return;
 case 101:
   FUN_00487ba0(0x20a, iVar11);
   return;
 }
 switch(*puVar8) {
 case 100:
   FUN_00487ba0(500, iVar11);
   return;
 case 101:
   FUN_00487ba0(520, iVar11);
   return;
 }
}
"""
        got = MODULE.extract_skill_switches(source)
        self.assertEqual(got[0]["card_actions"], {"100": [502], "101": [522]})
        self.assertEqual(got[1]["card_actions"], {"100": [500], "101": [520]})

    def test_classifies_air_and_ground_routes_from_is_grounded_branch(self):
        source = """void handler() {
 cVar3 = FUN_00463530();
 if (cVar3 == '\\0') {
   switch(*puVar8) { case 100: FUN_00487ba0(502, x); }
 } else {
   switch(*puVar8) { case 100: FUN_00487ba0(500, x); }
 }
}
"""
        switches = MODULE.extract_skill_switches(source)
        MODULE.classify_ground_context(source, switches)
        self.assertEqual([item["context"] for item in switches], ["airborne", "grounded"])

    def test_real_reimu_mapping_covers_all_skill_cards_and_pat_actions(self):
        root = Path(__file__).resolve().parents[1]
        report = MODULE.analyze(
            root / "original/th123.exe",
            root / "artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/004ae670.c",
            root / "artifacts/extracted/data/csv/reimu/spellcard.csv",
            root / "artifacts/extracted/data/csv/reimu/deck.csv",
            root / "artifacts/pat-detail.tsv",
            root / "artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/manifest.tsv",
        )
        self.assertEqual(report["skill_card_count"], 12)
        self.assertEqual(report["complete_skill_card_switch_line"], 415)
        self.assertEqual(report["complete_skill_card_switch_context"], "grounded")
        self.assertEqual([item["context"] for item in report["ghidra_handler_switches"]],
                         ["airborne", "grounded"])
        self.assertEqual(
            [(row["card_id"], row["action_id"]) for row in report["routes"]],
            [(100, 500), (101, 520), (102, 540), (103, 560),
             (104, 505), (105, 525), (106, 545), (107, 565),
             (108, 510), (109, 530), (110, 550), (111, 570)],
        )
        self.assertEqual(report["default_skill_cards"], [100, 100, 101, 101, 102, 102, 103, 103])
        self.assertTrue(all(row["pat_poses"] > 0 for row in report["routes"]))
        gate = report["activation_gate"]
        self.assertEqual(gate["skill_frame_requirement"]["cancellable_mask"], "0x20")
        self.assertEqual(gate["sequence_cancel_window"]["action_lock_offset"], "0x12")
        self.assertEqual(gate["sequence_cancel_window"]["maximum_exclusive"], 51)
        self.assertEqual(gate["status_gates"]["stopwatch_time_left_offset"], "0x84c")
        self.assertEqual(gate["card_gate"]["air_routes"],
                         "8 explicit skill cards; four IDs have no air switch case")


if __name__ == "__main__":
    unittest.main()
