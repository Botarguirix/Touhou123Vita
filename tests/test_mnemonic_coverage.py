import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "summarize_mnemonic_coverage.py"
SPEC = importlib.util.spec_from_file_location("summarize_mnemonic_coverage", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class MnemonicCoverageTests(unittest.TestCase):
    def test_summarizes_twenty_handlers_and_aggregates_mnemonics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            handler_map = root / "handlers.tsv"
            disassembly = root / "disassembly"
            disassembly.mkdir()
            fields = ["sha256", "character", "handleInputs_va"]
            with handler_map.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
                writer.writeheader()
                for index in range(20):
                    character = f"Character{index}"
                    address = f"{0x401000 + index * 0x10:08x}"
                    writer.writerow({
                        "sha256": MODULE.EXPECTED_SHA256,
                        "character": character,
                        "handleInputs_va": address,
                    })
                    (disassembly / f"{address}.asm.tsv").write_text(
                        f"# sha256={MODULE.EXPECTED_SHA256}\tcharacter={character}\tentry={address}\n"
                        "address\tmnemonic\toperands\n"
                        f"{address}\tmov\teax, ebx\n"
                        f"{int(address, 16) + 1:08x}\tret\t\n",
                        encoding="utf-8",
                    )

            report = MODULE.summarize(handler_map, disassembly)
        self.assertEqual(report["handler_count"], 20)
        self.assertEqual(report["instruction_count"], 40)
        self.assertEqual(report["aggregate_mnemonic_counts"], {"mov": 20, "ret": 20})
        self.assertIn("not semantic support", report["scope"])

    def test_rejects_disassembly_for_different_handler(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            disassembly = root / "disassembly"
            disassembly.mkdir()
            handler_map = root / "handlers.tsv"
            with handler_map.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=["sha256", "character", "handleInputs_va"], delimiter="\t"
                )
                writer.writeheader()
                writer.writerow({
                    "sha256": MODULE.EXPECTED_SHA256,
                    "character": "Reimu",
                    "handleInputs_va": "00401000",
                })
            (disassembly / "00401000.asm.tsv").write_text(
                f"# sha256={MODULE.EXPECTED_SHA256}\tcharacter=Other\tentry=00401000\n"
                "address\tmnemonic\toperands\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                MODULE.summarize(handler_map, disassembly)


if __name__ == "__main__":
    unittest.main()
