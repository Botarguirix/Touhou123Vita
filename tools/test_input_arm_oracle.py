"""Differentially execute the Vita-compiled input matcher against x86 vectors.

The test compiles the C implementation with VitaSDK's ARMv7 compiler, then
runs that freestanding ARM ELF in Unicorn beside the original x86 oracle.
"""
import argparse
import os
import random
import struct
import subprocess
import tempfile
from pathlib import Path

from x86_motion_oracle import MotionOracle, vectors
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_INTR, UC_HOOK_CODE, UcError
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_R0

ROOT = Path(__file__).resolve().parents[1]
CODE_BASE = 0x00010000
MEMORY_SIZE = 0x00800000
STACK_TOP = 0x007F0000


def extended_cases():
    rng = random.Random(0x123A)
    face_positive = [0x0b, 0x09, 0x08, 0x0a, 0x01, 0x00, 0x02, 0x05, 0x04, 0x06]
    face_negative = [0x0b, 0x0a, 0x08, 0x09, 0x02, 0x00, 0x01, 0x06, 0x04, 0x05]
    button = {"A": 0x10, "B": 0x20, "C": 0x40, "D": 0x80, "X": 0x40}
    base_patterns = ["NRNR", "NLNL", "DD", "N09", "N07", "N08",
                     "2N2A", "NR", "N2A", "6A", "N", "0", "X",
                     "AB", "2A", "NX", "RX", "8D"]
    cases = []
    for i in range(128):
        pattern = base_patterns[i % len(base_patterns)]
        direction = 1 if (i // len(base_patterns)) % 2 == 0 else -1
        table = face_positive if direction > 0 else face_negative
        seq = []
        for token in pattern:
            if token == "N": seq.append(0)
            elif token == "R": seq.append(0x02)
            elif token == "L": seq.append(0x01)
            elif token in button: seq.append(button[token])
            else: seq.append(table[int(token)])
        # Preserve a few deliberate overlapping button/direction samples and
        # otherwise insert an exact contiguous positive command near history end.
        if i % 3 == 0 and len(seq) >= 2 and pattern[-1] in button and seq[-2] < 0x10:
            seq[-2] |= seq[-1]
            seq.pop()
        samples = [0] * 90
        start = 90 - len(seq) - (i % 4)
        samples[start:start + len(seq)] = seq
        cases.append({"pattern": pattern, "samples": samples,
                      "history": rng.choice((15, 20, 30, 90)),
                      "direction": direction})

    alphabet = "NRL0123456789ABCDX"
    sample_values = [0x000, 0x001, 0x002, 0x004, 0x005, 0x006, 0x008,
                     0x009, 0x00a, 0x00b, 0x010, 0x020, 0x040, 0x080,
                     0x030, 0x050, 0x0c0, 0x0f0, 0x110, 0x210, 0x400]
    for _ in range(256):
        pattern = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 6)))
        samples = [rng.choice(sample_values) for _ in range(90)]
        cases.append({"pattern": pattern, "samples": samples,
                      "history": rng.choice((1, 2, 3, 5, 10, 15, 20, 30, 60, 90)),
                      "direction": rng.choice((-1, 1))})
    return cases


def run_arm_elf(elf_path: Path) -> int:
    raw = elf_path.read_bytes()
    if raw[:4] != b"\x7fELF" or raw[4] != 1 or raw[5] != 1:
        raise ValueError("expected a little-endian ELF32 binary")
    header = struct.unpack_from("<16sHHIIIIIHHHHHH", raw)
    entry, phoff, phentsize, phnum = header[4], header[5], header[9], header[10]
    emu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    emu.mem_map(CODE_BASE, MEMORY_SIZE - CODE_BASE)
    loaded = False
    for index in range(phnum):
        p = struct.unpack_from("<IIIIIIII", raw, phoff + index * phentsize)
        p_type, p_offset, p_vaddr, _paddr, p_filesz, p_memsz = p[:6]
        if p_type != 1:
            continue
        if p_vaddr < CODE_BASE or p_vaddr + p_memsz > MEMORY_SIZE:
            raise ValueError(f"ELF segment outside Unicorn memory: {p_vaddr:#x}")
        if p_filesz:
            emu.mem_write(p_vaddr, raw[p_offset:p_offset + p_filesz])
        if p_memsz > p_filesz:
            emu.mem_write(p_vaddr + p_filesz, bytes(p_memsz - p_filesz))
        loaded = True
    if not loaded:
        raise ValueError("ELF has no loadable segments")

    result = {"interrupt": None, "return": None}
    last_pc = {"value": entry}

    def on_interrupt(machine, number, _user):
        result["interrupt"] = number
        result["return"] = machine.reg_read(UC_ARM_REG_R0)
        machine.emu_stop()

    def on_code(_machine, address, _size, _user):
        last_pc["value"] = address

    emu.hook_add(UC_HOOK_INTR, on_interrupt)
    emu.hook_add(UC_HOOK_CODE, on_code)
    emu.reg_write(UC_ARM_REG_SP, STACK_TOP)
    emu.reg_write(UC_ARM_REG_PC, entry)
    try:
        emu.emu_start(entry, MEMORY_SIZE, count=5_000_000)
    except UcError as error:
        pc = last_pc["value"]
        print(f"ARM Unicorn stopped at PC={pc:#x}, bytes="
              f"{bytes(emu.mem_read(pc, 8)).hex()}: {error}")
        raise
    if result["interrupt"] is None:
        raise RuntimeError("ARM harness returned without reaching its SVC")
    return result["return"]


