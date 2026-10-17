import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "extract_character_handlers.py"
SPEC = importlib.util.spec_from_file_location("extract_character_handlers", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fake_pe(base: int, tables: dict[int, list[int]]) -> bytes:
    """Build a minimal PE32 image with vtables at specified VAs."""
    image = bytearray(0x3000)
    image[0:2] = b"MZ"
    struct.pack_into("<I", image, 0x3C, 0x80)
    image[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", image, 0x84, 0x14C, 1, 0, 0, 0, 0xE0, 0)
    opt = 0x98
    struct.pack_into("<H", image, opt, 0x10B)
    struct.pack_into("<I", image, opt + 28, base)
    section = opt + 0xE0
    image[section : section + 8] = b".all\0\0\0\0"
    struct.pack_into("<IIII", image, section + 8, 0x2000, 0x1000, 0x2000, 0x1000)
    for table, targets in tables.items():
        offset = 0x1000 + table - base - 0x1000
        struct.pack_into(f"<{len(targets)}I", image, offset, *targets)
    return bytes(image)


class CharacterHandlerTests(unittest.TestCase):
    def test_extracts_twenty_unique_handlers_from_vtables(self):
        base = 0x400000
        names = MODULE.PLAYABLE
        table_addresses = {name: 0x401100 + i * 0x80 for i, name in enumerate(names)}
        targets = {name: 0x402000 + i * 0x20 for i, name in enumerate(names)}
        targets.update(MODULE.KNOWN_HANDLERS)
        image_tables = {
            table_addresses[name]: [0x402000] * 20 + [targets[name], 0x403000]
            for name in names
        }
        source = "\n".join(
            f"const int _vtable_info<v2::Player{name}>::baseAddr = 0x{table_addresses[name]:08x};"
            for name in names
        )
        with tempfile.TemporaryDirectory() as temporary:
            exe = Path(temporary) / "th123.exe"
            cpp = Path(temporary) / "Player.cpp"
            exe.write_bytes(fake_pe(base, image_tables))
            cpp.write_text(source, encoding="utf-8")
            digest = MODULE.hashlib.sha256(exe.read_bytes()).hexdigest()
            MODULE.EXPECTED_SHA256 = digest
            got_digest, rows = MODULE.extract(exe, cpp)
        self.assertEqual(got_digest, digest)
        self.assertEqual(len(rows), 20)
        self.assertEqual(len({row["handleInputs_va"] for row in rows}), 20)
        self.assertTrue(all(row["checkAllMotionInputs_va"] == "00403000" for row in rows))

    def test_rejects_unpinned_executable(self):
        with tempfile.TemporaryDirectory() as temporary:
            exe = Path(temporary) / "th123.exe"
            cpp = Path(temporary) / "Player.cpp"
            exe.write_bytes(b"wrong image")
            cpp.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unexpected TH123 executable SHA-256"):
                MODULE.extract(exe, cpp)


if __name__ == "__main__":
    unittest.main()
