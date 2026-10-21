import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StageCatalogTests(unittest.TestCase):
    def test_catalog_covers_every_stage_id_dispatched_by_the_pe(self):
        source = (ROOT / "src/vita_main.c").read_text(encoding="utf-8")
        match = re.search(r"static const char \*stage_names\[\]=\{([^}]+)\};", source)
        self.assertIsNotNone(match)
        names = re.findall(r'"(bg[0-9]{2})"', match.group(1))
        ids = [int(name[2:]) for name in names]
        expected = [*range(0, 7), *range(10, 19), *range(30, 39)]
        self.assertEqual(ids, expected)
        self.assertEqual(len(names), 25)
        self.assertEqual(names[names.index("bg34") + 1], "bg35")

    def test_blank_stage_viewer_reports_missing_decoded_tiles(self):
        source = (ROOT / "src/vita_main.c").read_text(encoding="utf-8")
        self.assertIn("No base tiles decoded from the local DATs", source)


if __name__ == "__main__":
    unittest.main()
