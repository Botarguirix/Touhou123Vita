import csv
import io
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))

from tools.extract_pat_pose_metadata import entries_from_dat
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32


class StoryNamazuSourceTests(unittest.TestCase):
    def test_meirin_story_stage_four_uses_namazu(self):
        archive = ROOT / "original" / "th123a.dat"
        entry_name = "data/csv/meirin/story.cv1"
        self.assertIn(entry_name, entries_from_dat(archive))

        manifest = (ROOT / "artifacts" / "th123-resource-manifest.tsv").read_text(
            encoding="utf-8")
        self.assertIn(f'"{entry_name}"', manifest)

        story_csv = ROOT / "artifacts" / "extracted" / "data" / "csv" / "meirin" / "story.csv"
        rows = list(csv.reader(io.StringIO(story_csv.read_bytes().decode("cp932"))))
        boss_rows = [row for row in rows if len(row) >= 4 and row[:2] == ["4", "Namazu"]]
        self.assertEqual(len(boss_rows), 1)
        self.assertEqual(boss_rows[0][2:4], ["5", "3"])

        expected_campaigns = {
            "chirno": ["Sanae", "Meirin", "Marisa", "Utsuho", "Alice"],
            "meirin": ["Patchouli", "Alice", "Marisa", "Reimu", "Namazu"],
            "sanae": ["Chirno", "Meirin", "Reimu", "Utsuho", "Suwako"],
        }
        observed = {}
        for protagonist, expected_rivals in expected_campaigns.items():
            path = ROOT / "artifacts" / "extracted" / "data" / "csv" / protagonist / "story.csv"
            self.assertIn(f'"data/csv/{protagonist}/story.cv1"', manifest)
            campaign_rows = list(csv.reader(io.StringIO(path.read_bytes().decode("cp932"))))
            observed[protagonist] = [row[1] for row in campaign_rows
                                     if len(row) >= 4 and row[0].isdigit()
                                     and row[1] and not row[1].isdigit()]
            self.assertEqual(observed[protagonist], expected_rivals)
        self.assertEqual(sum(len(rivals) for rivals in observed.values()), 15)
        self.assertEqual([(hero, stage, rival)
                          for hero, rivals in observed.items()
                          for stage, rival in enumerate(rivals) if rival == "Namazu"],
                         [("meirin", 4, "Namazu")])

        character_header = (ROOT / "local" / "SokuLib" / "src" / "Character.hpp").read_text(
            encoding="utf-8")
        self.assertRegex(character_header, r"/\*\s*21\s*\*/\s*CHARACTER_NAMAZU")

        pe = pefile.PE(str(ROOT / "original" / "th123.exe"), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        instructions = list(md.disasm(pe.get_data(0x45EF50 - base, 0x2B0), 0x45EF50))
        rendered = [(ins.address, ins.mnemonic, ins.op_str) for ins in instructions]
        lookup = next(i for i, row in enumerate(rendered)
                      if row[1:] == ("call", "0x43f440"))
        store = next(i for i, row in enumerate(rendered)
                     if row[1:] == ("mov", "dword ptr [ecx], eax"))
        create_slot = next(i for i, row in enumerate(rendered)
                           if row[1:] == ("call", "0x46ead0"))
        self.assertLess(lookup, store)
        self.assertLess(store, create_slot)
        self.assertIn((0x45F174, "push", "3"), rendered)
        self.assertIn((0x45F115, "cmp", "ebx, 3"), rendered)

        image = pe.get_memory_mapped_image()
        self.assertIn(b"data/csv/\0", image[0x858718 - base:0x858718 - base + 16])
        self.assertIn(b"/story.csv\0", image[0x85870C - base:0x85870C - base + 16])
        text = next(section.get_data() for section in pe.sections
                    if section.Name.rstrip(b"\0") == b".text")
        self.assertIn((0x858718).to_bytes(4, "little"), text)
        self.assertIn((0x85870C).to_bytes(4, "little"), text)

        callers = []
        for section in pe.sections:
            data = section.get_data()
            start = base + section.VirtualAddress
            for offset in range(len(data) - 5):
                if data[offset] == 0xE8:
                    target = start + offset + 5 + int.from_bytes(
                        data[offset + 1:offset + 5], "little", signed=True)
                    if target == 0x45EF50:
                        callers.append(start + offset)
        self.assertEqual(set(callers), {0x46152A, 0x481C3D, 0x481CDC})
        self.assertIn((0x85B734).to_bytes(4, "little"),
                      pe.get_data(0x481C0F - base, 0x2F))
        self.assertIn((0x85B72C).to_bytes(4, "little"),
                      pe.get_data(0x481CAB - base, 0x31))
        self.assertIn(b"win\0", image[0x85B734 - base:0x85B734 - base + 8])
        self.assertIn(b"lose\0", image[0x85B72C - base:0x85B72C - base + 8])

        loader = list(md.disasm(pe.get_data(0x432F8B - base, 0x3A5), 0x432F8B))
        loader_ops = [(ins.address, ins.mnemonic, ins.op_str) for ins in loader]
        self.assertIn((0x432F8D, "push", "0x858718"), loader_ops)
        self.assertIn((0x432FFB, "push", "0x85870c"), loader_ops)
        self.assertIn((0x433029, "call", "0x40f370"), loader_ops)
        self.assertIn((0x4330B6, "call", "0x43f440"), loader_ops)
        self.assertIn((0x43328D, "cmp", "eax, 0x14"), loader_ops)
        self.assertIn((0x433294, "jl", "0x432bb0"), loader_ops)

        # The Story progress records are 0x18-byte rows in vectors rooted at
        # manager+0x1a4. The parser inserts rows through 0x430e20, while the
        # stage-state updater matches two keys and increments field +0x0c.
        parser = list(md.disasm(pe.get_data(0x4330B6 - base, 0x11C), 0x4330B6))
        parser_ops = [(ins.address, ins.mnemonic, ins.op_str) for ins in parser]
        self.assertIn((0x4330B6, "call", "0x43f440"), parser_ops)
        self.assertIn((0x4331C2, "call", "0x430e20"), parser_ops)
        self.assertIn((0x4331A7, "cmp", "eax, dword ptr [edx + ebx + 8]"), parser_ops)

        updater = list(md.disasm(pe.get_data(0x42F5E0 - base, 0xA0), 0x42F5E0))
        updater_ops = [(ins.address, ins.mnemonic, ins.op_str) for ins in updater]
        self.assertIn((0x42F602, "shl", "eax, 4"), updater_ops)
        self.assertIn((0x42F648, "cmp", "dword ptr [esi], ecx"), updater_ops)
        self.assertIn((0x42F656, "cmp", "dword ptr [esi + 8], ebp"), updater_ops)
        self.assertIn((0x42F674, "add", "dword ptr [esi + 0xc], 1"), updater_ops)
        story_manager = list(md.disasm(pe.get_data(0x468DE0 - base, 0xA0), 0x468DE0))
        story_ops = [(ins.address, ins.mnemonic, ins.op_str) for ins in story_manager]
        self.assertIn((0x468E2E, "call", "0x43df50"), story_ops)
        self.assertIn((0x468E35, "call", "0x42f5e0"), story_ops)
        singleton = list(md.disasm(pe.get_data(0x43DF50 - base, 6), 0x43DF50))
        self.assertEqual([(ins.mnemonic, ins.op_str) for ins in singleton],
                         [("mov", "eax, 0x899f60"), ("ret", "")])

        callers_42f5e0 = []
        callers_42f680 = []
        text = next(section for section in pe.sections
                    if section.Name.rstrip(b"\0") == b".text")
        text_bytes = text.get_data()
        text_start = base + text.VirtualAddress
        for offset in range(len(text_bytes) - 5):
            if text_bytes[offset] != 0xE8:
                continue
            target = text_start + offset + 5 + int.from_bytes(
                text_bytes[offset + 1:offset + 5], "little", signed=True)
            if target == 0x42F5E0:
                callers_42f5e0.append(text_start + offset)
            elif target == 0x42F680:
                callers_42f680.append(text_start + offset)
        self.assertEqual(callers_42f5e0, [0x468E35])
        self.assertEqual(callers_42f680, [0x468FA6, 0x51DD45])


if __name__ == "__main__":
    unittest.main()


