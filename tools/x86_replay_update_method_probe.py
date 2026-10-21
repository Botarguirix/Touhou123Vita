#!/usr/bin/env python3
"""Execute original replay update method 0x481040 on real replay words in Unicorn."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile  # noqa: E402
from tools.replay_layout import parse_replay  # noqa: E402
from unicorn import UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32, Uc  # noqa: E402
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP,
                               UC_X86_REG_ESP, UC_X86_REG_EDI)  # noqa: E402

EXE_SHA256 = "24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3"
REPLAY_SHA256 = "6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e"
UPDATE = 0x00481040
CAPTURE = 0x0048110F  # first instruction after the cursor increment
MODE_GETTER = 0x0043CED0
INPUT_CONTEXT_GETTER = 0x0043CEC0
DECODER = 0x0042A410
INPUT_MODE_GETTER = 0x0043CCD0
WORD_READER = 0x0042EA50
INPUT_SETTER = 0x0043CC80
MANAGER_GLOBAL = 0x0085D748
STOP = 0x00960000


class UpdateHarness:
    def __init__(self, exe_path: Path, words: list[int]):
        raw = exe_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != EXE_SHA256:
            raise ValueError(f"unexpected executable SHA-256: {digest}")
        pe = pefile.PE(data=raw)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        image_size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xFFF) & ~0xFFF
        self.emu = Uc(UC_ARCH_X86, UC_MODE_32)
        self.emu.mem_map(0, 0x1000)
        self.emu.mem_map(self.base, image_size)
        self.emu.mem_write(self.base, raw[:pe.OPTIONAL_HEADER.SizeOfHeaders])
        for section in pe.sections:
            data = section.get_data()
            if data:
                self.emu.mem_write(self.base + section.VirtualAddress, data)
        self.emu.mem_map(0x900000, 0x8000)
        vector_size = max(0x1000, (len(words) * 2 + 0xFFF) & ~0xFFF)
        self.emu.mem_map(0xA00000, vector_size)
        self.emu.mem_map(0x980000, 0x10000)
        self.instance = 0x900000
        self.manager = 0x901000
        self.wrapper = 0x902000
        self.input_object = 0x903000
        self.input_state = 0x904000
        self.vector = 0xA00000
        self.stack = 0x980000
        self.words = words
        self.callbacks: list[tuple[int, int]] = []
        self.read_indexes: list[int] = []
        self._u32(MANAGER_GLOBAL, self.manager)
        self._u32(self.manager + 0x10, 2)
        self._u32(self.manager + 0x14, 0)
        self._u32(self.manager + 0x28, len(words))
        self._u32(self.manager + 0x34, 3)
        self._u32(self.manager + 0x18, self.vector)
        self._u32(self.instance + 0x10, self.wrapper)
        self._u32(self.wrapper + 0x740, self.input_object)
        self._u32(self.input_object, self.input_state)
        self._u32(self.input_state + 0x60, 0)
        if words:
            self.emu.mem_write(self.vector, struct.pack(f"<{len(words)}H", *words))
        self.initial_sp = self.stack + 0x8000
        self.emu.mem_write(self.initial_sp, struct.pack("<I", STOP))
        self.emu.hook_add(UC_HOOK_CODE, self._hook)

    def _u32(self, address: int, value: int) -> None:
        self.emu.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _return(self, machine: Uc, value: int = 0) -> None:
        esp = machine.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
        machine.reg_write(UC_X86_REG_ESP, esp + 4)
        machine.reg_write(UC_X86_REG_EIP, ret)
        machine.reg_write(UC_X86_REG_EAX, value & 0xFFFFFFFF)

    def _hook(self, machine: Uc, address: int, _size: int, _user: object) -> None:
        if address == CAPTURE:
            machine.emu_stop()
        elif address == MODE_GETTER:
            self._return(machine, 2)
        elif address == INPUT_CONTEXT_GETTER:
            self._return(machine, self.input_object)
        elif address == DECODER:
            self._return(machine, 0)
        elif address == INPUT_MODE_GETTER:
            self._return(machine, 8)
        elif address == WORD_READER:
            esp = machine.reg_read(UC_X86_REG_ESP)
            index = struct.unpack("<I", machine.mem_read(esp + 4, 4))[0]
            self.read_indexes.append(index)
            pointer = self.vector + index * 2 if 0 <= index < len(self.words) else self.vector
            self._return(machine, pointer)
        elif address == INPUT_SETTER:
            esp = machine.reg_read(UC_X86_REG_ESP)
            _, input_id, pressed = struct.unpack("<III", machine.mem_read(esp, 12))
            self.callbacks.append((input_id, pressed & 0xFF))
            self._return(machine, 0)

    def step(self, expected_word: int, cursor_index: int,
             read_index: int | None = None) -> dict[str, object]:
        if read_index is None:
            read_index = cursor_index
        self.callbacks.clear()
        self.read_indexes.clear()
        self._u32(0, 0)
        self._u32(self.manager + 0x14, cursor_index)
        self.emu.reg_write(UC_X86_REG_ESP, self.initial_sp)
        self.emu.reg_write(UC_X86_REG_EDI, self.instance)
        self.emu.reg_write(UC_X86_REG_ECX, self.instance)
        self.emu.emu_start(UPDATE, STOP, count=5000)
        if self.emu.reg_read(UC_X86_REG_EIP) != CAPTURE:
            raise RuntimeError(f"update method stopped at {self.emu.reg_read(UC_X86_REG_EIP):#x}")
        after = struct.unpack("<I", self.emu.mem_read(self.manager + 0x14, 4))[0]
        mask = struct.unpack("<H", self.emu.mem_read(self.input_state + 0x60, 2))[0]
        expected_events = [(0x3C, int(bool(expected_word & 0x4000))),
                           (0x3D, int(bool(expected_word & 0x2000)))]
        if (after != read_index + 1 or self.read_indexes != [read_index]
                or mask != expected_word or self.callbacks != expected_events):
            raise RuntimeError({"word": expected_word, "cursor_index": cursor_index,
                                "read_index": read_index,
                                "after": after, "mask": mask,
                                "reads": self.read_indexes, "callbacks": self.callbacks})
        return {"cursor_index": cursor_index, "read_index": read_index,
                "word": expected_word,
                "mask_written": mask, "cursor_after": after,
                "callbacks": [[key, pressed] for key, pressed in self.callbacks]}


def analyze(exe_path: Path, replay_path: Path, samples_per_record: int = 64,
            all_words: bool = False) -> dict[str, object]:
    replay_raw = replay_path.read_bytes()
    replay_sha = hashlib.sha256(replay_raw).hexdigest()
    if replay_sha != REPLAY_SHA256:
        raise ValueError(f"unexpected replay SHA-256: {replay_sha}")
    parsed = parse_replay(replay_raw)
    records = []
    for rec_index, record in enumerate(parsed["records"]):
        words = record["values"]
        if not all_words and len(words) < samples_per_record:
            raise ValueError(f"record {rec_index} is shorter than sample window")
        # Include early consecutive words and spread samples by default, or
        # execute every stored word for the full replay validation.
        indexes = (range(len(words)) if all_words else
                   sorted(set(range(samples_per_record)) |
                          {len(words) * part // 8 for part in range(1, 8)}))
        harness = UpdateHarness(exe_path, words)
        first_samples: list[dict[str, object]] = []
        last_samples: list[dict[str, object]] = []
        flagged_samples: list[dict[str, object]] = []
        flagged_count = 0
        executed = 0
        for index in indexes:
            sample = harness.step(words[index], index)
            executed += 1
            if index < 8:
                first_samples.append(sample)
            if index >= len(words) - 8:
                last_samples.append(sample)
            if words[index] & 0x6000:
                flagged_count += 1
                if len(flagged_samples) < 16:
                    flagged_samples.append(sample)
        # Exercise the natural end-of-vector guard: an exhausted index wraps to zero.
        wrap = harness.step(words[0], len(words), read_index=0)
        if wrap["cursor_after"] != 1 or wrap["read_index"] != 0:
            raise RuntimeError(f"record {rec_index}: cursor end guard failed")
        records.append({"record": rec_index, "word_count": len(words),
                        "invocations_executed": executed,
                        "words_with_0x2000_or_0x4000_flags": flagged_count,
                        "first_samples": first_samples,
                        "flagged_samples": flagged_samples,
                        "last_samples": last_samples,
                        "end_guard_wrap": wrap})
    total_invocations = sum(int(record["invocations_executed"]) for record in records)
    return {
        "schema": 1,
        "exe_sha256": EXE_SHA256,
        "replay_sha256": replay_sha,
        "method_va": f"0x{UPDATE:08x}",
        "capture_va": f"0x{CAPTURE:08x}",
        "records": records,
        "all_words_executed": all_words,
        "total_invocations_executed": total_invocations,
        "checks": {"sampled_words_match_original_mask_store": True,
                   "two_input_flags_match_original_setter_calls": True,
                   "one_index_increment_per_guarded_invocation": True,
                   "end_of_vector_guard_wraps_to_zero": True},
        "scope": "Unicorn executes original instructions in 0x481040 up to the cursor increment. System getters, the input decoder, indexed word reader, and setter are controlled hooks. This validates per-invocation mechanics with real replay words, not live-game call cadence or frame timing.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--samples-per-record", type=int, default=64)
    parser.add_argument("--all-words", action="store_true",
                        help="execute 0x481040 once for every uint16 in all replay records")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(analyze(args.exe, args.replay, args.samples_per_record,
                                args.all_words), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
