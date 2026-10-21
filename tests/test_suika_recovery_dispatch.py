import struct
import unittest
from pathlib import Path

from tools.scan_pe_vtable_callgraph_field import EXPECTED_SHA256
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile
from tools.x86_suwako_808_factory_probe import Suwako808FactoryProbe


class SuikaRecoveryDispatchTests(unittest.TestCase):
    def test_actions_96_and_97_share_the_original_down_handler(self):
        exe = Path("original/th123.exe")
        if not exe.is_file():
            self.skipTest("local reference original/th123.exe is unavailable")
        import hashlib
        import pefile

        self.assertEqual(hashlib.sha256(exe.read_bytes()).hexdigest(), EXPECTED_SHA256)
        pe = pefile.PE(str(exe), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase

        def dword(va):
            return struct.unpack("<I", pe.get_data(va - base, 4))[0]

        def byte(va):
            return pe.get_data(va - base, 1)[0]

        # Player::update -> 0x483f40 indexes by (action - 0x32), then
        # dispatches through byte map 0x486e3c and dword table 0x486d80.
        def update_handler(action):
            index = byte(0x486E3C + action - 0x32)
            return dword(0x486D80 + index * 4)

        # Player action-change callback -> 0x48b210 has a separate map/table.
        def action_callback(action):
            index = byte(0x48C47C + action)
            return dword(0x48C3B8 + index * 4)

        self.assertEqual(update_handler(96), 0x485115)
        self.assertEqual(update_handler(97), 0x485115)
        self.assertEqual(update_handler(98), 0x4852A0)
        self.assertEqual(action_callback(96), 0x48BE20)
        self.assertEqual(action_callback(97), 0x48B85F)
        self.assertEqual(action_callback(98), 0x48B8F6)

    def test_single_sequence_action96_fixture_self_links_missing_sequences(self):
        exe = Path("original/th123.exe")
        dat = Path("original/th123c.dat")
        if not exe.is_file() or not dat.is_file():
            self.skipTest("local reference PE/DAT files are unavailable")
        probe = Suwako808FactoryProbe(exe, character="suika", action_id=96,
                                      intercept_box_transforms=True)
        probe._prepare_pat_actions((96,))
        node = probe._sequence_node_by_action[96][0]
        previous = struct.unpack("<I", probe.uc.mem_read(node + 0x1C, 4))[0]
        following = struct.unpack("<I", probe.uc.mem_read(node + 0x18, 4))[0]
        frame_start, frame_end = struct.unpack("<II", probe.uc.mem_read(node + 4, 8))
        self.assertEqual(previous, node)
        self.assertEqual(following, node)
        self.assertEqual((frame_end - frame_start) // 0xA8, 10)

    def test_original_pat_loader_builds_singleton_previous_self_link(self):
        exe = Path("original/th123.exe")
        if not exe.is_file():
            self.skipTest("local reference original/th123.exe is unavailable")
        pe = pefile.PE(str(exe), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        loader_block = 0x467DF2
        decoder = Cs(CS_ARCH_X86, CS_MODE_32)
        instructions = list(decoder.disasm(pe.get_data(loader_block - base, 14), loader_block))
        self.assertEqual([(ins.address, ins.mnemonic, ins.op_str) for ins in instructions[:2]], [
            (0x467DF2, "mov", "dword ptr [esi + 0x18], 0"),
            (0x467DF9, "mov", "dword ptr [esi + 0x1c], esi"),
        ])


if __name__ == "__main__":
    unittest.main()
