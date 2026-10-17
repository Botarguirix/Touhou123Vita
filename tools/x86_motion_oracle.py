"""Run the original 1.10a input-pattern matcher over synthetic ring snapshots.

This is a reverse-engineering probe, not a game emulator. It validates the
matcher itself against controlled 90-sample deque fixtures; it does not model
the game's input producer.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local/python-deps"))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EAX,
)

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
MATCHER = 0x46CC90
PLAYER = 0x01000000
BLOCK_VECTOR = 0x01100000
PATTERN = 0x01200000
STACK = 0x02000000
STOP = 0x03000000
RING_BLOCKS = 0x04000000


class MotionOracle:
    def __init__(self, exe: Path):
        raw = exe.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != REFERENCE_SHA256:
            raise ValueError(f"reference SHA256 mismatch: {self.sha256}")
        pe = pefile.PE(data=raw)
        image = pe.get_memory_mapped_image()
        base = pe.OPTIONAL_HEADER.ImageBase
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(base, (len(image) + 4095) & ~4095)
        self.uc.mem_write(base, image)
        for address, size in (
            (PLAYER, 0x1000), (BLOCK_VECTOR, 0x1000), (PATTERN, 0x1000),
            (STACK, 0x10000), (STOP, 0x1000), (RING_BLOCKS, 12 * 0x1000),
        ):
            self.uc.mem_map(address, size)
        # The CRT cookie checker uses this process-global value. Assertions
        # are no-ops in this probe; the matcher and deque helpers run as x86.
        self.uc.mem_write(0x8943B8, struct.pack("<I", 0x12345678))
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc, address, _size, _user):
        if address not in (0x81FF70, 0x81FB35):
            return
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        uc.reg_write(UC_X86_REG_ESP, esp + 4)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def match(self, pattern: str, samples: list[int], history: int, direction: int):
        if not samples or len(samples) != 90:
            raise ValueError("fixture must contain exactly 90 chronological samples")
        if not pattern or len(pattern) > 9:
            raise ValueError("pattern length must be in 1..9")
        if history < 1 or history > 90:
            raise ValueError("history must be in 1..90")
        if not -128 <= direction <= 127:
            raise ValueError("direction must fit in signed byte")

        u = self.uc
        u.mem_write(PLAYER, bytes(0x1000))
        u.mem_write(BLOCK_VECTOR, bytes(0x1000))
        u.mem_write(PATTERN, pattern.encode("ascii") + b"\0")
        # deque layout from 0042cf90 / 0046cc90: +4 block vector,
        # +8 block count, +0xc logical head, +0x10 sample count.
        u.mem_write(PLAYER + 0x7B4, struct.pack("<I", BLOCK_VECTOR))
        u.mem_write(PLAYER + 0x7B8, struct.pack("<I", 12))
        u.mem_write(PLAYER + 0x7BC, struct.pack("<I", 0))
        u.mem_write(PLAYER + 0x7C0, struct.pack("<I", 90))
        u.mem_write(BLOCK_VECTOR, struct.pack(
            "<12I", *(RING_BLOCKS + i * 0x1000 for i in range(12))
        ))
        for block in range(12):
            chunk = samples[block * 8:block * 8 + 8]
            chunk += [0] * (8 - len(chunk))
            u.mem_write(RING_BLOCKS + block * 0x1000,
                        struct.pack("<8H", *chunk))
        u.mem_write(PLAYER + 0x104, struct.pack("<b", direction))

        esp = STACK + 0xEFFC
        args = (STOP, PATTERN, len(pattern), history)
        u.mem_write(esp, struct.pack("<4I", *args))
        u.reg_write(UC_X86_REG_ECX, PLAYER)
        u.reg_write(UC_X86_REG_ESP, esp)
        u.reg_write(UC_X86_REG_EIP, MATCHER)
        u.emu_start(MATCHER, STOP, count=10000)
        return u.reg_read(UC_X86_REG_EAX) & 0xFF


def vectors():
    cases = []
    for direction in (1, -1):
        for pattern, code, sample in (
            ("NRNR", 1, 0x02), ("NLNL", 1, 0x01), ("DD", 1, 0x80),
        ):
            seq = [0] * 90
            if pattern == "NRNR": seq[-4:] = [0, sample, 0, sample]
            elif pattern == "NLNL": seq[-4:] = [0, sample, 0, sample]
            else: seq[-2:] = [sample, sample]
            cases.append(dict(pattern=pattern, samples=seq, history=15,
                              direction=direction, expected=code))
    for pattern, token, history in (("N09", 0x06, 20), ("N07", 0x05, 20),
                                    ("N08", 0x04, 20)):
        seq = [0] * 90
        seq[-3:] = [0, 0x08, token]
        cases.append(dict(pattern=pattern, samples=seq, history=history,
                          direction=1, expected=1))
    for pattern, tail, history, direction, expected in (
        ("NRNR", [0, 0x02, 0, 0x01], 15, 1, 0),
        ("NRNR", [0, 0x02, 0, 0x02], 3, 1, 0),
        ("N09", [0, 0x08, 0x05], 20, 1, 0),
        ("2N2A", [0x08, 0, 0x08, 0x10], 15, 1, 1),
        ("X", [0x10], 15, 1, 1),
        ("X", [0x20], 15, 1, 2),
        ("X", [0x40], 15, 1, 3),
        ("X", [0x80], 15, 1, 4),
    ):
        seq = [0] * 90
        seq[-len(tail):] = tail
        cases.append(dict(pattern=pattern, samples=seq, history=history,
                          direction=direction, expected=expected))
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("exe", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    oracle = MotionOracle(args.exe)
    rows = []
    for case in vectors():
        result = oracle.match(case["pattern"], case["samples"],
                              case["history"], case["direction"])
        rows.append({k: v for k, v in case.items() if k != "samples"} |
                    {"result": result, "passed": result == case["expected"]})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(json.dumps({
        "schema": 1, "reference_sha256": oracle.sha256,
        "matcher_va": hex(MATCHER), "fixture_samples": 90,
        "cases": rows, "passed": all(row["passed"] for row in rows),
        "scope": "synthetic ring; producer is not modeled; 0042a950 runs as x86",
    }, indent=2) + "\n", encoding="utf-8")
    args.output.write_text("pattern,history,direction,expected,result,passed\n" +
        "".join(f'{r["pattern"]},{r["history"]},{r["direction"]},'
                f'{r["expected"]},{r["result"]},{int(r["passed"])}\n' for r in rows),
        encoding="ascii")
    print(f"matcher vectors: {len(rows)}; passed: {sum(r['passed'] for r in rows)}")


if __name__ == "__main__":
    main()
