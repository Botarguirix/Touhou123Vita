import struct
import tempfile
import unittest
from pathlib import Path

from tools.make_livearea_assets import generate


class LiveAreaAssetTests(unittest.TestCase):
    def test_generates_indexed_pngs_and_matching_template(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generate(root)
            expected = {
                "icon0.png": (128, 128),
                "livearea/contents/bg.png": (840, 500),
                "livearea/contents/startup.png": (280, 158),
            }
            for relative, dimensions in expected.items():
                png = (root / relative).read_bytes()
                self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">IIBBBBB", png[16:29]),
                                 (*dimensions, 8, 3, 0, 0, 0))
            template = (root / "livearea/contents/template.xml").read_text(
                encoding="utf-8")
            self.assertIn("<image>bg.png</image>", template)
            self.assertIn("<startup-image>startup.png</startup-image>", template)


if __name__ == "__main__":
    unittest.main()
