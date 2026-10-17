import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARIZER = ROOT / "tools" / "summarize_pat_image_decode.py"
HEADER = "character\tpat\timage_index\timage_name\tpose_refs\tdamaging_pose_refs\tbpp\twidth\theight\tstatus\n"


class PatImageDecodeSummary(unittest.TestCase):
    def test_summary_counts_referenced_and_unused_images(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "audit.tsv"
            target = Path(directory) / "audit.md"
            source.write_text(
                HEADER
                + "reimu\tdata/character/reimu/reimu.pat\t0\tstand000.bmp\t2\t1\t8\t64\t128\tdecoded\n"
                + "reimu\tdata/character/reimu/reimu.pat\t1\tpalette000.bmp\t0\t0\t0\t0\t0\tunreferenced\n"
                + "# summary pats=1 images=2 decoded=1 unreferenced=1 missing_resource=0 missing_palette=0 unsupported_or_invalid=0\n",
                encoding="ascii",
            )
            result = subprocess.run(
                [sys.executable, str(SUMMARIZER), str(source), str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = target.read_text(encoding="utf-8")
            self.assertIn("**1** (20 candidatos jugables", report)
            self.assertIn("| reimu | 1 | 1 | 0 | 1 | 0 |", report)
            self.assertIn("No hay referencias usadas con fallo.", report)

    def test_rejects_incomplete_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "audit.tsv"
            source.write_text(HEADER, encoding="ascii")
            result = subprocess.run(
                [sys.executable, str(SUMMARIZER), str(source)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("no terminal summary row", result.stderr)


if __name__ == "__main__":
    unittest.main()
