#!/usr/bin/env python3
"""Bounded decoder for the record layout read by TH123 PE 2009 VA 0x42cd60.

This reports serialized fields without assigning gameplay semantics to them.
The executable build/hash check is handled by x86_replay_compatibility_probe.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import struct


MAX_RECORDS = 32
MAX_U16_VALUES = 1_000_000


class ReplayFormatError(ValueError):
    """The file is truncated, inconsistent, or exceeds safe parser bounds."""


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def take(self, size: int, label: str) -> bytes:
        if size < 0 or size > len(self.data) - self.offset:
            raise ReplayFormatError(
                f"truncated {label} at 0x{self.offset:x}: need {size}, "
                f"have {len(self.data) - self.offset}"
            )
        start = self.offset
        self.offset += size
        return self.data[start:self.offset]

    def u8(self, label: str) -> int:
        return self.take(1, label)[0]

    def u32(self, label: str) -> int:
        return struct.unpack("<I", self.take(4, label))[0]

    def u16_vector(self, count: int, label: str) -> list[int]:
        available = (len(self.data) - self.offset) // 2
        if count > MAX_U16_VALUES or count > available:
            raise ReplayFormatError(
                f"invalid {label} count {count} at 0x{self.offset:x}; "
                f"maximum from remaining input is {min(MAX_U16_VALUES, available)}"
            )
        raw = self.take(count * 2, label)
        return list(struct.unpack(f"<{count}H", raw)) if count else []


@dataclass
class Channel:
    character_id: int
    reserved: int
    values: list[int]
    flags: list[int]


@dataclass
class ReplayRecord:
    offset: int
    channels: list[Channel]
    trailer_bytes: list[int]
    trailer_word: int
    values: list[int]
    end_offset: int


def parse_replay(data: bytes) -> dict[str, object]:
    """Decode the exact field/read order observed in PE 2009's 0x42cd60."""
    reader = Reader(data)
    if len(data) < 14:
        raise ReplayFormatError("file is shorter than the 14-byte loader header")

    version = reader.u32("version")
    extended = reader.take(10, "extended header")
    # 0x42e030 uses the signed byte at extended[7] as the loop bound and
    # reserves that many in-memory 0x50-byte records.
    record_count = struct.unpack("b", extended[7:8])[0]
    if not 1 <= record_count <= MAX_RECORDS:
        raise ReplayFormatError(f"unsupported signed record count: {record_count}")

    records: list[ReplayRecord] = []
    for record_index in range(record_count):
        start = reader.offset
        channels: list[Channel] = []
        for channel_index in range(2):
            character_id = reader.u8(f"record {record_index} channel {channel_index} character id")
            reserved = reader.u8(f"record {record_index} channel {channel_index} reserved")
            count = reader.u32(f"record {record_index} channel {channel_index} count")
            values = reader.u16_vector(count, f"record {record_index} channel {channel_index} values")
            # Three individual byte reads, written to non-contiguous fields
            # by the original decoder.
            flags = [reader.u8(f"record {record_index} channel {channel_index} flag") for _ in range(3)]
            channels.append(Channel(character_id, reserved, values, flags))

        trailer_bytes = [reader.u8(f"record {record_index} trailer byte") for _ in range(3)]
        trailer_word = reader.u32(f"record {record_index} trailer dword")
        count = reader.u32(f"record {record_index} final vector count")
        values = reader.u16_vector(count, f"record {record_index} final vector")
        records.append(ReplayRecord(start, channels, trailer_bytes, trailer_word,
                                    values, reader.offset))

    if reader.offset != len(data):
        raise ReplayFormatError(
            f"loader schema consumed {reader.offset} of {len(data)} bytes; "
            f"{len(data) - reader.offset} trailing bytes remain"
        )

    return {
        "schema": 2,
        "decoder": {"pe_profile": "provided-original-2009", "va": "0x42cd60",
                    "record_stride_memory": "0x50", "endianness": "little"},
        "file": {"size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                 "version": hex(version), "extended_header_hex": extended.hex(" "),
                 "record_count": record_count,
                 "record_count_minus_one": (record_count - 1) & 0xff},
        "records": [asdict(record) for record in records],
        "consumed_bytes": reader.offset,
        "trailing_bytes": 0,
        "semantics": (
            "The first byte of each channel is consumed as a character selection ID; "
            "the final uint16 vector is consumed as replay input words. In the original "
            "decoder, slot 0 maps six high bits and slot 1 uses only the low 10 bits when "
            "both source flags are active. Natural source flags and per-frame timing "
            "remain unverified."
        ),
    }


def summarize(parsed: dict[str, object]) -> dict[str, object]:
    """Return a compact, reviewable summary without expanding packed vectors."""
    records = parsed["records"]
    summary_records = []
    for index, record in enumerate(records):
        channels = []
        for channel in record["channels"]:
            values = channel["values"]
            channels.append({
                "character_id": channel["character_id"],
                "reserved": channel["reserved"],
                "value_count": len(values),
                "first_values": values[:8],
                "last_values": values[-4:],
                "flags": channel["flags"],
            })
        values = record["values"]
        summary_records.append({
            "index": index,
            "offset": f"0x{record['offset']:x}",
            "end_offset": f"0x{record['end_offset']:x}",
            "size": record["end_offset"] - record["offset"],
            "channels": channels,
            "trailer_bytes": record["trailer_bytes"],
            "trailer_word": f"0x{record['trailer_word']:08x}",
            "value_count": len(values),
            "input_word_decode_f0_3_assumption": [
                {"slot": index % 2, **decode_input_word(value, slot=index % 2)}
                for index, value in enumerate(values[:16])
            ],
            "first_values": values[:12],
            "last_values": values[-8:],
            "monotonic_nondecreasing": all(a <= b for a, b in zip(values, values[1:])),
        })
    return {key: value for key, value in parsed.items() if key != "records"} | {"records": summary_records}


def decode_input_word(value: int, slot: int = 0) -> dict[str, object]:
    """Decode a stream word for slot 0 or slot 1 as observed in PE 2009."""
    if not 0 <= value <= 0xFFFF:
        raise ValueError("replay input word must be an unsigned 16-bit value")
    if slot not in (0, 1):
        raise ValueError("replay input slot must be 0 or 1")
    mapped_bits = ((0x8000, 0x3B), (0x4000, 0x3C), (0x2000, 0x3D),
                   (0x1000, 0x3F), (0x0800, 0x40), (0x0400, 0x41))
    return {
        "raw": value,
        "button_mask": value & 0x03FF,
        "mapped_input_ids": ([input_id for bit, input_id in mapped_bits if value & bit]
                             if slot == 0 else []),
    }
