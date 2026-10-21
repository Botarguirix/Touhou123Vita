import csv
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
EXPORT = ROOT / "artifacts/kernel" / PE_SHA256 / "stage-layout"


class Bg35PeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exe = ROOT / "original/th123.exe"
        if not exe.exists() or hashlib.sha256(exe.read_bytes()).hexdigest() != PE_SHA256:
            raise unittest.SkipTest("hash-pinned TH123 PE is unavailable")
        manifest = EXPORT / "manifest.tsv"
        if not manifest.exists() or f"sha256\t{PE_SHA256}" not in manifest.read_text(encoding="utf-8"):
            raise unittest.SkipTest("matching Ghidra stage export is unavailable")

    def test_bg35_dispatches_to_common_grid_constructor(self):
        dispatcher = (EXPORT / "00470e40.c").read_text(encoding="utf-8")
        common_ctor = (EXPORT / "00477550.c").read_text(encoding="utf-8")
        grid_loader = (EXPORT / "0046fe40.c").read_text(encoding="utf-8")
        self.assertIn("case 0x23:", dispatcher)
        self.assertIn("FUN_00477550(0x23,0x56,1)", dispatcher)
        self.assertIn("FUN_0046fe40(param_2,param_3,param_4)", common_ctor)
        self.assertIn('"data/background/BG%02d/0000[%02d][%02d].bmp"', grid_loader)
        self.assertIn("while ((int)uVar5 < 0x1e)", grid_loader)
        self.assertIn("if (*(int *)(iVar1 + uVar5 * 4) != 0)", grid_loader)

    def test_failed_resource_lookup_leaves_the_tile_null_and_skips_draw(self):
        loader = (ROOT / "artifacts/kernel" / PE_SHA256 /
                  "resource-loader/00405030.c").read_text(encoding="utf-8")
        grid_loader = (EXPORT / "0046fe40.c").read_text(encoding="utf-8")
        self.assertIn("if (iVar2 < 0)", loader)
        self.assertIn("*param_1 = 0;", loader)
        self.assertIn("if (*(int *)(iVar1 + uVar5 * 4) != 0)", grid_loader)

    def test_missing_bg35_tiles_are_not_in_local_reference_indexes(self):
        manifests = (
            ROOT / "artifacts/th123-resource-manifest.tsv",
            ROOT / "artifacts/th105-resource-manifest.tsv",
            ROOT / "artifacts/resource-manifest.tsv",
        )
        for manifest in manifests:
            with self.subTest(manifest=manifest.name):
                with manifest.open(encoding="utf-8-sig", errors="replace", newline="") as stream:
                    rows = list(csv.DictReader(stream, delimiter="\t"))
                archives = {row["archive"].lower() for row in rows}
                if manifest.name == "th123-resource-manifest.tsv":
                    self.assertEqual(archives, {"th123a.dat", "th123b.dat", "th123c.dat"})
                elif manifest.name == "th105-resource-manifest.tsv":
                    self.assertEqual(archives, {"th105a.dat", "th105b.dat", "th105c.dat"})
                paths = [row["path"].replace("\\", "/").lower() for row in rows]
                self.assertFalse(any(path.startswith("data/background/bg35/") for path in paths))


if __name__ == "__main__":
    unittest.main()
