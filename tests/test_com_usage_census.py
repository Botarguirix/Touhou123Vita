from pathlib import Path
import tempfile
import unittest
from tools.com_usage_census import (ROOT, SHA256, VTABLES, census,
                                    census_instructions, join_state, method_name)


class ResolverTests(unittest.TestCase):
    def test_sdk_offsets_are_interface_specific(self):
        self.assertEqual(method_name("IDirect3D9", 0x40), "CreateDevice")
        self.assertEqual(method_name("IDirect3DDevice9", 0x38), "GetSwapChain")
        self.assertEqual(method_name("IDirect3DSwapChain9", 0xC), "Present")
        self.assertEqual(method_name("IDirect3DDevice9", 0xE4), "SetRenderState")
        self.assertEqual(method_name("IDirect3DDevice9", 0x10C), "SetTextureStageState")
        self.assertEqual(method_name("IDirect3DDevice9", 0x114), "SetSamplerState")
        self.assertEqual(method_name("IDirectSoundBuffer8", 0x2C), "Lock")
        self.assertEqual(len(VTABLES["ID3DXEffect"]), 79)
        self.assertIsNone(method_name("IDirect3D9", 3))

    def fixture(self):
        return [(1, 5, "mov", "eax, dword ptr [0x8a0e30]"),
                (6, 2, "mov", "ecx, dword ptr [eax]"),
                (8, 6, "mov", "edx, dword ptr [ecx + 0xe4]"),
                (14, 2, "push", "1"), (16, 2, "push", "0x16"),
                (18, 1, "push", "eax"), (19, 2, "call", "edx")]

    def test_register_indirect_call_and_constant_arguments(self):
        result = census_instructions(self.fixture())
        self.assertEqual(len(result["calls"]), 1)
        call = result["calls"][0]
        self.assertEqual(call["method"], "SetRenderState")
        self.assertEqual(call["confidence"], "high")
        self.assertEqual(call["constant_arguments"], [22, 1])

    def test_cpp_vtable_with_same_offset_is_not_assumed_com(self):
        rows = self.fixture()
        rows[0] = (1, 2, "mov", "eax, dword ptr [esi]")
        result = census_instructions(rows)
        self.assertFalse(result["calls"])
        self.assertEqual(len(result["unresolved_indirect_calls"]), 1)

    def test_crossing_branch_downgrades_confidence(self):
        rows = self.fixture()
        rows.insert(3, (13, 2, "jne", "0x100"))
        result = census_instructions(rows)
        self.assertEqual(result["calls"][0]["confidence"], "medium")

    def test_partial_register_write_invalidates_pointer(self):
        rows = self.fixture()
        rows.insert(3, (13, 2, "mov", "dl, 1"))
        self.assertFalse(census_instructions(rows)["calls"])

    def wrapper_fixture(self):
        return [(0x1000, 5, "mov", "ecx, 0x896b4c"),
                (0x1005, 5, "call", "0x2000"), (0x100A, 1, "ret", ""),
                (0x2000, 2, "mov", "esi, ecx"),
                (0x2002, 2, "test", "eax, eax"),
                (0x2004, 2, "jne", "0x2008"),
                (0x2006, 2, "mov", "ebx, esi"),
                (0x2008, 2, "mov", "eax, dword ptr [esi + 4]"),
                (0x200A, 2, "mov", "edx, dword ptr [eax]"),
                (0x200C, 3, "mov", "ecx, dword ptr [edx + 0xe4]"),
                (0x200F, 2, "push", "1"),
                (0x2011, 2, "push", "0x1b"),
                (0x2013, 1, "push", "eax"),
                (0x2014, 2, "call", "ecx"), (0x2016, 1, "ret", "")]

    def test_cfg_preserves_known_receiver_on_both_paths(self):
        result = census_instructions(self.wrapper_fixture(), follow_wrappers=True)
        call = next(c for c in result["calls"] if c["va"] == 0x2014)
        self.assertEqual(call["method"], "SetRenderState")
        self.assertEqual(call["constant_arguments"], [27, 1])
        self.assertEqual(call["confidence"], "medium")
        self.assertTrue(call["this_argument_matches"])

    def test_cfg_drops_receiver_when_one_path_clobbers_it(self):
        rows = self.wrapper_fixture()
        rows[6] = (0x2006, 2, "mov", "esi, 0")
        result = census_instructions(rows, follow_wrappers=True)
        self.assertFalse(any(c["va"] == 0x2014 for c in result["calls"]))

    def test_stack_merge_aligns_arguments_from_top(self):
        top = (("constant", 5), ("constant", 19), ("interface", "IDirect3DDevice9", 123))
        _, stack = join_state(({}, top), ({}, (("constant", 999),) + top))
        self.assertEqual(stack, top)

    def test_constant_merge_keeps_alternative_values(self):
        registers, _ = join_state(({"eax": ("constant", 5)}, ()),
                                  ({"eax": ("constant", 6)}, ()))
        self.assertEqual(registers["eax"], ("constant_set", (5, 6)))

    def test_wrong_hash_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong.exe"
            path.write_bytes(b"wrong")
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                census(path)


@unittest.skipUnless((ROOT / "original/th123.exe").is_file(), "falta el PE local")
class ReferenceTests(unittest.TestCase):
    def test_proven_device_input_audio_and_effect_calls(self):
        result = census()
        self.assertEqual(result["sha256"], SHA256)
        by_va = {r["va"]: r for r in result["calls"]}
        for va in (0x415028, 0x415049, 0x41506B):
            self.assertEqual(by_va[va]["method"], "CreateDevice")
            self.assertEqual(by_va[va]["interface"], "IDirect3D9")
        self.assertEqual(by_va[0x4150C7]["method"], "GetSwapChain")
        self.assertEqual(by_va[0x414F27]["method"], "GetAdapterDisplayMode")
        self.assertEqual(by_va[0x40D854]["method"], "CreateDevice")
        self.assertEqual(by_va[0x418AE1]["method"], "CreateSoundBuffer")
        self.assertEqual(by_va[0x418222]["method"], "OnLostDevice")
        self.assertEqual(by_va[0x418222]["confidence"], "medium")
        self.assertEqual(by_va[0x4185BC]["method"], "Lock")
        self.assertEqual(by_va[0x4185BC]["interface"], "IDirectSoundBuffer")
        self.assertEqual(by_va[0x405250]["method"], "GetSurfaceLevel")
        self.assertEqual(by_va[0x405261]["method"], "GetDesc")
        self.assertEqual(by_va[0x404B1B]["method"], "SetSamplerState")
        self.assertEqual(by_va[0x404D48]["method"], "SetTextureStageState")
        self.assertEqual(by_va[0x404D48]["constant_arguments"], [0, 4, 4])
        self.assertEqual(by_va[0x404BD3]["constant_arguments"], [19, 5])
        self.assertFalse(result["incomplete_wrapper_cfg"])
        derived = {row["global_va"]: row["interface"] for row in result["derived_output_globals"]}
        self.assertEqual(derived[0x8A01A4], "IDirectInputDevice8A")
        self.assertEqual(derived[0x8A0FC8], "IDirectSoundBuffer")
        self.assertTrue(result["unresolved_indirect_calls"])
        for row in result["constant_states"]:
            self.assertEqual(row["interface"], "IDirect3DDevice9")


if __name__ == "__main__":
    unittest.main()
