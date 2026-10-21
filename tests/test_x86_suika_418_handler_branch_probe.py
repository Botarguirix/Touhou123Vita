import unittest
from pathlib import Path

from tools.x86_suika_418_handler_branch_probe import cases


class Suika418HandlerBranchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path("original/th123.exe").is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")

    def test_original_suika_handler_418_branch_and_guards(self):
        rows = cases()
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["passed"] for row in rows))
        success = next(row for row in rows if row["case"] == "forward_from_dash_200")
        self.assertEqual(success["setter_actions"], [418])
        self.assertTrue(success["cleanup_reached"])
        self.assertEqual(success["buffered_after"], [0] * 8)


if __name__ == "__main__":
    unittest.main()
