import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "summarize_character_handlers.py"
SPEC = importlib.util.spec_from_file_location("summarize_character_handlers", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CharacterHandlerSummaryTests(unittest.TestCase):
    def test_extracts_virtual_action_and_move_lock_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            map_path = root / "handlers.tsv"
            with map_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["sha256", "character", "handleInputs_va"], delimiter="\t")
                writer.writeheader()
                for index, character in enumerate(("Reimu", *[f"Other{i}" for i in range(19)])):
                    writer.writerow({"sha256": MODULE.HASH, "character": character, "handleInputs_va": f"{0x004AE670 + index * 0x10:08x}"})
            asm = root / "disassembly"
            asm.mkdir()
            (asm / "004ae670.asm.tsv").write_text(
                "# fixture\naddress\tmnemonic\toperands\n"
                "004b0000\tpush\t0x198\n"
                "004b0002\tmov\tecx, esi\n"
                "004b0004\tcall\t0x489610\n"
                "004b0009\tpush\t0x198\n"
                "004b000b\tmov\tecx, esi\n"
                "004b000d\tcall\tedx\n",
                encoding="utf-8",
            )
            rows = MODULE.summarize(map_path, root)
        self.assertEqual(rows[0]["dispatches"], "408:1")
        self.assertEqual(rows[0]["lock_queries"], "408")
        self.assertEqual(rows[0]["instructions"], "6")


if __name__ == "__main__":
    unittest.main()