def render_harness(cases, oracle_results) -> str:
    rows = []
    for case, expected in zip(cases, oracle_results):
        values = ",".join(f"0x{x:04x}" for x in case["samples"])
        rows.append(
            f'{{"{case["pattern"]}",{case["history"]},'
            f'{case["direction"]},{expected},{{{values}}}}}'
        )
    return """
#include <stdint.h>
#include "t123/input.h"
typedef struct {
    const char *pattern;
    unsigned history;
    int8_t facing;
    uint8_t expected;
    uint16_t samples[90];
} Vector;
static const Vector vectors[] = {
""" + ",\n".join(rows) + """
};
int t123_input_oracle_test(void) {
    T123InputHistory history;
    t123_input_history_reset(&history, 0);
    for (unsigned i = 0; i < 100; ++i)
        t123_input_history_push(&history, (uint16_t)i);
    if (history.count != 90 || t123_input_history_get(&history, 0) != 10 ||
        t123_input_history_get(&history, 89) != 99) return 0x00ff0000;
    for (unsigned v = 0; v < sizeof(vectors) / sizeof(vectors[0]); ++v) {
        history.count = 90;
        history.next = 0;
        for (unsigned i = 0; i < 90; ++i) history.samples[i] = vectors[v].samples[i];
        uint8_t result = t123_input_match(&history, vectors[v].pattern,
                                          vectors[v].history, vectors[v].facing);
        if (result != vectors[v].expected) return ((int)v + 1) * 256 + result;
    }
    return 0;
}
"""


START_ASM = """
.section .text.start,"ax",%progbits
.global _start
.type _start,%function
_start:
    bl t123_input_oracle_test
    svc #0
1:  b 1b
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--vita-sdk", type=Path,
                        default=Path(os.environ.get("VITASDK", r"C:\vitasdk")))
    parser.add_argument("--report", type=Path,
                        default=ROOT / "artifacts/x86-arm-input-vectors.json")
    args = parser.parse_args()

    cc = args.vita_sdk / "bin/arm-vita-eabi-gcc.exe"
    if not cc.is_file():
        raise FileNotFoundError(f"VitaSDK compiler not found: {cc}")
    checked_cases = vectors()
    cases = checked_cases + extended_cases()
    oracle = MotionOracle(args.exe)
    expected = [oracle.match(case["pattern"], case["samples"],
                             case["history"], case["direction"])
                for case in cases]
    if any(value != case["expected"]
           for value, case in zip(expected, checked_cases)):
        raise AssertionError("x86 oracle did not satisfy the checked-in vectors")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="input-arm-oracle-",
                                     dir=args.report.parent) as temp:
        temp = Path(temp)
        harness = temp / "vectors.c"
        startup = temp / "start.S"
        elf = temp / "matcher.elf"
        harness.write_text(render_harness(cases, expected), encoding="ascii")
        startup.write_text(START_ASM, encoding="ascii")
        command = [
            str(cc), "-mcpu=cortex-a9", "-marm", "-O2", "-std=c11",
            "-ffreestanding", "-fno-builtin", "-fno-tree-vectorize",
            "-Wall", "-Wextra", "-Werror",
            "-nostdlib", "-I", str(ROOT / "include"),
            "-Wl,-Ttext=0x10000", "-Wl,-e,_start", "-Wl,--build-id=none",
            str(startup), str(harness), str(ROOT / "src/input.c"), "-lgcc",
            "-o", str(elf),
        ]
        subprocess.run(command, check=True, cwd=ROOT)
        try:
            arm_code = run_arm_elf(elf)
        except Exception:
            objdump = args.vita_sdk / "bin/arm-vita-eabi-objdump.exe"
            if objdump.is_file():
                subprocess.run([str(objdump), "-d", str(elf)], check=False)
            raise

    rows = []
    for case, x86_result in zip(cases, expected):
        rows.append({
            "pattern": case["pattern"], "history": case["history"],
            "direction": case["direction"], "x86": x86_result,
        })
    report = {
        "schema": 1,
        "reference_sha256": oracle.sha256,
        "matcher_va": "0x46cc90",
        "target": "VitaSDK ARMv7 freestanding ELF under Unicorn",
        "vectors": rows,
        "count": len(rows),
        "checked_vectors": len(checked_cases),
        "generated_vectors": len(cases) - len(checked_cases),
        "passed": arm_code == 0,
        "failed_vector": ((arm_code >> 8) - 1) if arm_code and arm_code < 0x00ff0000 else None,
        "arm_result": (arm_code & 0xff) if arm_code and arm_code < 0x00ff0000 else None,
        "history_contract_failed": arm_code >= 0x00ff0000,
    }
    args.report.write_text(__import__("json").dumps(report, indent=2) + "\n",
                           encoding="utf-8")
    print(f"matcher differential: {len(rows)} x86/ARM vectors; "
          f"{'passed' if arm_code == 0 else f'failed at vector {arm_code - 1}'}")
    if arm_code >= 0x00ff0000:
        print("  90-sample history reset/wrap contract failed")
        raise SystemExit(1)
    if arm_code:
        failed_index = (arm_code >> 8) - 1
        arm_result = arm_code & 0xff
        failed = cases[failed_index]
        print(f"  pattern={failed['pattern']} history={failed['history']} "
              f"direction={failed['direction']} x86={expected[failed_index]} "
              f"ARM={arm_result}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
