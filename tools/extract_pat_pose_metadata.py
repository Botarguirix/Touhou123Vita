#!/usr/bin/env python3
"""Read pose offsets from a PAT inside the user's local Touhou DAT archives."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


class MT19937:
    def __init__(self, seed: int):
        self.words = [0] * 624
        self.words[0] = seed & 0xFFFFFFFF
        for i in range(1, 624):
            prev = self.words[i - 1]
            self.words[i] = (1812433253 * (prev ^ (prev >> 30)) + i) & 0xFFFFFFFF
        self.index = 624

    def next(self) -> int:
        if self.index == 624:
            for i in range(624):
                value = (self.words[i] & 0x80000000) | (self.words[(i + 1) % 624] & 0x7FFFFFFF)
                self.words[i] = (
                    self.words[(i + 397) % 624] ^ (value >> 1) ^ (0x9908B0DF if value & 1 else 0)
                ) & 0xFFFFFFFF
            self.index = 0
        value = self.words[self.index]
        self.index += 1
        value ^= value >> 11
        value ^= (value << 7) & 0x9D2C5680
        value ^= (value << 15) & 0xEFC60000
        return (value ^ (value >> 18)) & 0xFFFFFFFF


def entries_from_dat(path: Path) -> dict[str, tuple[int, int]]:
    with path.open("rb") as stream:
        header = stream.read(6)
        if len(header) != 6:
            raise ValueError(f"truncated DAT header: {path}")
        count, table_size = struct.unpack("<HI", header)
        if not count or table_size < count * 9 or table_size > 16 * 1024 * 1024:
            raise ValueError(f"invalid DAT table header: {path}")
        table = bytearray(stream.read(table_size))
        if len(table) != table_size:
            raise ValueError(f"truncated DAT table: {path}")
        rng = MT19937(table_size + 6)
        a, b = 0xC5, 0x83
        for i in range(table_size):
            table[i] ^= (rng.next() ^ a) & 0xFF
            a = (a + b) & 0xFF
            b = (b + 0x53) & 0xFF

        result: dict[str, tuple[int, int]] = {}
        cursor = 0
        for _ in range(count):
            if cursor + 9 > table_size:
                raise ValueError(f"invalid DAT entry table: {path}")
            offset, size, name_size = struct.unpack_from("<IIB", table, cursor)
            cursor += 9
            if not name_size or cursor + name_size > table_size:
                raise ValueError(f"invalid DAT entry name: {path}")
            name = bytes(table[cursor:cursor + name_size]).decode("cp932")
            cursor += name_size
            result[name.casefold()] = (offset, size)
        return result


def read_pat(dat_path: Path, name: str) -> tuple[bytes, str] | None:
    entry = entries_from_dat(dat_path).get(name.casefold())
    if entry is None:
        return None
    offset, size = entry
    with dat_path.open("rb") as stream:
        stream.seek(offset)
        pat = bytearray(stream.read(size))
    if len(pat) != size:
        raise ValueError(f"truncated PAT payload in {dat_path}")
    key = ((offset >> 1) | 0x23) & 0xFF
    for i in range(size):
        pat[i] ^= key
    return bytes(pat), hashlib.sha256(pat).hexdigest()


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def take(self, size: int) -> bytes:
        if size < 0 or size > len(self.data) - self.pos:
            raise ValueError(f"truncated PAT at byte 0x{self.pos:x}")
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def u8(self) -> int:
        return self.take(1)[0]

    def u16(self) -> int:
        return struct.unpack("<H", self.take(2))[0]

    def i32(self) -> int:
        return struct.unpack("<i", self.take(4))[0]

    def skip_boxes(self, extra: bool) -> None:
        count = self.u8()
        if count > 16:
            raise ValueError(f"PAT box count exceeds runtime limit at 0x{self.pos - 1:x}")
        for _ in range(count):
            self.take(16)
            if extra and self.u8():
                self.take(16)


def pose_metadata(pat: bytes, action_id: int, sequence_id: int) -> tuple[list[str], list[dict[str, object]]]:
    reader = Reader(pat)
    if reader.u8() != 5:
        raise ValueError("unsupported PAT version")
    image_count = reader.u16()
    if not image_count or image_count > 8192:
        raise ValueError("invalid PAT image count")
    images = [reader.take(128).split(b"\0", 1)[0].decode("cp932") for _ in range(image_count)]
    record_limit = struct.unpack("<I", reader.take(4))[0]
    if not record_limit or record_limit > 16384:
        raise ValueError("invalid PAT record count")

    found: list[dict[str, object]] = []
    action, sequence = -1, 0
    while reader.pos < len(pat):
        record = reader.i32()
        if record == -1:
            reader.take(8)  # alias action and target
            continue
        if record == -2:
            if action < 0:
                raise ValueError("PAT sequence marker before action")
            sequence += 1
        else:
            if record < 0:
                raise ValueError(f"unknown PAT record {record}")
            action, sequence = record, 0
        reader.take(4)  # move lock and action lock
        reader.u8()  # loop mode
        frame_count = struct.unpack("<I", reader.take(4))[0]
        if not frame_count or frame_count > 4096:
            raise ValueError(f"invalid frame count for action {action}/{sequence}")
        for frame in range(frame_count):
            raw = reader.take(19)
            image = struct.unpack_from("<H", raw)[0]
            tx, ty = struct.unpack_from("<2h", raw, 4)
            width, height = struct.unpack_from("<2h", raw, 8)
            ox, oy = struct.unpack_from("<2h", raw, 12)
            duration = struct.unpack_from("<H", raw, 16)[0]
            flags = raw[18]
            if image >= len(images) or flags > 2:
                raise ValueError(f"invalid pose image/flags in action {action}/{sequence}/{frame}")
            special_data = reader.take(16) if flags == 2 else b""
            reader.take(49)  # traits, explicit flags and attack flags
            reader.skip_boxes(False)
            reader.skip_boxes(False)
            reader.skip_boxes(True)
            reader.take(30)  # effect payload retained by the C decoder
            if action == action_id and sequence == sequence_id:
                found.append({
                    "frame": frame, "image": images[image], "tx": tx, "ty": ty,
                    "width": width, "height": height, "ox": ox, "oy": oy,
                    "duration": duration, "flags": flags,
                    "special_data": special_data.hex(),
                })
    return images, found


def action_sequence_metadata(pat: bytes, action_id: int | None, *,
                             effective: bool = False) -> list[dict[str, object]]:
    """Return PAT records, optionally applying the runtime's action replacement rule."""
    reader = Reader(pat)
    if reader.u8() != 5:
        raise ValueError("unsupported PAT version")
    image_count = reader.u16()
    if not image_count or image_count > 8192:
        raise ValueError("invalid PAT image count")
    images = [reader.take(128).split(b"\0", 1)[0].decode("cp932") for _ in range(image_count)]
    record_limit = struct.unpack("<I", reader.take(4))[0]
    if not record_limit or record_limit > 16384:
        raise ValueError("invalid PAT record count")

    result: list[dict[str, object]] = []
    action, sequence = -1, 0
    while reader.pos < len(pat):
        record = reader.i32()
        if record == -1:
            reader.take(8)
            continue
        if record == -2:
            if action < 0:
                raise ValueError("PAT sequence marker before action")
            sequence += 1
        else:
            if record < 0:
                raise ValueError(f"unknown PAT record {record}")
            action, sequence = record, 0
            # The runtime decoder discards earlier records for a redefined
            # action. Raw inventory remains the default; execution probes can
            # request the effective view to mirror t123_pattern_decode.
            if effective:
                if action_id is None:
                    result = [row for row in result if row.get("action") != action]
                elif action_id == action:
                    result.clear()
        reader.take(4)  # move lock and action lock
        loop_mode = reader.u8()
        frame_count = struct.unpack("<I", reader.take(4))[0]
        if not frame_count or frame_count > 4096:
            raise ValueError(f"invalid frame count for action {action}/{sequence}")
        frames = []
        for frame in range(frame_count):
            raw = reader.take(19)
            image = struct.unpack_from("<H", raw)[0]
            tx, ty = struct.unpack_from("<2h", raw, 4)
            width, height = struct.unpack_from("<2h", raw, 8)
            ox, oy = struct.unpack_from("<2h", raw, 12)
            duration = struct.unpack_from("<H", raw, 16)[0]
            flags = raw[18]
            if image >= len(images) or flags > 2:
                raise ValueError(f"invalid pose image/flags in action {action}/{sequence}/{frame}")
            special_data = reader.take(16) if flags == 2 else b""
            traits = reader.take(40)
            damage = struct.unpack_from("<H", traits)[0]
            chip = struct.unpack_from("<H", traits, 4)[0]
            hit_stop = struct.unpack_from("<H", traits, 14)[0]
            enemy_stun = struct.unpack_from("<H", traits, 16)[0]
            block_stun = struct.unpack_from("<H", traits, 20)[0]
            reader.take(1)  # reserved/unknown frame byte
            frame_flags = struct.unpack("<I", reader.take(4))[0]
            attack_flags = struct.unpack("<I", reader.take(4))[0]

            def read_boxes(extra: bool) -> list[list[int]]:
                count = reader.u8()
                if count > 16:
                    raise ValueError(f"PAT box count exceeds runtime limit at 0x{reader.pos - 1:x}")
                boxes = []
                for _ in range(count):
                    boxes.append([reader.i32(), reader.i32(), reader.i32(), reader.i32()])
                    if extra and reader.u8():
                        reader.take(16)
                return boxes

            collision_boxes = read_boxes(False)
            hurt_boxes = read_boxes(False)
            attack_boxes = read_boxes(True)
            reader.take(30)
            frames.append({"frame": frame, "image": images[image], "duration": duration,
                           "tx": tx, "ty": ty, "width": width, "height": height,
                           "ox": ox, "oy": oy, "flags": flags,
                           "special_data": special_data.hex(),
                           # Preserve the entire original block; x86 response
                           # code also consumes combat fields not named yet.
                           "combat_traits": list(traits),
                           "damage": damage, "chip": chip, "hit_stop": hit_stop,
                           "enemy_stun": enemy_stun,
                           "block_stun": block_stun, "frame_flags": frame_flags,
                           "attack_flags": attack_flags, "collision_boxes": collision_boxes,
                           "hurt_boxes": hurt_boxes, "attack_boxes": attack_boxes})
        if action_id is None or action == action_id:
            row: dict[str, object] = {"sequence": sequence, "loop_mode": loop_mode,
                                      "frames": frames}
            if action_id is None:
                row["action"] = action
            result.append(row)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dat_dir", type=Path, nargs="?", default=Path("original"))
    parser.add_argument("--character", default="suwako")
    parser.add_argument("--action", type=int, default=808)
    parser.add_argument("--sequence", type=int, default=0)
    args = parser.parse_args()
    name = f"data/character/{args.character}/{args.character}.pat"
    output = []
    for archive in ("th123a.dat", "th123b.dat", "th123c.dat"):
        path = args.dat_dir / archive
        if not path.is_file():
            continue
        payload = read_pat(path, name)
        if payload is None:
            output.append({"archive": archive, "present": False})
            continue
        pat, digest = payload
        _, poses = pose_metadata(pat, args.action, args.sequence)
        output.append({"archive": archive, "present": True, "pat_sha256": digest, "poses": poses})
    if not output:
        raise SystemExit(f"No Touhou 12.3 DAT archives found in {args.dat_dir}")
    effective = next((entry for entry in reversed(output) if entry.get("present")), None)
    print(json.dumps({"resource": name, "action": args.action, "sequence": args.sequence,
                      "archive_lookup_priority": ["th123c.dat", "th123b.dat", "th123a.dat"],
                      "effective_archive": effective["archive"] if effective else None,
                      "effective_poses": effective["poses"] if effective else [],
                      "archives": output}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
