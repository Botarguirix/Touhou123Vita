#!/usr/bin/env python3
"""Extrae e inspecciona los efectos FX del PE fijado; salidas solo locales."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
sys.path.insert(0, str(ROOT / "local/python-deps"))
import pefile

# Tamaños y referencias inmediatas del PE fijado, comprobados en los callers.
SITES = ((0x85A608, 0x4D0, 0x471665),
         (0x85F908, 0x1B20, 0x7FB030),
         (0x861428, 0x684, 0x7FB049))
TYPES = {0: "void", 1: "bool", 2: "int", 3: "float", 4: "string",
         5: "texture", 6: "texture1d", 7: "texture2d", 8: "texture3d",
         9: "texturecube", 10: "sampler", 11: "sampler1d", 12: "sampler2d",
         13: "sampler3d", 14: "samplercube", 15: "pixelshader", 16: "vertexshader"}
CLASSES = {0: "scalar", 1: "vector", 2: "matrix_rows", 3: "matrix_columns",
           4: "object", 5: "struct"}
STATES = {146: "VertexShader", 147: "PixelShader", 160: "PixelShaderConstant1",
          161: "PixelShaderConstant2", 164: "Texture"}
OPCODES = {0: ("nop", 0), 1: ("mov", 2), 2: ("add", 3), 3: ("sub", 3),
           4: ("mad", 4), 5: ("mul", 3), 6: ("rcp", 2), 7: ("rsq", 2),
           8: ("dp3", 3), 9: ("dp4", 3), 10: ("min", 3), 11: ("max", 3),
           12: ("slt", 3), 13: ("sge", 3), 14: ("exp", 2), 15: ("log", 2),
           16: ("lit", 2), 17: ("dst", 3), 18: ("lrp", 4), 19: ("frc", 2),
           20: ("m4x4", 3), 21: ("m4x3", 3), 22: ("m3x4", 3),
           23: ("m3x3", 3), 24: ("m3x2", 3), 31: ("dcl", 2),
           35: ("abs", 2), 36: ("nrm", 2), 64: ("texcoord", 1),
           65: ("texkill", 1), 66: ("tex", 1), 67: ("texbem", 2),
           68: ("texbeml", 2), 69: ("texreg2ar", 2), 70: ("texreg2gb", 2),
           71: ("texm3x2pad", 2), 72: ("texm3x2tex", 2),
           73: ("texm3x3pad", 2), 74: ("texm3x3tex", 2),
           76: ("texm3x3spec", 3), 77: ("texm3x3vspec", 2),
           78: ("expp", 2), 79: ("logp", 2), 80: ("cnd", 4),
           81: ("def", 5), 88: ("cmp", 4)}


class Reader:
    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos

    def take(self, size):
        if size < 0 or self.pos < 0 or self.pos + size > len(self.data):
            raise ValueError("truncated FX data")
        value = self.data[self.pos:self.pos + size]
        self.pos += size
        return value

    def u32(self):
        return struct.unpack("<I", self.take(4))[0]

    def name(self, offset):
        other = Reader(self.data, offset)
        size = other.u32()
        if not size:
            return None
        raw = other.take(size)
        if raw[-1] != 0:
            raise ValueError("unterminated FX name")
        return raw[:-1].decode("ascii")


def parameter(data, typedef, value):
    r = Reader(data, typedef)
    kind, cls, name, semantic, elements = [r.u32() for _ in range(5)]
    if kind not in TYPES or cls not in CLASSES:
        raise ValueError("unsupported FX type/class")
    if cls == 5:
        raise ValueError("FX structs not implemented")
    rows = columns = 0
    if cls in (0, 1, 2, 3):
        rows, columns = r.u32(), r.u32()
        if cls == 1:
            rows, columns = columns, rows
    result = {"type": TYPES[kind], "class": CLASSES[cls], "name": r.name(name),
              "semantic": r.name(semantic), "elements": elements,
              "rows": rows, "columns": columns, "value_offset": value}
    v = Reader(data, value)
    if cls == 4 and kind in range(10, 15):
        count = v.u32()
        if count > 256:
            raise ValueError("invalid sampler state count")
        result["sampler_states"] = [state(v) for _ in range(count)]
    elif cls == 4:
        result["object_ids"] = [v.u32() for _ in range(max(1, elements))]
    else:
        count = rows * columns * max(1, elements)
        if count > 65536:
            raise ValueError("invalid FX value dimensions")
        fmt = "f" if kind == 3 else "I"
        result["initial_value"] = list(struct.unpack("<" + fmt * count, v.take(4 * count)))
    return result


def state(r):
    operation, index, typedef, value = [r.u32() for _ in range(4)]
    return {"operation": operation, "operation_name": STATES.get(operation, "unknown"), "index": index,
            "parameter": parameter(r.data, typedef, value)}


def annotations(r, count):
    if count > 256:
        raise ValueError("invalid annotation count")
    result = []
    for _ in range(count):
        typedef, value = r.u32(), r.u32()
        result.append(parameter(r.data, typedef, value))
    return result


def parse_effect(blob):
    header = Reader(blob)
    if header.u32() != 0xFEFF0901:
        raise ValueError("not an FX9 binary")
    metadata = header.u32()
    data = blob[8:]
    r = Reader(data, metadata)
    nparams, ntech, nshaders, nobjects = [r.u32() for _ in range(4)]
    if max(nparams, ntech, nobjects, nshaders) > 4096:
        raise ValueError("invalid FX counts")
    params, techniques = [], []
    for _ in range(nparams):
        typedef, value, flags, nanno = [r.u32() for _ in range(4)]
        entry = parameter(data, typedef, value)
        entry.update(flags=flags, annotations=annotations(r, nanno))
        params.append(entry)
    for _ in range(ntech):
        name, nanno, npass = [r.u32() for _ in range(3)]
        if npass > 256:
            raise ValueError("invalid pass count")
        technique = {"name": r.name(name), "annotations": annotations(r, nanno), "passes": []}
        for _ in range(npass):
            pname, panno, nstates = [r.u32() for _ in range(3)]
            if nstates > 4096:
                raise ValueError("invalid state count")
            technique["passes"].append({"name": r.name(pname),
                                        "annotations": annotations(r, panno),
                                        "states": [state(r) for _ in range(nstates)]})
        techniques.append(technique)
    strings, resources = r.u32(), r.u32()
    if max(strings, resources) > 4096:
        raise ValueError("invalid FX resource count")
    objects = []
    for _ in range(strings):
        object_id, size = r.u32(), r.u32()
        start = r.pos
        payload = r.take((size + 3) & ~3)[:size]
        objects.append({"object_id": object_id, "offset": start + 8,
                        "size": size})
    bindings = []
    for _ in range(resources):
        technique, index, element, state_index, usage, size = [r.u32() for _ in range(6)]
        start = r.pos
        r.take((size + 3) & ~3)
        bindings.append({"technique": technique, "index": index, "element": element,
                         "state_index": state_index, "usage": usage,
                         "offset": start + 8, "size": size})
    if r.pos + 8 != len(blob):
        raise ValueError(f"FX length mismatch: parsed {r.pos + 8}, supplied {len(blob)}")
    return {"parameters": params, "techniques": techniques, "objects": objects,
            "resources": bindings, "shader_slots": nshaders, "object_count": nobjects}


def register(token, dest=False, stage="vs"):
    kind = ((token >> 28) & 7) | ((token >> 8) & 24)
    number = token & 0x7FF
    prefixes = {0: "r", 1: "v", 2: "c", 3: "t" if stage == "ps" else "a", 5: "oD", 6: "oT",
                7: "i", 8: "oC", 10: "s", 14: "b"}
    if kind == 4:
        name = {0: "oPos", 1: "oFog", 2: "oPts"}.get(number)
        if name is None:
            raise ValueError("unknown raster output")
    elif kind in prefixes:
        name = prefixes[kind] + str(number)
    else:
        raise ValueError(f"unsupported register type {kind}")
    if token & 0x2000:
        raise ValueError("relative shader registers not implemented")
    if dest:
        mask = (token >> 16) & 15
        if mask != 15:
            name += "." + "".join(c for i, c in enumerate("xyzw") if mask & (1 << i))
    else:
        swizzle = (token >> 16) & 255
        if swizzle != 0xE4:
            chars = "".join("xyzw"[(swizzle >> (2 * i)) & 3] for i in range(4))
            name += "." + (chars[0] if len(set(chars)) == 1 else chars)
        modifier = (token >> 24) & 15
        if modifier == 1:
            name = "-" + name
        elif modifier != 0:
            raise ValueError(f"unsupported source modifier {modifier}")
    return name


def disassemble_shader(blob):
    r = Reader(blob)
    version = r.u32()
    stage = {0xFFFE: "vs", 0xFFFF: "ps"}.get(version >> 16)
    major, minor = (version >> 8) & 255, version & 255
    if stage is None or major not in (1, 2, 3):
        raise ValueError("invalid shader version")
    lines, count = [f"{stage}_{major}_{minor}"], 0
    while r.pos < len(blob):
        token = r.u32()
        opcode = token & 0xFFFF
        if opcode == 0xFFFF:
            if r.pos != len(blob):
                raise ValueError("bytes after shader END")
            return {"profile": lines[0], "instructions": count, "asm": "\n".join(lines) + "\n"}
        if opcode == 0xFFFE:
            r.take(((token >> 16) & 0x7FFF) * 4)
            continue
        if opcode not in OPCODES:
            raise ValueError(f"unsupported shader opcode {opcode:#x}")
        mnemonic, length = OPCODES[opcode]
        if opcode == 66 and major >= 2:
            length = 3
        if major >= 2 and ((token >> 24) & 15) != length:
            raise ValueError("shader operand count mismatch")
        args = [r.u32() for _ in range(length)]
        if opcode == 81:
            operands = [register(args[0], True, stage)] + [repr(struct.unpack("<f", struct.pack("<I", w))[0]) for w in args[1:]]
        elif opcode == 31:
            usage = {0: "position", 1: "blendweight", 2: "blendindices", 3: "normal",
                     4: "psize", 5: "texcoord", 6: "tangent", 7: "binormal",
                     8: "tessfactor", 9: "positiont", 10: "color", 11: "fog",
                     12: "depth", 13: "sample"}.get(args[0] & 15)
            if usage is None:
                raise ValueError("unsupported DCL usage")
            semantic_index = (args[0] >> 16) & 15
            mnemonic += "_" + usage + (str(semantic_index) if semantic_index else "")
            operands = [register(args[1], True, stage)]
        else:
            operands = [register(w, i == 0, stage) for i, w in enumerate(args)]
        if token & 0xFF0000:
            raise ValueError("shader instruction controls not implemented")
        if args and opcode != 31:
            shift = (args[0] >> 24) & 15
            suffix = {0: "", 1: "_x2", 2: "_x4", 3: "_x8",
                      13: "_d8", 14: "_d4", 15: "_d2"}.get(shift)
            if suffix is None or (args[0] >> 20) & 14:
                raise ValueError("shader destination modifier not implemented")
            mnemonic += suffix
            if args[0] & 0x00100000:
                mnemonic += "_sat"
        lines.append(mnemonic + " " + ", ".join(operands))
        count += 1
    raise ValueError("shader END missing")


def extract(exe, output):
    raw = Path(exe).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError("reference SHA256 mismatch")
    pe = pefile.PE(data=raw)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    effects = []
    for va, size, caller in SITES:
        blob = pe.get_data(va - pe.OPTIONAL_HEADER.ImageBase, size)
        parsed = parse_effect(blob)
        stem = f"effect-{va:08x}"
        (output / (stem + ".fxo")).write_bytes(blob)
        parsed.update(va=va, size=size, caller=caller, wrapper=0x418190,
                      sha256=hashlib.sha256(blob).hexdigest(), shaders=[])
        # Los shaders vienen delimitados por las longitudes de recursos FX.
        for resource in parsed["objects"] + parsed["resources"]:
            data = blob[resource["offset"]:resource["offset"] + resource["size"]]
            if len(data) < 4 or struct.unpack_from("<I", data)[0] >> 16 not in (0xFFFE, 0xFFFF):
                if all(c == 0 or 32 <= c < 127 for c in data):
                    resource["text"] = data.rstrip(b"\0").decode("ascii")
                else:
                    resource["payload_kind"] = "binary_non_shader"
                continue
            shader = disassemble_shader(data)
            number = len(parsed["shaders"])
            (output / f"{stem}-shader-{number}.asm").write_text(shader.pop("asm"), encoding="utf-8")
            (output / f"{stem}-shader-{number}.bin").write_bytes(data)
            shader.update(binding=resource)
            if "object_id" in resource:
                shader["parameter_names"] = [p["name"] for p in parsed["parameters"]
                                             if resource["object_id"] in p.get("object_ids", [])]
            else:
                shader["pass_name"] = parsed["techniques"][resource["technique"]]["passes"][resource["index"]]["name"]
            parsed["shaders"].append(shader)
        effects.append(parsed)
    result = {"sha256": SHA256, "effects": effects}
    (output / "effects.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    p.add_argument("--output", type=Path, default=ROOT / "artifacts/pe-inventory" / SHA256 / "effects")
    args = p.parse_args()
    result = extract(args.exe, args.output)
    print(f"extracted {len(result['effects'])} effects to {args.output}")


if __name__ == "__main__":
    main()
