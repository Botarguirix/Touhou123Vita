#!/usr/bin/env python3
"""Run the original 2009 replay-input decoder over a user-supplied .rep stream.

This is a bounded Unicorn oracle for VA 0x42a410. It validates word extraction
and button-flag mapping, but does not simulate game frames or the outer player
update loop.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))

import pefile  # noqa: E402
from replay_layout import parse_replay  # noqa: E402
from unicorn import UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32, Uc  # noqa: E402
from unicorn.x86_const import (  # noqa: E402
    UC_X86_REG_ECX,
    UC_X86_REG_EIP,
    UC_X86_REG_ESP,
)

ORIGINAL_2009_SHA256 = "24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3"
DECODE_INPUT_VA = 0x0042A410
LOCK_VAS = {0x0040AB50, 0x0040AB60}
SET_INPUT_VA = 0x0043CC80
FLAG_MAP = ((0x8000, 0x3B), (0x4000, 0x3C), (0x2000, 0x3D),
            (0x1000, 0x3F), (0x0800, 0x40), (0x0400, 0x41))


def align_page(size: int) -> int:
    return (size + 0xFFF) & ~0xFFF


def emulate_record(exe: Path, words: list[int]) -> dict[str, object]:
    if len(words) % 2:
        raise ValueError("the paired-channel oracle requires an even word count")

    raw_exe = exe.read_bytes()
    digest = hashlib.sha256(raw_exe).hexdigest()
    if digest != ORIGINAL_2009_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {digest}")
    pe = pefile.PE(data=raw_exe)
    base = pe.OPTIONAL_HEADER.ImageBase
    image_size = align_page(pe.OPTIONAL_HEADER.SizeOfImage)

    obj, ctx, table, data = 0x900000, 0x910000, 0x920000, 0x930000
    stack, stop = 0x950000, 0x960000
    block_count = max(1, (len(words) + 7) // 8)
    emu = Uc(UC_ARCH_X86, UC_MODE_32)
    emu.mem_map(base, image_size)
    emu.mem_write(base, raw_exe[:pe.OPTIONAL_HEADER.SizeOfHeaders])
    for section in pe.sections:
        section_data = section.get_data()
        if section_data:
            emu.mem_write(base + section.VirtualAddress, section_data)

    emu.mem_map(obj, 0x1000)
    emu.mem_map(ctx, 0x1000)
    emu.mem_map(table, align_page(block_count * 4))
    emu.mem_map(data, align_page(max(16, block_count * 16)))
    emu.mem_map(stack, 0x10000)
    emu.mem_map(stop, 0x1000)

    emu.mem_write(data, struct.pack(f"<{len(words)}H", *words) if words else b"")
    emu.mem_write(table, struct.pack(f"<{block_count}I",
                                     *(data + 16 * i for i in range(block_count))))

    def put_u32(address: int, value: int) -> None:
        emu.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    # Two active input channels, with a segmented uint16 vector at ctx + 0x3c.
    put_u32(obj + 0xF0, 3)
    put_u32(obj + 0x104, ctx)
    put_u32(ctx + 0x40, table)
    put_u32(ctx + 0x44, block_count)
    put_u32(ctx + 0x48, 0)
    put_u32(ctx + 0x4C, len(words))

    callback_events: list[tuple[int, int]] = []

    def hook(machine: Uc, address: int, _size: int, _user_data: object) -> None:
        if address in LOCK_VAS:
            esp = machine.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == SET_INPUT_VA:
            esp = machine.reg_read(UC_X86_REG_ESP)
            ret, input_id, pressed = struct.unpack("<III", machine.mem_read(esp, 12))
            # The original uses SETA on the low byte, leaving upper EAX bits
            # unspecified before pushing the C boolean argument.
            callback_events.append((input_id, pressed & 0xFF))
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)

    emu.hook_add(UC_HOOK_CODE, hook)
    initial_sp = stack + 0x8000
    emu.mem_write(initial_sp, struct.pack("<I", stop))
    for pair_index in range(len(words) // 2):
        emu.reg_write(UC_X86_REG_ESP, initial_sp)
        emu.reg_write(UC_X86_REG_ECX, obj)
        emu.emu_start(DECODE_INPUT_VA, stop, count=10000)
        if emu.reg_read(UC_X86_REG_EIP) != stop:
            raise RuntimeError("original decoder did not return to the harness")
        expected_first = words[pair_index * 2] & 0x03FF
        expected_second = words[pair_index * 2 + 1] & 0x03FF
        actual_first = struct.unpack("<H", emu.mem_read(obj + 0x68, 2))[0]
        actual_second = struct.unpack("<H", emu.mem_read(obj + 0xD0, 2))[0]
        if (actual_first, actual_second) != (expected_first, expected_second):
            raise RuntimeError(f"x86 mask mismatch at input pair {pair_index}")

    expected_events: list[tuple[int, int]] = []
    expected_first_masks: list[int] = []
    expected_second_masks: list[int] = []
    for first, second in zip(words[::2], words[1::2]):
        expected_first_masks.append(first & 0x03FF)
        expected_second_masks.append(second & 0x03FF)
        expected_events.extend((input_id, int(bool(first & bit)))
                               for bit, input_id in FLAG_MAP)

    # The original decoder leaves the last pair's masks in these object fields.
    actual_first = struct.unpack("<H", emu.mem_read(obj + 0x68, 2))[0]
    actual_second = struct.unpack("<H", emu.mem_read(obj + 0xD0, 2))[0]
    remaining = struct.unpack("<I", emu.mem_read(ctx + 0x4C, 4))[0]
    passed = (callback_events == expected_events and
              actual_first == (expected_first_masks[-1] if words else 0) and
              actual_second == (expected_second_masks[-1] if words else 0) and
              remaining == 0)
    return {
        "words": len(words),
        "paired_updates": len(words) // 2,
        "decoded_input_callback_count": len(callback_events),
        "cursor_remaining": remaining,
        "last_masks": {"channel0": actual_first, "channel1": actual_second},
        "oracle_matches_static_mapping": passed,
    }


def analyze(exe: Path, replay_path: Path, record_index: int | None = None) -> dict[str, object]:
    parsed = parse_replay(replay_path.read_bytes())
    version = parsed["file"]["version"]
    if version not in ("0xc8", "0x100c8"):
        raise ValueError(f"unsupported replay version: {version}")
    records = parsed["records"]
    indexes = range(len(records)) if record_index is None else (record_index,)
    output = []
    for index in indexes:
        if not 0 <= index < len(records):
            raise ValueError(f"record index {index} is out of range")
        record = records[index]
        result = emulate_record(exe, record["values"])
        result.update({"record": index,
                       "character_ids": [channel["character_id"]
                                         for channel in record["channels"]],
                       "channel_value_counts": [len(channel["values"])
                                                for channel in record["channels"]]})
        if not result["oracle_matches_static_mapping"]:
            raise RuntimeError(f"x86 oracle mismatch in replay record {index}")
        output.append(result)
    return {
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "replay_sha256": parsed["file"]["sha256"],
        "replay_version": version,
        "oracle_function": hex(DECODE_INPUT_VA),
        "records": output,
        "scope": ("Executes the original decoder once per pair of uint16 words with both "
                  "input-channel flags enabled. This validates decoding/cursor consumption, "
                  "not game-loop timing or frame-by-frame gameplay parity."),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path, help="user-supplied TH123 .rep file")
    parser.add_argument("--exe", type=Path, required=True,
                        help="the compatible 2009 TH123 executable")
    parser.add_argument("--record", type=int, help="record index (default: all)")
    parser.add_argument("--output", type=Path, help="optional JSON report")
    args = parser.parse_args()
    result = json.dumps(analyze(args.exe, args.replay, args.record), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
