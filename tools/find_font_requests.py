#!/usr/bin/env python3
"""Recover GDI font requests and execute their bitmap/DBCS adapters (T5).

Only metadata is written to the report. The PE and DAT resources remain local.
The Unicorn probes stub GDI and allocation, not the instructions under test;
they establish the ABI/conversion contract, not Windows font rasterizer parity.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
sys.path.insert(0, str(ROOT / "local/python-deps"))
sys.path.insert(0, str(ROOT / "tools"))
import pefile  # noqa: E402
from capstone import Cs, CS_ARCH_X86, CS_MODE_32  # noqa: E402
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE  # noqa: E402
from unicorn.x86_const import (  # noqa: E402
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
    UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP,
    UC_X86_REG_EIP,
)
from extract_pat_pose_metadata import entries_from_dat  # noqa: E402

BASE = 0x400000
FONT = 0x02000000
OUTPUT = 0x02010000
ALLOC = 0x02020000
STACK = 0x0300E000
STOP = 0x020FF000
FONT_NAME = 0x858764
CREATE_FONT = 0x411C75
GLYPH_SITES = (0x411E53, 0x411F1A, 0x4120C2, 0x41213B)
REGS = {"eax": UC_X86_REG_EAX, "ebx": UC_X86_REG_EBX,
        "ecx": UC_X86_REG_ECX, "edx": UC_X86_REG_EDX,
        "esi": UC_X86_REG_ESI, "edi": UC_X86_REG_EDI,
        "ebp": UC_X86_REG_EBP, "esp": UC_X86_REG_ESP}
FONT_ARGS = ("height", "width", "escapement", "orientation", "weight",
             "italic", "underline", "strikeout", "charset", "out_precision",
             "clip_precision", "quality", "pitch_and_family", "face_pointer")


def hx(value: int) -> str:
    return f"0x{value:08x}"


def load_pe(path: Path):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"reference SHA256 mismatch: {digest}")
    return pefile.PE(data=raw), digest


def c_string(pe, address: int, limit: int = 1024) -> bytes:
    return pe.get_data(address - BASE, limit).split(b"\0", 1)[0]


class Probe:
    def __init__(self, pe):
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xFFF) & ~0xFFF
        self.uc.mem_map(BASE, size)
        self.uc.mem_write(BASE, pe.get_memory_mapped_image())
        self.uc.mem_map(FONT, 0x100000)
        self.uc.mem_map(0x03000000, 0x10000)
        self.set("esp", STACK)
        self.u32(STACK, STOP)

    def set(self, register: str, value: int):
        self.uc.reg_write(REGS[register], value)

    def get(self, register: str) -> int:
        return self.uc.reg_read(REGS[register])

    def u32(self, address: int, value: int | None = None) -> int:
        if value is not None:
            self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def skip_call(self, address: int, length: int, result: int, cleanup: int = 0):
        # Called before CALL executes; arguments therefore begin at [ESP].
        self.set("eax", result)
        self.set("esp", self.get("esp") + cleanup)
        self.uc.reg_write(UC_X86_REG_EIP, address + length)

    def run(self, start: int, callback, end: int = STOP, count: int = 100000):
        def hook(uc, address, size, unused):
            if address == end:
                uc.emu_stop()
            else:
                callback(self, address, size)
        handle = self.uc.hook_add(UC_HOOK_CODE, hook)
        self.uc.emu_start(start, end + 1, count=count)
        self.uc.hook_del(handle)
        if self.uc.reg_read(UC_X86_REG_EIP) != end:
            raise RuntimeError(f"probe did not reach {hx(end)}")


def description(pe, height=14, weight=300, italic=0) -> bytes:
    data = bytearray(0x128)
    name = c_string(pe, FONT_NAME)
    data[:len(name)] = name
    struct.pack_into("<ii", data, 0x108, height, weight)
    data[0x110] = italic
    struct.pack_into("<I", data, 0x114, 100000)
    return bytes(data)


def create_font_probe(pe, height=14, weight=300, italic=0) -> dict:
    probe = Probe(pe)
    probe.uc.mem_write(FONT + 0xC, description(pe, height, weight, italic))
    probe.set("esi", FONT)
    probe.run(0x411C40, lambda *_: None, CREATE_FONT)
    args = dict(zip(FONT_ARGS, struct.unpack("<14I", probe.uc.mem_read(probe.get("esp"), 56))))
    args["height"] = struct.unpack("<i", struct.pack("<I", args["height"]))[0]
    args["face"] = bytes(probe.uc.mem_read(args["face_pointer"], 256)).split(b"\0")[0].decode("cp932")
    args["face_pointer"] = "SWRFont+0x0c"
    args["callsite"] = hx(CREATE_FONT)
    args["evidence"] = "executed PE setup to the import call; GDI not executed"
    return args


def descriptor_probes(pe) -> list[dict]:
    # Each range begins at an instruction boundary before the local descriptor
    # is initialized. The PE's strcpy_s also executes (valid pointers/capacity);
    # external scene/config state is explicit.
    specs = [
        (0x434CF5, 0x434DE1, {"ebx": 0, "edi": 0}, "profile_layout", "14 - edi (edi=0 in probe)"),
        (0x438532, 0x438611, {"ebx": 0}, "menu", "14"),
        (0x43D7AB, 0x43D883, {"esi": 0}, "scene_local", "14"),
        (0x44406E, 0x444142, {"ebp": 0}, "global_89a4f8", "14"),
        (0x44B986, 0x44BA52, {"ebx": 0, "esi": FONT}, "scene_member", "14"),
        (0x450A82, 0x450B52, {"ebx": 0}, "global_89a4f8_shadow", "14"),
        (0x462925, 0x462990, {"ebx": 0, "esi": FONT, "ebp": FONT + 0x1FC}, "script_default", "24"),
    ]
    rows = []
    for start, end, registers, context, formula in specs:
        probe = Probe(pe)
        for reg, value in registers.items():
            probe.set(reg, value)
        if context == "script_default":
            probe.run(0x462381, lambda *_: None, 0x4623CB)
        probe.run(start, lambda *_: None, end)
        ptr = probe.u32(probe.get("esp"))
        raw = bytes(probe.uc.mem_read(ptr, 0x128))
        rows.append({"callsite": hx(end), "fragment_start": hx(start), "context": context,
                     "face": raw[:256].split(b"\0", 1)[0].decode("cp932"),
                     "height_measured": struct.unpack_from("<i", raw, 0x108)[0],
                     "height_expression": formula,
                     "weight_measured": struct.unpack_from("<i", raw, 0x10C)[0],
                     "weight_seeded": False,
                     "italic": raw[0x110], "confidence": "high for executed fragment; scene state supplied"})
    # The two profile labels shrink according to byte length. Exercise both
    # arithmetic fragments without bypassing their instructions.
    for start, end, threshold in ((0x453C5B, 0x453CD1, 16), (0x453D47, 0x453DBD, 15)):
        for length in (8, 20, 32):
            probe = Probe(pe)
            probe.set("ebx", 0)
            probe.uc.mem_write(STACK + 0x34, description(pe))
            probe.u32(STACK + 0x2C, length)
            probe.run(start, lambda *_: None, end)
            ptr = probe.u32(probe.get("esp"))
            raw = bytes(probe.uc.mem_read(ptr, 0x128))
            rows.append({"callsite": hx(end), "fragment_start": hx(start),
                         "context": "profile_name_shrink", "byte_length": length,
                         "height_measured": struct.unpack_from("<i", raw, 0x108)[0],
                         "height_expression": f"14 - max(trunc((byte_length - {threshold}) / 2), 0)",
                         "weight_measured": struct.unpack_from("<i", raw, 0x10C)[0],
                         "weight_seeded": True, "face_seeded": True,
                         "confidence": "high for arithmetic; descriptor inherited"})
    return rows


def script_font_probe(pe) -> dict:
    probe = Probe(pe)
    probe.set("esi", FONT)
    probe.set("ebx", 0)
    probe.run(0x462381, lambda *_: None, 0x4623CB)
    record = FONT + 0x1000
    probe.uc.mem_write(record + 0xC, b"FixtureFace\0")
    probe.u32(record + 0x20, 0)  # short-string representation
    probe.u32(record + 0x24, 18)
    probe.u32(record + 0x28, 9)
    probe.u32(record + 0x2C, 2)
    probe.set("esi", record)
    probe.set("ebx", FONT)
    probe.run(0x461FDA, lambda *_: None, 0x46202A)
    ptr = probe.u32(probe.get("esp"))
    data = bytes(probe.uc.mem_read(ptr, 0x128))
    return {"callsite": hx(0x46202A), "face": data[:256].split(b"\0", 1)[0].decode("ascii"),
            "height": struct.unpack_from("<i", data, 0x108)[0],
            "weight": struct.unpack_from("<i", data, 0x10C)[0],
            "char_space_x": struct.unpack_from("<i", data, 0x120)[0],
            "char_space_y": struct.unpack_from("<i", data, 0x124)[0],
            "evidence": "executed script constructor field defaults and arbitrary synthetic parsed font record"}


def ruby_font_probe(pe, parent_height: int) -> dict:
    probe = Probe(pe)
    probe.set("esi", FONT)
    probe.uc.mem_write(FONT + 0xC, description(pe, parent_height, 400))
    probe.set("ecx", STACK + 0x64)
    probe.run(0x411680, lambda *_: None, 0x4116C2)
    # The ruby span must be large enough to enter the subsequent layout path.
    probe.u32(FONT + 0x190, 100)
    probe.run(0x41254E, lambda *_: None, 0x4125C3)
    raw = bytes(probe.uc.mem_read(STACK + 0x64, 0x128))
    return {"callsite": hx(0x4126AD), "fragment_end": hx(0x4125C3),
            "parent_height": parent_height, "base_ruby_height": struct.unpack_from("<i", raw, 0x108)[0],
            "weight": struct.unpack_from("<i", raw, 0x10C)[0],
            "evidence": "executed height/face setup; later available-span spacing adjustment not executed"}


def embedded_text_probe(pe) -> dict:
    probe = Probe(pe)
    probe.set("ebx", 0)
    probe.set("esi", FONT)
    probe.run(0x44885D, lambda *_: None, 0x448880)
    args = struct.unpack("<7I", probe.uc.mem_read(probe.get("esp"), 28))
    return {"callsite": hx(0x448880), "text_address": hx(args[1]),
            "font_address": hx(args[2]), "texture_size": list(args[3:5]),
            "text_metadata": encoding_metadata(c_string(pe, args[1])),
            "evidence": "executed argument setup; text pointer points into the PE .rdata, not a DAT allocation"}


def text_texture_probe(pe) -> dict:
    probe = Probe(pe)
    probe.set("ebp", FONT + 0x200)
    probe.set("ebx", 256)
    probe.set("edi", 128)
    probe.u32(FONT + 0x208, OUTPUT)
    probe.u32(0x8A0E30, FONT + 0x800)
    # Begin after the external critical-section call; execute all eight
    # original argument pushes, stopping before D3DXCreateTexture.
    probe.run(0x40943E, lambda *_: None, 0x409453)
    device, width, height, levels, usage, fmt, pool, output = struct.unpack(
        "<8I", probe.uc.mem_read(probe.get("esp"), 32))
    if device != FONT + 0x800 or output != OUTPUT:
        raise RuntimeError("unexpected D3DXCreateTexture output/device arguments")
    return {"callsite": hx(0x409453), "format": fmt,
            "format_name": "D3DFMT_A8R8G8B8" if fmt == 21 else "unknown",
            "width_seeded": width, "height_seeded": height,
            "levels": levels, "usage": usage, "pool": pool,
            "evidence": "executed original allocation argument setup; D3DX/GPU not executed"}


def glyph_bitmap_probe(pe, period: bool = False, gradient: bool = False) -> dict:
    probe = Probe(pe)
    probe.set("esi", FONT)
    probe.set("eax", FONT)
    probe.u32(FONT, 0x1234)  # fake HDC, never dereferenced by the PE
    probe.u32(FONT + 0x13C, 8)  # tmAscent
    probe.u32(FONT + 0x140, OUTPUT)
    probe.u32(FONT + 0x144, OUTPUT)
    probe.u32(FONT + 0x148, 32)
    probe.u32(FONT + 0x14C, 32)
    probe.u32(FONT + 0x150, 32)  # output pitch in pixels
    probe.u32(FONT + 0x168, 0x00123456)
    if gradient:
        probe.u32(FONT + 0x154, FONT + 0x800)
        probe.uc.mem_write(FONT + 0x800, struct.pack("<16I", *([0x00123456] * 16)))
    if period:
        # __usercall: ESI=font, [ESP+4]=center column, [ESP+8]=row.
        probe.u32(STACK + 4, 4)
        probe.u32(STACK + 8, 0)
    else:
        probe.u32(STACK + 4, 0x82A0)  # a two-byte CP932 character, not UTF-16
        probe.u32(STACK + 8, 0)
        probe.u32(STACK + 12, 0)
    # Deliberately 3 pixels wide: tests DWORD padding as well as endpoints.
    samples = bytes([0, 8, 16, 0xEE, 16, 1, 15, 0xEE])
    calls = []
    def callback(p, address, size):
        if address in GLYPH_SITES:
            hdc, char, fmt, metrics, length, buffer, matrix = struct.unpack("<7I", p.uc.mem_read(p.get("esp"), 28))
            mat = struct.unpack("<4i", p.uc.mem_read(matrix, 16))
            calls.append({"callsite": hx(address), "character": char, "format": fmt,
                          "format_name": {5: "GGO_GRAY4_BITMAP"}.get(fmt, "unknown"),
                          "buffer_size": length, "buffer_is_null": buffer == 0,
                          "matrix_address": hx(matrix), "matrix_fixed16_16": list(mat)})
            # GLYPHMETRICS: blackbox 3x2, origin(0,2), advance(4,0).
            p.uc.mem_write(metrics, struct.pack("<IIiihh", 3, 2, 0, 2, 4, 0))
            if buffer:
                if length != len(samples):
                    raise RuntimeError("unexpected bitmap allocation")
                p.uc.mem_write(buffer, samples)
            p.skip_call(address, size, len(samples), 28)
        elif address in (0x411EF6, 0x41211A):
            if p.u32(p.get("esp")) != len(samples):
                raise RuntimeError("unexpected allocation request")
            p.skip_call(address, size, ALLOC)
        elif address in (0x41200F, 0x412220):
            if p.u32(p.get("esp")) != ALLOC:
                raise RuntimeError("unexpected free")
            p.skip_call(address, size, 0)
    probe.run(0x412090 if period else 0x411E20, callback)
    pixels = struct.unpack("<1024I", probe.uc.mem_read(OUTPUT, 4096))
    written = [{"x": i % 32, "y": i // 32, "argb": f"0x{color:08x}"}
               for i, color in enumerate(pixels) if color]
    return {"mode": "period" if period else "glyph", "gradient": gradient,
            "calls": calls, "output_pixels": written,
            "cursor_x": probe.u32(FONT + 0x134),
            "evidence": "executed original metrics/row-stride/coverage-to-ARGB copy with synthetic GDI bitmap"}


def dbcs_probe(pe, data: bytes) -> dict:
    if not data or len(data) > 8 or data.endswith(b"\0"):
        raise ValueError("supply a short nonempty unterminated sample")
    probe = Probe(pe)
    probe.set("esi", FONT)
    probe.set("ebx", FONT + 0x800)
    probe.set("edi", 0)
    probe.set("edx", len(data))
    probe.uc.mem_write(FONT + 0x800, data + b"\0\0\0\0")
    probe.run(0x4129B3, lambda *_: None, 0x4129D9)
    return {"input_hex": data.hex(), "gdi_character": probe.get("eax"),
            "bytes_consumed": probe.get("ecx") & 0xFF}


def decode_cv_text(data: bytes) -> bytes:
    out = bytearray(data)
    a, b = 0x8B, 0x71
    for i in range(len(out)):
        out[i] ^= a
        a = (a + b) & 255
        b = (b - 0x6B) & 255
    return bytes(out)


def encoding_metadata(data: bytes) -> dict:
    result = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    for encoding in ("cp932", "utf-8"):
        try:
            text = data.decode(encoding)
            result[encoding] = {"valid": True, "characters": len(text),
                                "japanese_characters": sum(0x3040 <= ord(c) <= 0x30FF or 0x3400 <= ord(c) <= 0x9FFF for c in text)}
        except UnicodeDecodeError:
            result[encoding] = {"valid": False}
    return result


def dat_text_sources(paths: list[Path]) -> list[dict]:
    rows = []
    for path in sorted(paths, key=lambda p: p.name.casefold()):
        entries = entries_from_dat(path)
        candidates = [(name, offset, size) for name, (offset, size) in sorted(entries.items())
                      if name.endswith((".cv0", ".cv1", ".csv", ".txt"))]
        counts = collections.Counter(Path(name).suffix for name, _, _ in candidates)
        samples = []
        # Decode all text resources, report only hashes/counts (no game text).
        cp932_valid = utf8_valid = japanese = 0
        with path.open("rb") as stream:
            for name, offset, size in candidates:
                if offset < 6 or size > 16 * 1024 * 1024 or offset + size > path.stat().st_size:
                    raise ValueError(f"invalid text resource bounds: {path.name}: {name}")
                stream.seek(offset)
                encrypted = stream.read(size)
                if len(encrypted) != size:
                    raise ValueError("truncated text resource")
                key = ((offset >> 1) | 0x23) & 255
                data = bytes(value ^ key for value in encrypted)
                if name.endswith((".cv0", ".cv1")):
                    data = decode_cv_text(data)
                meta = encoding_metadata(data)
                cp932_valid += meta["cp932"]["valid"]
                utf8_valid += meta["utf-8"]["valid"]
                japanese += meta["cp932"].get("japanese_characters", 0)
                if len(samples) < 4 and meta["cp932"].get("japanese_characters", 0):
                    samples.append({"resource": name, **meta})
        rows.append({"archive": path.name, "archive_bytes": path.stat().st_size,
                     "text_resource_counts": dict(sorted(counts.items())), "decoded_text_files": len(candidates),
                     "cp932_valid_files": cp932_valid, "utf8_valid_files": utf8_valid,
                     "japanese_characters_cp932": japanese, "samples": samples})
    return rows


def scan(pe) -> dict:
    imports = {i.address: i.name.decode("ascii") for e in pe.DIRECTORY_ENTRY_IMPORT
               for i in e.imports if i.name}
    names = {a: n for a, n in imports.items() if n in ("CreateFontA", "GetGlyphOutlineA", "GetTextMetricsA")}
    sites = collections.defaultdict(list)
    setters, text_calls, face_refs, resource_refs = [], [], [], []
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    for sec in pe.sections:
        if not sec.Characteristics & 0x20000000:
            continue
        for address, _, mnemonic, operands in md.disasm_lite(sec.get_data()[:sec.Misc_VirtualSize], BASE + sec.VirtualAddress):
            if mnemonic in ("call", "jmp", "mov"):
                for target, name in names.items():
                    if re.search(rf"\b{target:x}\b", operands.replace("0x", "")):
                        sites[name].append({"address": hx(address), "kind": mnemonic})
            if mnemonic == "call" and operands == "0x411840":
                setters.append(hx(address))
            if mnemonic == "call" and operands == "0x4050a0":
                text_calls.append(hx(address))
            if hex(FONT_NAME) in operands:
                face_refs.append(hx(address))
    for sec in pe.sections:
        for match in re.finditer(rb"[\x20-\x7e]{8,}", sec.get_data()):
            value = match.group().decode("ascii")
            if re.search(r"(?:data[/_].*\.(?:csv|cv0|cv1|txt))", value, re.I):
                resource_refs.append({"address": hx(BASE + sec.VirtualAddress + match.start()), "path": value})
    return {"imports": {n: hx(a) for a, n in sorted(names.items())},
            "import_sites": dict(sorted(sites.items())), "set_indirect_calls": setters,
            "create_text_texture_calls": text_calls, "default_face_refs": face_refs,
            "text_resource_path_refs": resource_refs,
            "scan_scope": "linear executable sections including skipdata; candidates cross-checked against known font functions"}


def analyze(exe: Path, dat_paths: list[Path] | None = None) -> dict:
    pe, digest = load_pe(exe)
    return {"schema": 1, "sha256": digest, "static": scan(pe),
            "default_face": {"address": hx(FONT_NAME), "encoding": "cp932",
                             "name": c_string(pe, FONT_NAME).decode("cp932")},
            "create_font_requests": [create_font_probe(pe), create_font_probe(pe, 24, 400),
                                     create_font_probe(pe, -17, 700, 1)],
            "descriptor_probes": descriptor_probes(pe),
            "script_font_probe": script_font_probe(pe),
            "ruby_font_probes": [ruby_font_probe(pe, height) for height in (14, 24, 17)],
            "embedded_text_probe": embedded_text_probe(pe),
            "text_texture_probe": text_texture_probe(pe),
            "glyph_bitmap_probes": [glyph_bitmap_probe(pe, period, gradient)
                                     for period in (False, True) for gradient in (False, True)],
            "dbcs_probes": [dbcs_probe(pe, b"A"), dbcs_probe(pe, bytes.fromhex("82a0")),
                            dbcs_probe(pe, bytes.fromhex("b1"))],
            "text_sources": dat_text_sources(dat_paths or []),
            "limitations": ["Windows GDI rasterization is stubbed; no visual or font-metric parity claimed",
                            "descriptor fields can be changed by script; sizes are not a finite global list",
                            "CP932 decode validity is corroboration, not unique identification without the PE DBCS path",
                            "source paths and metadata only; no proprietary text or bitmap payload in report"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--dat", type=Path, action="append", help="local DAT to inspect; repeat (default original/*.dat)")
    parser.add_argument("--no-dat", action="store_true", help="analyze PE only")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "artifacts/pe-inventory" / EXPECTED_SHA256 / "T5-font-requests.json")
    args = parser.parse_args()
    if args.no_dat and args.dat:
        parser.error("--dat and --no-dat are mutually exclusive")
    paths = [] if args.no_dat else args.dat if args.dat is not None else sorted((ROOT / "original").glob("*.dat"))
    try:
        report = analyze(args.exe, paths)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"error: {error}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({report['sha256']})")
    print(f"CreateFontA sites={len(report['static']['import_sites'].get('CreateFontA', []))}; "
          f"GetGlyphOutlineA sites={len(report['static']['import_sites'].get('GetGlyphOutlineA', []))}; "
          f"DAT archives={len(report['text_sources'])}")


if __name__ == "__main__":
    main()
