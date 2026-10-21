from __future__ import annotations

import struct
import unittest

from tools.replay_layout import (
    ReplayFormatError,
    decode_input_word,
    parse_replay,
    summarize,
)


def sample_replay(record_count: int = 1) -> bytes:
    extended = bytearray(10)
    extended[7] = record_count
    output = bytearray(struct.pack("<I", 0x100C8) + extended)
    for record in range(record_count):
        for channel in range(2):
            output += bytes((15 + channel, record))
            values = [100 + record, 200 + record]
            output += struct.pack("<I", len(values))
            output += struct.pack("<2H", *values)
            output += bytes((1, 2, 3))
        output += bytes((4, 5, 6))
        output += struct.pack("<I", 0xDA9D606A)
        values = [10 + record, 20 + record, 30 + record]
        output += struct.pack("<I", len(values))
        output += struct.pack("<3H", *values)
    return bytes(output)


class ReplayLayoutTests(unittest.TestCase):
    def test_decodes_loader_header_and_two_channel_record(self):
        parsed = parse_replay(sample_replay())
        self.assertEqual(parsed["file"]["version"], "0x100c8")
        self.assertEqual(parsed["file"]["record_count"], 1)
        self.assertEqual(parsed["consumed_bytes"], len(sample_replay()))
        record = parsed["records"][0]
        self.assertEqual([channel["character_id"] for channel in record["channels"]], [15, 16])
        self.assertEqual(record["channels"][1]["values"], [100, 200])
        self.assertEqual(record["values"], [10, 20, 30])
        self.assertEqual(record["trailer_word"], 0xDA9D606A)

    def test_summary_reports_record_boundaries_without_expanding_vectors(self):
        parsed = parse_replay(sample_replay(2))
        parsed["records"][0]["values"] = [0xA155, 0xA955, 0x8155]
        summary = summarize(parsed)
        self.assertEqual(summary["schema"], 2)
        self.assertEqual(summary["file"]["record_count"], 2)
        self.assertEqual(len(summary["records"]), 2)
        self.assertEqual(summary["records"][0]["offset"], "0xe")
        self.assertTrue(summary["records"][1]["monotonic_nondecreasing"])
        decoded = summary["records"][0]["input_word_decode_f0_3_assumption"]
        self.assertEqual([word["slot"] for word in decoded[:3]], [0, 1, 0])
        self.assertEqual(decoded[0]["mapped_input_ids"], [0x3B, 0x3D])
        self.assertEqual(decoded[1]["mapped_input_ids"], [])
        self.assertEqual(decoded[2]["mapped_input_ids"], [0x3B])

    def test_decodes_replay_word_without_inventing_button_names(self):
        decoded = decode_input_word(0x8000 | 0x2000 | 0x0155)
        self.assertEqual(decoded, {
            "raw": 0xA155,
            "button_mask": 0x155,
            "mapped_input_ids": [0x3B, 0x3D],
        })

    def test_secondary_input_slot_uses_only_low_ten_bits(self):
        decoded = decode_input_word(0xA155, slot=1)
        self.assertEqual(decoded, {
            "raw": 0xA155,
            "button_mask": 0x155,
            "mapped_input_ids": [],
        })

    def test_rejects_unknown_input_slot(self):
        with self.assertRaisesRegex(ValueError, "slot must be 0 or 1"):
            decode_input_word(0, slot=2)

    def test_rejects_input_words_outside_u16(self):
        with self.assertRaisesRegex(ValueError, "unsigned 16-bit"):
            decode_input_word(0x10000)

    def test_rejects_truncated_vector(self):
        data = bytearray(sample_replay())
        # First channel vector count starts at absolute offset 16.
        struct.pack_into("<I", data, 16, 0xFFFFFFFF)
        with self.assertRaisesRegex(ReplayFormatError, "invalid record 0 channel 0 values count"):
            parse_replay(bytes(data))

    def test_rejects_negative_signed_record_count(self):
        data = bytearray(sample_replay())
        data[11] = 0xFF
        with self.assertRaisesRegex(ReplayFormatError, "signed record count"):
            parse_replay(bytes(data))

    def test_rejects_unconsumed_trailing_data(self):
        with self.assertRaisesRegex(ReplayFormatError, "trailing bytes remain"):
            parse_replay(sample_replay() + b"\x00")

    def test_rejects_truncated_header(self):
        with self.assertRaisesRegex(ReplayFormatError, "14-byte loader header"):
            parse_replay(b"\0" * 13)


if __name__ == "__main__":
    unittest.main()
