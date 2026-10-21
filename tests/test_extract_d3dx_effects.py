from pathlib import Path
import struct
import tempfile
import unittest

from tools.extract_d3dx_effects import (ROOT, SHA256, SITES, Reader,
                                       disassemble_shader, extract, parse_effect)


def words(*values):
    return struct.pack("<" + "I" * len(values), *values)


class BinarySafetyTests(unittest.TestCase):
    def test_reader_rejects_overflow_and_unterminated_name(self):
        with self.assertRaises(ValueError):
            Reader(b"abc").u32()
        with self.assertRaises(ValueError):
            Reader(words(2) + b"ab").name(0)

    def test_rejects_non_fx_and_truncated_metadata(self):
        with self.assertRaises(ValueError):
            parse_effect(words(0, 0))
        with self.assertRaises(ValueError):
            parse_effect(words(0xFEFF0901, 100))

    def test_shader_comment_and_exact_end(self):
        shader = words(0xFFFE0101, 0x0001FFFE, 0x12345678,
                       1, 0xC00F0000, 0x90E40000, 0xFFFF)
        result = disassemble_shader(shader)
        self.assertEqual(result["profile"], "vs_1_1")
        self.assertEqual(result["instructions"], 1)
        self.assertIn("mov oPos, v0", result["asm"])
        with self.assertRaises(ValueError):
            disassemble_shader(shader[:-4])
        with self.assertRaises(ValueError):
            disassemble_shader(shader + words(0))

    def test_saturate_is_an_instruction_modifier(self):
        result = disassemble_shader(words(0xFFFF0101, 2, 0x801F0000,
                                          0x80E40000, 0xA0E40000, 0xFFFF))
        self.assertIn("add_sat r0, r0, c0", result["asm"])

    def test_unknown_opcodes_fail_visibly(self):
        with self.assertRaisesRegex(ValueError, "unsupported shader opcode"):
            disassemble_shader(words(0xFFFF0101, 0x1234, 0xFFFF))

    def test_hash_checked_before_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wrong = root / "wrong.exe"
            wrong.write_bytes(b"wrong")
            out = root / "output"
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                extract(wrong, out)
            self.assertFalse(out.exists())


@unittest.skipUnless((ROOT / "original/th123.exe").is_file(), "falta el PE local")
class ReferenceTests(unittest.TestCase):
    def test_all_effects_parse_to_exact_callsite_length(self):
        with tempfile.TemporaryDirectory() as directory:
            result = extract(ROOT / "original/th123.exe", directory)
            self.assertEqual(result["sha256"], SHA256)
            effects = result["effects"]
            self.assertEqual([(e["va"], e["size"], e["caller"]) for e in effects], list(SITES))
            self.assertEqual([len(e["parameters"]) for e in effects], [5, 13, 4])
            self.assertEqual([len(e["techniques"][0]["passes"]) for e in effects], [1, 7, 3])
            self.assertEqual([len(e["shaders"]) for e in effects], [1, 10, 3])
            shaders = [s for e in effects for s in e["shaders"]]
            self.assertEqual(sum(s["profile"] == "ps_1_1" for s in shaders), 11)
            self.assertEqual(sum(s["profile"] == "vs_1_1" for s in shaders), 3)
            self.assertEqual([s["instructions"] for s in effects[1]["shaders"]],
                             [9, 8, 6, 5, 4, 4, 3, 13, 13, 13])
            self.assertEqual(effects[0]["parameters"][0]["name"], "Tex0")
            self.assertEqual(effects[1]["shaders"][0]["parameter_names"], ["pshaderEx0DP"])
            self.assertEqual(len(list(Path(directory).glob("*.asm"))), 14)
            self.assertIn("add_d2 r0.xyz", (Path(directory) / "effect-0085a608-shader-0.asm").read_text())
            before = (Path(directory) / "effects.json").read_bytes()
            extract(ROOT / "original/th123.exe", directory)
            self.assertEqual(before, (Path(directory) / "effects.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
