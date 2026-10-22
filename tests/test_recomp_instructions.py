"""Instruction-level equivalence for the lifter: hand-assembled x86 snippets run in
Unicorn and as lifted C (recomp/tests/diff_runner.c) from the same random states.

Covers the instructions added for whole-program coverage (F1.3): xadd, imul r/m8,
rcl/rcr, rol/ror of 8/16 bits, shld/shrd, bt/bts/btr/btc, xlatb, scas/cmps with
repe/repne, pushfd/popfd and fnsave/frstor. cpuid and segment-register reads
are excluded on purpose: the runtime reports fixed values (docs/F1_COVERAGE.md).
No game code is involved, so the test does not need th123.exe.
"""
import random
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from recomp.analysis.discover import Discovery  # noqa: E402
from recomp.analysis.image import Image, Section  # noqa: E402
from recomp.lift.lifter import Lifter  # noqa: E402
from recomp.verify import differential as D  # noqa: E402
from test_recomp_discover import Asm  # noqa: E402

BASE, TEXT = 0x400000, 0x401000

# Every snippet uses esi (DATA+0x180) as its data pointer and ends with ret.
SNIPPETS = {
    "xadd_mem": "8b5604 f00fc116 c3",                        # mov edx,[esi+4]; lock xadd [esi],edx
    "xadd_reg": "8b06 8b5604 0fc1d0 894608 89560c c3",      # xadd eax,edx; store both
    "imul_r8": "8a06 f66e01 66894608 0f92460a 0f90460b c3",  # imul byte [esi+1]; setc; seto
    "rcr_rcl": ("8b06 034604 d1d8 894608 0f92460c 8b4610 034614 d1d0 894618 0f92461c "
                "8a4e20 8b4624 034628 d3d8 89462c 0f924630 c3"),
    "rotate_8_16": ("8a06 8a4e01 d2c0 884608 0f924609 668b4602 66d3c8 6689460a 0f92460c "
                    "d0c8 88460d c3"),
    "shld_shrd": ("8b06 8b5604 8a4e08 0fa5d0 89460c 8b06 0facd005 894610 0f924614 "
                  "8b06 0fadd0 894618 c3"),
    "bit_ops": ("8b06 25ff030000 0fab06 0f924640 0fa306 0f924641 8b4604 83e01f 0fb34608 "
                "0f924642 0fbb460c 0f924643 0fbae607 0f924644 c3"),
    "xlatb": "89f3 8a4650 d7 884660 c3",
    "scasb": ("89f7 8a4610 b920000000 f2ae 894e70 897e74 0f944678 89f7 8a4611 b910000000 "
              "f3ae 894e7c c3"),
    "cmps": ("56 8d7e20 b906000000 f3a4 5e 8d7e20 b90a000000 f3a6 894e70 0f944674 "
             "8d7e40 b904000000 66f3a7 894e78 c3"),
    "flags_roundtrip": ("8b06 034604 9c 58 25c5080000 894608 8b460c 25c5080000 50 9d "
                        "0f924610 0f944611 0f984612 0f904613 0f9a4614 c3"),
    # fld a; fld b; fnsave [esp]; fld1 (clobbers); frstor [esp]; fstp; fstp.
    # fprem1 itself is checked against the real FPU in x87_native_test.c: Unicorn
    # rounds the quotient wrongly for negative divisors.
    "fnsave_frstor": ("83ec6c d906 d94604 dd3424 d9e8 dd2424 83c46c d95e0c d95e10 c3"),
}


def build_image():
    asm = Asm(TEXT)
    entries = {}
    for name, code in SNIPPETS.items():
        asm.align(16)
        entries[name] = asm.here()
        asm.raw(bytes.fromhex(code.replace(" ", "")))
    asm.align(16)
    text = asm.build()
    image = Image(BASE, TEXT, [Section(".text", TEXT, text, True),
                               Section(".rdata", TEXT + 0x10000, bytes(16), False)])
    flat = bytes(TEXT - BASE) + text
    return image, entries, flat


def case(entry: int, rng: random.Random) -> D.Case:
    c = D.random_case(entry, rng, 0x027F)
    # Integer snippets want mixed bit patterns, not mostly floats.
    data = bytearray(c.data)
    for i in range(0x180, 0x200, 4):
        struct.pack_into("<I", data, i, rng.getrandbits(32))
    for i in (0x180, 0x184):  # fprem1 operands: finite, non-zero floats
        struct.pack_into("<f", data, i, rng.choice([1, -1]) * rng.uniform(0.5, 1000))
    return D.Case(c.entry, c.regs, c.cw, bytes(data), c.args, c.st_in)


@unittest.skipUnless(D.GCC.exists(), "requires MSYS2 gcc")
class LiftedInstructionTest(unittest.TestCase):
    def test_snippets_match_unicorn(self):
        image, entries, flat = build_image()
        lifter = Lifter(Discovery(image), set(entries.values()))
        result = lifter.lift(sorted(entries.values()))
        self.assertEqual(result.faults, {}, "lifter rejected an instruction")
        ref = D.UnicornReference(flat, BASE)
        rng = random.Random(7)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "snippets.c").write_text(result.source, encoding="utf-8")
            (tmp / "image.raw").write_bytes(b"T123RAW\0" + struct.pack("<II", BASE, len(flat)) + flat)
            runner = D.build_runner(tmp / "snippets.c", tmp / "runner.exe")
            cases, refs, names = [], [], []
            for name, entry in entries.items():
                for _ in range(200):
                    c = case(entry, rng)
                    r = ref.run(c)
                    self.assertIsNotNone(r, f"{name} does not run in Unicorn")
                    cases.append(c)
                    refs.append(r)
                    names.append(name)
            lifted = D.run_lifted(runner, tmp / "image.raw", cases, tmp)
            failures = {}
            for name, r, l in zip(names, refs, lifted):
                diffs = D.compare(r, l)
                if diffs:
                    failures.setdefault(name, diffs)
            self.assertEqual(failures, {})


if __name__ == "__main__":
    unittest.main()
