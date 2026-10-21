#!/usr/bin/env python3
"""Run the original Story-manager callback prefix and observe its decoder dispatch."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile  # noqa: E402
from unicorn import UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32, Uc  # noqa: E402
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP,
                               UC_X86_REG_ESP)  # noqa: E402

EXE_SHA256 = "24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3"
STORY_UPDATE = 0x0047EE10
AFTER_REPLAY_DECODER = 0x0047EE4C
REPLAY_INPUT_GLOBAL = 0x0085EC98
REPLAY_STATE_GLOBAL = 0x0085EC08
DECODER = 0x0042A410
INPUT_SETTER = 0x0043CC80
LOCK_VAS = {0x0040AB50, 0x0040AB60}
FLAG_MAP = ((0x8000, 0x3B), (0x4000, 0x3C), (0x2000, 0x3D),
            (0x1000, 0x3F), (0x0800, 0x40), (0x0400, 0x41))
REPLAY_SHA256 = "6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e"
STOP = 0x00960000

try:  # supports both `python tools/...py` and unittest module imports
    from tools.replay_layout import parse_replay  # type: ignore[import-not-found]  # noqa: E402
except ModuleNotFoundError:
    from replay_layout import parse_replay  # noqa: E402


class StoryCallbackHarness:
    def __init__(self, exe_path: Path, state: int, words: list[int] | None = None):
        raw = exe_path.read_bytes()
        self.exe_sha256 = hashlib.sha256(raw).hexdigest()
        if self.exe_sha256 != EXE_SHA256:
            raise ValueError(f"unexpected executable SHA-256: {self.exe_sha256}")
        pe = pefile.PE(data=raw)
        base = pe.OPTIONAL_HEADER.ImageBase
        image_size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xFFF) & ~0xFFF
        self.emu = Uc(UC_ARCH_X86, UC_MODE_32)
        self.emu.mem_map(0, 0x1000)
        self.emu.mem_map(base, image_size)
        self.emu.mem_write(base, raw[:pe.OPTIONAL_HEADER.SizeOfHeaders])
        for section in pe.sections:
            data = section.get_data()
            if data:
                self.emu.mem_write(base + section.VirtualAddress, data)
        self.emu.mem_map(0x900000, 0x1000)
        self.emu.mem_map(0x910000, 0x1000)
        block_count = max(1, (len(words or []) + 7) // 8)
        table_size = max(0x1000, (block_count * 4 + 0xFFF) & ~0xFFF)
        data_size = max(0x1000, (block_count * 16 + 0xFFF) & ~0xFFF)
        self.emu.mem_map(0x920000, table_size)
        self.emu.mem_map(0x930000, data_size)
        self.emu.mem_map(0x980000, 0x10000)
        self.manager = 0x900000
        self.context = 0x910000
        self.table = 0x920000
        self.data = 0x930000
        self.stack = 0x980000
        self.initial_sp = self.stack + 0x8000
        self.state = state
        self.words = words
        self.intercept_decoder = words is None
        self.decoder_receivers: list[int] = []
        self.input_events: list[tuple[int, int]] = []
        self.emu.mem_write(REPLAY_STATE_GLOBAL, struct.pack("<I", state))
        if words is not None:
            if len(words) % 2:
                raise ValueError("Story replay decoder requires complete word pairs")
            self.emu.mem_write(REPLAY_INPUT_GLOBAL + 0xF0, struct.pack("<I", 3))
            self.emu.mem_write(REPLAY_INPUT_GLOBAL + 0x104, struct.pack("<I", self.context))
            self.emu.mem_write(self.context + 0x40, struct.pack("<I", self.table))
            self.emu.mem_write(self.context + 0x44, struct.pack("<I", block_count))
            self.emu.mem_write(self.context + 0x48, struct.pack("<I", 0))
            self.emu.mem_write(self.context + 0x4C, struct.pack("<I", len(words)))
            if words:
                self.emu.mem_write(self.data, struct.pack(f"<{len(words)}H", *words))
            self.emu.mem_write(self.table, struct.pack(
                f"<{block_count}I", *(self.data + 16 * i for i in range(block_count))))
        self.emu.mem_write(self.initial_sp, struct.pack("<I", STOP))
        self.emu.hook_add(UC_HOOK_CODE, self._hook)

    def _return(self, machine: Uc, value: int = 0) -> None:
        esp = machine.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
        machine.reg_write(UC_X86_REG_ESP, esp + 4)
        machine.reg_write(UC_X86_REG_EIP, ret)
        machine.reg_write(UC_X86_REG_EAX, value & 0xFFFFFFFF)

    def _hook(self, machine: Uc, address: int, _size: int, _user: object) -> None:
        if address == AFTER_REPLAY_DECODER:
            machine.emu_stop()
        elif address == DECODER:
            self.decoder_receivers.append(machine.reg_read(UC_X86_REG_ECX))
            if self.intercept_decoder:
                self._return(machine)
        elif address in LOCK_VAS:
            self._return(machine)
        elif address == INPUT_SETTER:
            esp = machine.reg_read(UC_X86_REG_ESP)
            _, input_id, pressed = struct.unpack("<III", machine.mem_read(esp, 12))
            self.input_events.append((input_id, pressed & 0xFF))
            self._return(machine)

    def run(self) -> dict[str, object]:
        self.emu.reg_write(UC_X86_REG_ESP, self.initial_sp)
        self.emu.reg_write(UC_X86_REG_ECX, self.manager)
        self.emu.emu_start(STORY_UPDATE, STOP, count=20000)
        eip = self.emu.reg_read(UC_X86_REG_EIP)
        if eip != AFTER_REPLAY_DECODER:
            raise RuntimeError(f"Story callback stopped at 0x{eip:08x}")
        return {
            "state": self.state,
            "decoder_call_count": len(self.decoder_receivers),
            "decoder_receivers": [f"0x{value:08x}" for value in self.decoder_receivers],
            "stopped_after_mode_guard": True,
        }

    def step_replay_pair(self, pair_index: int) -> dict[str, object]:
        if self.words is None:
            raise RuntimeError("replay words were not configured")
        start = pair_index * 2
        if start + 1 >= len(self.words):
            raise IndexError(pair_index)
        self.decoder_receivers.clear()
        self.input_events.clear()
        before = struct.unpack("<I", self.emu.mem_read(self.context + 0x4C, 4))[0]
        self.emu.reg_write(UC_X86_REG_ESP, self.initial_sp)
        self.emu.reg_write(UC_X86_REG_ECX, self.manager)
        self.emu.emu_start(STORY_UPDATE, STOP, count=50000)
        eip = self.emu.reg_read(UC_X86_REG_EIP)
        if eip != AFTER_REPLAY_DECODER:
            raise RuntimeError(f"Story callback stopped at 0x{eip:08x}")
        after = struct.unpack("<I", self.emu.mem_read(self.context + 0x4C, 4))[0]
        first, second = self.words[start:start + 2]
        mask_first = struct.unpack("<H", self.emu.mem_read(REPLAY_INPUT_GLOBAL + 0x68, 2))[0]
        mask_second = struct.unpack("<H", self.emu.mem_read(REPLAY_INPUT_GLOBAL + 0xD0, 2))[0]
        expected_events = [(input_id, int(bool(first & bit))) for bit, input_id in FLAG_MAP]
        expected = (self.decoder_receivers == [REPLAY_INPUT_GLOBAL]
                    and before - after == 2
                    and mask_first == (first & 0x03FF)
                    and mask_second == (second & 0x03FF)
                    and self.input_events == expected_events)
        if not expected:
            raise RuntimeError({"pair": pair_index, "remaining_before": before,
                                "remaining_after": after, "receiver": self.decoder_receivers,
                                "masks": [mask_first, mask_second],
                                "events": self.input_events})
        return {"pair": pair_index, "words": [first, second],
                "masks": [mask_first, mask_second], "remaining_after": after,
                "input_events": len(self.input_events)}


def analyze(exe_path: Path) -> dict[str, object]:
    replay_state = StoryCallbackHarness(exe_path, 2).run()
    control_state = StoryCallbackHarness(exe_path, 1).run()
    checks = {
        "state_2_invokes_decoder_once": replay_state["decoder_call_count"] == 1,
        "state_2_passes_global_replay_input": replay_state["decoder_receivers"]
        == [f"0x{REPLAY_INPUT_GLOBAL:08x}"],
        "control_state_skips_decoder": control_state["decoder_call_count"] == 0,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Story callback dispatch mismatch: {checks}")
    return {
        "schema": 1,
        "exe_sha256": EXE_SHA256,
        "method_va": f"0x{STORY_UPDATE:08x}",
        "decoder_va": f"0x{DECODER:08x}",
        "input_global_va": f"0x{REPLAY_INPUT_GLOBAL:08x}",
        "state_global_va": f"0x{REPLAY_STATE_GLOBAL:08x}",
        "runs": {"state_2": replay_state, "control_state_1": control_state},
        "checks": checks,
        "scope": ("Unicorn executes original Story callback instructions through the decoder callsite. The decoder is intercepted; "
                  "this proves callback gating and object dispatch, not input consumption, replay-menu reachability, or frame cadence."),
    }


def analyze_replay(exe_path: Path, replay_path: Path) -> dict[str, object]:
    raw = replay_path.read_bytes()
    replay_sha = hashlib.sha256(raw).hexdigest()
    if replay_sha != REPLAY_SHA256:
        raise ValueError(f"unexpected replay SHA-256: {replay_sha}")
    parsed = parse_replay(raw)
    records = []
    for record_index, record in enumerate(parsed["records"]):
        words = record["values"]
        harness = StoryCallbackHarness(exe_path, 2, words)
        pair_count = len(words) // 2
        first_samples = []
        for pair_index in range(pair_count):
            sample = harness.step_replay_pair(pair_index)
            if pair_index < 4:
                first_samples.append(sample)
        remaining = struct.unpack("<I", harness.emu.mem_read(harness.context + 0x4C, 4))[0]
        if remaining != 0:
            raise RuntimeError(f"record {record_index}: replay cursor has {remaining} words left")
        records.append({"record": record_index, "word_count": len(words),
                        "story_callback_invocations": pair_count,
                        "decoder_calls": pair_count,
                        "input_setter_calls": pair_count * len(FLAG_MAP),
                        "cursor_remaining": remaining,
                        "first_samples": first_samples})
    total = sum(record["story_callback_invocations"] for record in records)
    return {
        "schema": 1,
        "exe_sha256": EXE_SHA256,
        "replay_sha256": replay_sha,
        "method_va": f"0x{STORY_UPDATE:08x}",
        "decoder_va": f"0x{DECODER:08x}",
        "input_global_va": f"0x{REPLAY_INPUT_GLOBAL:08x}",
        "records": records,
        "total_story_callback_invocations": total,
        "checks": {"one_story_callback_consumes_each_word_pair": True,
                   "original_decoder_updates_both_channel_masks": True,
                   "primary_button_flags_match_original_setter": True,
                   "all_record_words_consumed": True},
        "scope": ("Executes the original Story callback and original decoder on every word pair of the pinned Sanae replay. "
                  "System input-source selection is configured as f0=3 by the harness; this validates per-invocation consumption, "
                  "not that the live menu configures f0=3, replay-menu reachability, or invocations per rendered frame."),
    }
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--replay", type=Path, help="also execute Story callback/decoder over the pinned Sanae replay")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze(args.exe)
    if args.replay:
        report["real_replay_execution"] = analyze_replay(args.exe, args.replay)
    result = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
