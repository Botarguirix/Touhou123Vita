import csv
import tempfile
import unittest
from pathlib import Path

from tools.audit_stage_resources import audit, write_tsv


class StageResourceAuditTests(unittest.TestCase):
    def test_separates_present_resources_from_viewer_name_conventions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "manifest.tsv"
            rows = [
                {"archive": "th123a.dat", "offset": "0", "size": "1",
                 "path": "data/background/bg10/0000_00.cv2"},
                {"archive": "th123a.dat", "offset": "1", "size": "1",
                 "path": "data/background/bg30/0000[01][01].cv2"},
                {"archive": "th123a.dat", "offset": "2", "size": "1",
                 "path": "data/background/bg34/0001[01][01].cv2"},
                {"archive": "th123a.dat", "offset": "3", "size": "1",
                 "path": "data/background/bg34/0001.cv2"},
                {"archive": "th123a.dat", "offset": "4", "size": "1",
                 "path": "data/background/bg34/object/objectFa000.cv2"},
                {"archive": "th105a.dat", "offset": "5", "size": "1",
                 "path": "data/background/bg02/left/a00.cv2"},
                {"archive": "th105a.dat", "offset": "6", "size": "1",
                 "path": "data/background/bg04/cloud2.cv2"},
                {"archive": "th105a.dat", "offset": "7", "size": "1",
                 "path": "data/background/bg16/0001.cv2"},
            ]
            with manifest.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)

            report = audit(manifest)
            by_name = {stage["stage"]: stage for stage in report["stages"]}
            self.assertEqual(report["stage_count"], 25)
            self.assertIn("bg35", by_name)
            self.assertEqual(by_name["bg35"]["loader_mode"], "grid-5x6")
            self.assertFalse(by_name["bg35"]["folder_present"])
            self.assertEqual(by_name["bg10"]["loader_mode"], "flat-30")
            self.assertEqual(by_name["bg10"]["base_names_present"], 1)
            self.assertEqual(len(by_name["bg10"]["missing_base_names"]), 29)
            self.assertEqual(by_name["bg30"]["loader_mode"], "grid-5x6")
            self.assertEqual(by_name["bg30"]["base_names_present"], 1)
            self.assertEqual(by_name["bg33"]["expected_base_names"], 24)
            self.assertEqual(len(by_name["bg33"]["missing_base_names"]), 24)
            self.assertFalse(any(name.startswith("0000[05]")
                                 for name in by_name["bg33"]["missing_base_names"]))
            self.assertEqual(by_name["bg34"]["aux_names_present"], 3)
            self.assertEqual(by_name["bg34"]["source_archives"], ["th123a.dat"])
            self.assertEqual(by_name["bg34"]["bitmap_names_present"], 1)
            self.assertEqual(by_name["bg34"]["sprite_names_present"], 1)
            self.assertEqual(len(by_name["bg34"]["missing_aux_names"]), 61)
            self.assertEqual(by_name["bg34"]["unconnected_cv2"], [])
            self.assertEqual(by_name["bg02"]["expected_aux_names"], 48)
            self.assertEqual(by_name["bg02"]["aux_names_present"], 1)
            self.assertEqual(by_name["bg02"]["source_archives"], ["th105a.dat"])
            self.assertEqual(by_name["bg04"]["aux_names_present"], 1)
            self.assertEqual(by_name["bg16"]["bitmap_names_present"], 1)

            tsv = root / "out.tsv"
            write_tsv(report, tsv)
            self.assertIn("bg30\tgrid-5x6", tsv.read_text(encoding="utf-8"))
            self.assertIn("base_names_present", tsv.read_text(encoding="utf-8"))
            self.assertIn("source_archives", tsv.read_text(encoding="utf-8"))

    def test_merges_inherited_and_current_dat_coverage_with_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifests = []
            for archive, paths in (
                ("th105a.dat", ["data/background/bg00/0000_00.cv2",
                                "data/background/bg10/0000_00.cv2"]),
                ("th123a.dat", ["data/background/bg10/0000_01.cv2",
                                "data/background/bg34/0000[01][01].cv2"]),
            ):
                manifest = root / f"{archive}.tsv"
                with manifest.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=("archive", "offset", "size", "path"), delimiter="\t")
                    writer.writeheader()
                    for index, path in enumerate(paths):
                        writer.writerow({"archive": archive, "offset": index, "size": 1, "path": path})
                manifests.append(manifest)

            by_name = {row["stage"]: row for row in audit(manifests)["stages"]}
            self.assertEqual(by_name["bg00"]["source_archives"], ["th105a.dat"])
            self.assertEqual(by_name["bg10"]["source_archives"], ["th105a.dat", "th123a.dat"])
            self.assertEqual(by_name["bg34"]["source_archives"], ["th123a.dat"])
            self.assertFalse(by_name["bg35"]["folder_present"])

    def test_lists_constructor_candidate_auxiliaries_separately(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "manifest.tsv"
            rows = [
                {"archive": "th123a.dat", "offset": "0", "size": "1",
                 "path": "data/background/bg36/clowd_l.cv2"},
                {"archive": "th123a.dat", "offset": "1", "size": "1",
                 "path": "data/background/bg36/mystery.cv2"},
            ]
            with manifest.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)
            by_name = {row["stage"]: row for row in audit(manifest)["stages"]}
            bg36 = by_name["bg36"]
            self.assertNotIn("clowd_l.cv2", bg36["missing_aux_names"])
            self.assertIn("clowd_s.cv2", bg36["missing_aux_names"])
            self.assertIn("mystery.cv2", bg36["unconnected_cv2"])

    def test_uses_exact_bg37_and_bg38_constructor_auxiliary_sets(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "manifest.tsv"
            paths = {
                "bg37": ("tori1.cv2", "clowd_l.cv2", "clowd_s.cv2"),
                "bg38": ("clowd_l.cv2", "clowd_s.cv2"),
            }
            rows = []
            for stage, names in paths.items():
                for name in names:
                    rows.append({"archive": "th123a.dat", "offset": "0", "size": "1",
                                 "path": f"data/background/{stage}/{name}"})
            with manifest.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)
            by_name = {row["stage"]: row for row in audit(manifest)["stages"]}
            self.assertEqual(by_name["bg37"]["expected_aux_names"], 3)
            self.assertEqual(by_name["bg37"]["aux_names_present"], 3)
            self.assertEqual(by_name["bg37"]["missing_aux_names"], [])
            self.assertEqual(by_name["bg38"]["expected_aux_names"], 2)
            self.assertEqual(by_name["bg38"]["aux_names_present"], 2)
            self.assertEqual(by_name["bg38"]["missing_aux_names"], [])


if __name__ == "__main__":
    unittest.main()
