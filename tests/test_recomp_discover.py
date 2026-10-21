import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recomp.analysis.discover import Discovery  # noqa: E402
from recomp.analysis.image import Image, Section  # noqa: E402

TEXT = 0x401000
RDATA = 0x402000
IAT_EXIT = RDATA
VTABLE = RDATA + 0x10


class Asm:
    """Tiny x86 byte assembler with label fixups for synthetic images."""

    def __init__(self, base):
        self.base, self.buf, self.labels, self.fixups = base, bytearray(), {}, []

    def here(self):
        return self.base + len(self.buf)

    def label(self, name):
        self.labels[name] = self.here()

    def raw(self, data):
        self.buf += bytes(data)

    def rel32(self, opcode, label):
        self.raw(opcode)
        self.fixups.append(("rel32", len(self.buf), label))
        self.raw(b"\0" * 4)

    def rel8(self, opcode, label):
        self.raw(opcode)
        self.fixups.append(("rel8", len(self.buf), label))
        self.raw(b"\0")

    def abs32(self, opcode, label):
        self.raw(opcode)
        self.fixups.append(("abs32", len(self.buf), label))
        self.raw(b"\0" * 4)

    def align(self, n, fill=0xCC):
        while len(self.buf) % n:
            self.raw([fill])

    def build(self):
        for kind, pos, label in self.fixups:
            target = self.labels[label] if isinstance(label, str) else label
            if kind == "rel32":
                struct.pack_into("<i", self.buf, pos, target - (self.base + pos + 4))
            elif kind == "rel8":
                struct.pack_into("<b", self.buf, pos, target - (self.base + pos + 1))
            else:
                struct.pack_into("<I", self.buf, pos, target)
        return bytes(self.buf)


def synthetic_image():
    a = Asm(TEXT)
    a.label("start")
    a.rel32(b"\xe8", "switch1")              # call switch1
    a.rel32(b"\xe8", "switch2")              # call switch2
    a.raw(b"\x6a\x00")                         # push 0
    a.abs32(b"\xff\x15", IAT_EXIT)             # call [ExitProcess]
    a.label("junk")
    a.raw(b"\xff\xff\xff\xff")                 # must stay undecoded after a noreturn call
    a.align(16)

    a.label("switch1")
    a.raw(b"\x8b\x44\x24\x04")                 # mov eax, [esp+4]
    a.raw(b"\x83\xf8\x02")                     # cmp eax, 2
    a.rel8(b"\x77", "default1")                # ja default1
    a.abs32(b"\xff\x24\x85", "table1")         # jmp [eax*4+table1]
    for i in range(3):
        a.label(f"case1_{i}")
        a.raw(bytes([0xB8, 0x0A + i, 0, 0, 0, 0xC3]))
    a.label("default1")
    a.raw(b"\x33\xc0\xc3")                     # xor eax, eax; ret
    a.align(4)
    a.label("table1")
    for i in range(3):
        a.abs32(b"", f"case1_{i}")
    a.align(16)

    a.label("switch2")
    a.raw(b"\x8b\x44\x24\x04")                 # mov eax, [esp+4]
    a.raw(b"\x83\xf8\x04")                     # cmp eax, 4
    a.rel8(b"\x77", "default2")                # ja default2
    a.abs32(b"\x0f\xb6\x80", "index2")         # movzx eax, byte [eax+index2]
    a.abs32(b"\xff\x24\x85", "table2")         # jmp [eax*4+table2]
    a.label("case2_0")
    a.raw(b"\x33\xc0\xc3")
    a.label("case2_1")
    a.raw(b"\xb0\x01\xc3")
    a.label("default2")
    a.raw(b"\x83\xc8\xff\xc3")                 # or eax, -1; ret
    a.align(4)
    a.label("table2")
    for name in ("case2_0", "case2_1", "default2"):
        a.abs32(b"", name)
    a.label("index2")
    a.raw(b"\x00\x01\x01\x00\x02")
    a.align(16)

    a.label("virtual")                         # only reachable through the vtable
    a.raw(b"\xb8\x05\x00\x00\x00\xc3")
    a.align(16)
    text = a.build()

    rdata = bytearray(0x20)
    struct.pack_into("<I", rdata, VTABLE - RDATA, a.labels["virtual"])
    struct.pack_into("<I", rdata, VTABLE - RDATA + 4, a.labels["junk"])
    image = Image(0x400000, TEXT, [Section(".text", TEXT, text, True),
                                   Section(".rdata", RDATA, bytes(rdata), False)],
                  {IAT_EXIT: ("KERNEL32.dll", "ExitProcess")})
    return image, a.labels


class SyntheticDiscoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.labels = synthetic_image()
        cls.d = Discovery(cls.image)
        cls.d.run()
        cls.maps = cls.d.byte_map()[".text"]

    def kind_at(self, label, offset=0):
        return self.maps[self.labels[label] + offset - TEXT]

    def test_functions_are_found_from_calls_and_vtable(self):
        found = set(self.d.functions)
        for name in ("start", "switch1", "switch2", "virtual"):
            self.assertIn(self.labels[name], found, name)
        self.assertEqual(self.d.functions[self.labels["virtual"]].source, "data_ptr")
        self.assertEqual(self.d.rejected.get(self.labels["junk"]), "invalid")

    def test_bounded_jump_table(self):
        fn = self.d.functions[self.labels["switch1"]]
        self.assertEqual(len(fn.switches), 1)
        sw = fn.switches[0]
        self.assertEqual((sw.table, sw.entries, sw.bound), (self.labels["table1"], 3, "cmp"))
        self.assertEqual(sw.targets, [self.labels[f"case1_{i}"] for i in range(3)])
        for i in range(12):
            self.assertEqual(self.kind_at("table1", i), 2)

    def test_two_level_jump_table(self):
        sw = self.d.functions[self.labels["switch2"]].switches[0]
        self.assertEqual(sw.index_table, self.labels["index2"])
        self.assertEqual((sw.index_entries, sw.entries), (5, 3))
        for i in range(5):
            self.assertEqual(self.kind_at("index2", i), 3)
        self.assertIn(self.labels["default2"], self.d.functions[self.labels["switch2"]].insns)

    def test_bytes_after_noreturn_call_stay_unexplained(self):
        self.assertIn(self.labels["start"], self.d.noreturn)
        for i in range(4):
            self.assertEqual(self.kind_at("junk", i), 0)
        summary = self.d.summary()
        self.assertEqual(summary["unexplained_bytes"], 4)
        self.assertEqual(summary["unresolved_indirect_jumps"], 0)


@unittest.skipUnless((ROOT / "original/th123.exe").exists(), "requires the user's th123.exe")
class Th123ImageTest(unittest.TestCase):
    def test_entry_point_decodes(self):
        image = Image.from_pe(ROOT / "original/th123.exe")
        d = Discovery(image)
        fn = d.explore(image.entry, "entry", set())
        self.assertFalse(fn.invalid)
        self.assertGreater(len(fn.insns), 5)


if __name__ == "__main__":
    unittest.main()
