"""F1.2 equivalence gates for the lifter and the guest runtime.

* Animation kernel: lifted 0x438c60 and its vtable methods reproduce the 2,048
  vectors of tools/x86_animation_oracle.py exactly.
* x87 model: the runtime matches the host's real x87 FPU under every precision and
  rounding control (and the data is shown to be sensitive to both).
* Real x87 functions: leaf functions of the game with x87 code, lifted, match the
  original run in Unicorn under five control words.

Generated C and binaries go to a temporary directory; nothing is versioned.
"""
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recomp.verify import differential as D  # noqa: E402

EXE = ROOT / "original/th123.exe"
SHA = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
DISCOVERY = ROOT / "artifacts/recomp" / SHA / "discovery.json"
GCC = D.GCC
RUNTIME = ROOT / "recomp/runtime"
CFLAGS = ["-std=gnu11", "-O2", "-Wall", "-Wextra", "-frounding-math", f"-I{RUNTIME}"]

# Known deviations, excluded with their reason (docs/F1_LIFTER.md):
EXCLUDED = {
    0x827800: "f2xm1/fscale: QEMU computes transcendentals in double, not a valid oracle",
    0x82d6a3: "CRT routine that raises FP exceptions; sticky exception flags are not modelled",
}


def gcc(*args):
    env = dict(os.environ, PATH=str(GCC.parent) + os.pathsep + os.environ.get("PATH", ""))
    subprocess.run([str(GCC), *args], check=True, env=env, capture_output=True, text=True)


def lift(entries, output):
    from recomp.lift_functions import lift_to
    return lift_to(EXE, entries, output)


@unittest.skipUnless(GCC.exists(), "requires MSYS2 gcc")
class X87NativeModelTest(unittest.TestCase):
    def test_runtime_matches_host_fpu_under_all_control_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "x87_native_test.exe"
            gcc(*CFLAGS, str(RUNTIME / "guest.c"), str(ROOT / "recomp/tests/x87_native_test.c"),
                "-lm", "-o", str(exe))
            run = subprocess.run([str(exe), "4000"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn(" 0 mismatches", run.stdout)


@unittest.skipUnless(EXE.exists() and GCC.exists() and DISCOVERY.exists(),
                     "requires th123.exe, MSYS2 gcc and recomp/discover.py output")
class AnimationKernelTest(unittest.TestCase):
    def test_lifted_kernel_reproduces_x86_oracle(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            subprocess.run([sys.executable, str(ROOT / "tools/x86_animation_oracle.py"), str(EXE),
                            str(tmp / "oracle.csv")], check=True, capture_output=True)
            summary = lift([0x438c60, 0x464ae0, 0x464b50, 0x464b70, 0x464bf0], tmp / "anim.c")
            self.assertEqual(summary["faults"], {})
            exe = tmp / "anim.exe"
            gcc(*CFLAGS, str(RUNTIME / "guest.c"), str(tmp / "anim.c"),
                str(ROOT / "recomp/tests/anim_harness.c"), "-lm", "-o", str(exe))
            run = subprocess.run([str(exe), str(EXE), str(tmp / "oracle.csv")],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            oracle = (tmp / "oracle.csv").read_text().splitlines()
            lifted = run.stdout.splitlines()
            self.assertEqual(len(oracle), 2048)
            self.assertEqual(lifted, oracle)
            self.assertIn("graphics refresh callbacks: 1128", run.stderr)


@unittest.skipUnless(EXE.exists() and GCC.exists() and DISCOVERY.exists(),
                     "requires th123.exe, MSYS2 gcc and recomp/discover.py output")
class RealX87FunctionsTest(unittest.TestCase):
    CONTROL_WORDS = (0x027F, 0x037F, 0x007F, 0x0E7F, 0x067F)

    def test_lifted_x87_leaf_functions_match_original(self):
        import pefile
        pe = pefile.PE(str(EXE))
        ref = D.UnicornReference(pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.ImageBase)
        doc = json.loads(DISCOVERY.read_text(encoding="utf-8"))
        rng = random.Random(5)
        selected = []
        for f in doc["functions"]:
            if (f["calls"] or f["imports"] or f["switches"] or f["noreturn"] or f["bytes"] > 220
                    or f["tailcalls"] or f["unresolved_jumps"]):
                continue
            entry = int(f["entry"], 16)
            ok, x87 = True, False
            for _ in range(6):
                ref.x87_executed = False
                if ref.run(D.random_case(entry, rng, 0x027F)) is None:
                    ok = False
                    break
                x87 |= ref.x87_executed
            if ok and x87:
                selected.append(entry)
        self.assertGreaterEqual(len(selected), 50)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            lift(selected, tmp / "x87.c")
            runner = D.build_runner(tmp / "x87.c", tmp / "diff_runner.exe")
            failures = {}
            compared = 0
            for cw in self.CONTROL_WORDS:
                cases, refs = [], []
                for entry in selected:
                    for _ in range(25):
                        case = D.random_case(entry, rng, cw)
                        result = ref.run(case)
                        if result is not None and not D.x87_stack_fault(result):
                            cases.append(case)
                            refs.append(result)
                for case, r, l in zip(cases, refs, D.run_lifted(runner, EXE, cases, tmp)):
                    if case.entry in EXCLUDED:
                        continue
                    compared += 1
                    diffs = D.compare(r, l)
                    if diffs:
                        failures.setdefault(f"{case.entry:#x} cw={cw:#06x}", diffs)
            self.assertGreater(compared, 5000)
            self.assertEqual(failures, {})


if __name__ == "__main__":
    unittest.main()
