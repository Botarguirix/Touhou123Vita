import struct
import unittest

from tools.extract_pat_pose_metadata import action_sequence_metadata


def make_pat(records):
    image_name = b"frame.cv2".ljust(128, b"\0")
    data = bytearray(struct.pack("<BH", 5, 1) + image_name + struct.pack("<I", 16))
    for action, sequence_count, marker in records:
        if marker == "action":
            sequence = 0
            data += struct.pack("<iHHBI", action, 0, 0, 0, 1)
        else:
            sequence += 1
            data += struct.pack("<iHHBI", -2, 0, 0, 0, 1)
        # The marker distinguishes definitions in this fixture through damage.
        traits = bytearray(40)
        struct.pack_into("<H", traits, 0, sequence_count)
        data += struct.pack("<H2x6hHB", 0, 0, 0, 0, 0, 0, 0, 1, 0)
        data += traits + bytes(1 + 4 + 4 + 3 + 30)
    return bytes(data)


class ExtractPatPoseMetadataTests(unittest.TestCase):
    def test_later_action_definition_replaces_shadowed_sequences(self):
        pat = make_pat([
            (418, 100, "action"),
            (418, 101, "sequence"),
            (419, 200, "action"),
            (418, 300, "action"),
            (418, 301, "sequence"),
        ])

        raw_all_actions = action_sequence_metadata(pat, None)
        all_actions = action_sequence_metadata(pat, None, effective=True)
        raw_action_418 = action_sequence_metadata(pat, 418)
        action_418 = action_sequence_metadata(pat, 418, effective=True)

        self.assertEqual(len(raw_all_actions), 5)
        self.assertEqual(len(raw_action_418), 4)
        self.assertEqual([(row["action"], row["sequence"], row["frames"][0]["damage"])
                          for row in all_actions],
                         [(419, 0, 200), (418, 0, 300), (418, 1, 301)])
        self.assertEqual([row["frames"][0]["damage"] for row in action_418], [300, 301])


if __name__ == "__main__":
    unittest.main()
