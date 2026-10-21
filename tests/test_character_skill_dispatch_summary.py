import tempfile
import unittest
from pathlib import Path

from tools.summarize_character_skill_dispatch import EXPECTED_SHA256, summarize


class CharacterSkillDispatchSummaryTest(unittest.TestCase):
    def test_extracts_selected_action_and_command_mask_from_call_sequence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            handler_map = root / "handlers.tsv"
            handler_map.write_text(
                "sha256\tcharacter\thandleInputs_va\n" + "".join(
                    f"{EXPECTED_SHA256}\t{name}\t{address}\n" for name, address in [
                        ("Suika", "00609dc0"), ("P2", "00609dc0"),
                        ("P3", "00609dc0"), ("P4", "00609dc0"),
                        ("P5", "00609dc0"), ("P6", "00609dc0"),
                        ("P7", "00609dc0"), ("P8", "00609dc0"),
                        ("P9", "00609dc0"), ("P10", "00609dc0"),
                        ("P11", "00609dc0"), ("P12", "00609dc0"),
                        ("P13", "00609dc0"), ("P14", "00609dc0"),
                        ("P15", "00609dc0"), ("P16", "00609dc0"),
                        ("P17", "00609dc0"), ("P18", "00609dc0"),
                        ("P19", "00609dc0"), ("P20", "00609dc0"),
                    ]), encoding="utf-8")
            disassembly_dir = root / "disassembly"
            disassembly_dir.mkdir()
            instructions = [
                "00609dc0\tcmp\tbyte ptr [esi + 0x6ad], 1",
                "00609dc6\tjl\t0x609e4a",
                "00609dc8\tpush\t0x213",
                "00609dcd\tcall\t0x489610",
                "00609dd2\tmovsx\teax, di",
                "00609dd5\tpush\teax",
                "00609dd6\tpush\t0x213",
                "00609ddb\tcall\t0x487ba0",
                "00609de0\ttest\tdword ptr [esi + 0x7c8], 0x400",
                "00609de6\tpush\t0x220",
                "00609deb\tpush\teax",
                "00609dec\tmov\tecx, esi",
                "00609dee\tcall\t0x487ba0",
            ]
            (disassembly_dir / "00609dc0.asm.tsv").write_text(
                f"# sha256={EXPECTED_SHA256}\tcharacter=Suika\naddress\tmnemonic\toperands\n"
                + "\n".join(instructions) + "\n", encoding="utf-8")
            rows = summarize(handler_map, disassembly_dir)
            self.assertEqual(len(rows), 20)
            self.assertEqual(rows[0]["selected_actions_calls"], "531:1")
            self.assertEqual(rows[0]["useSkill_action_sites"], "1")
            self.assertEqual(rows[0]["command_bit_tests"], "0x400")


if __name__ == "__main__":
    unittest.main()
