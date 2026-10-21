#!/usr/bin/env python3
"""Inventory the hash-pinned TH123 PE32 image for the static-recompilation route (F0).

Reports headers, sections, toolchain (Rich header), imports and their call sites,
COM GUIDs, embedded libraries/shader hints and an instruction-class census from a
linear sweep of executable sections. Full output stays local under artifacts/;
only aggregate metadata is meant for docs/PE_INVENTORY.md.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import re
import struct
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile  # noqa: E402
from capstone import Cs, CS_ARCH_X86, CS_MODE_32  # noqa: E402

# Rich header product build numbers -> Visual Studio release (common subset).
MSVC_BUILDS = {
    8168: "VS6 (12.0) SP6", 8447: "VS6 (12.0) SP5", 9466: "VS2002 (13.0)",
    3077: "VS2003 (13.10)", 4035: "VS2003 (13.10) SP1", 6030: "VS2003 (13.10) SP1",
    50727: "VS2005 (14.0)", 21022: "VS2008 (15.0)", 30729: "VS2008 (15.0) SP1",
    30319: "VS2010 (16.0)", 40219: "VS2010 (16.0) SP1", 50727 + 1: "VS2005",
}

COM_GUIDS = {
    "CLSID_DirectSound": "47D4D946-62E8-11CF-93BC-444553540000",
    "CLSID_DirectSound8": "3901CC3F-84B5-4FA4-BA35-AA8172B8A09B",
    "IID_IDirectSound": "279AFA83-4981-11CE-A521-0020AF0BE560",
    "IID_IDirectSound8": "C50A7E93-F395-4834-9EF6-7FA99DE50966",
    "IID_IDirectSoundBuffer": "279AFA85-4981-11CE-A521-0020AF0BE560",
    "IID_IDirectSoundBuffer8": "6825A449-7524-4D82-920F-50E36AB3AB1E",
    "IID_IDirectSoundNotify": "B0210783-89CD-11D0-AF08-00A0C925CD16",
    "CLSID_DirectInput": "25E609E0-B259-11CF-BFC7-444553540000",
    "CLSID_DirectInput8": "25E609E4-B259-11CF-BFC7-444553540000",
    "IID_IDirectInput8A": "BF798030-483A-4DA2-AA99-5D64ED369700",
    "IID_IDirectInput8W": "BF798031-483A-4DA2-AA99-5D64ED369700",
    "IID_IDirectInputDevice8A": "54D41080-DC15-4833-A41B-748F73A38179",
    "IID_IDirectInputDevice8W": "54D41081-DC15-4833-A41B-748F73A38179",
    "GUID_SysMouse": "6F1D2B60-D5A0-11CF-BFC7-444553540000",
    "GUID_SysKeyboard": "6F1D2B61-D5A0-11CF-BFC7-444553540000",
    "GUID_Joystick": "6F1D2B70-D5A0-11CF-BFC7-444553540000",
    "CLSID_FilterGraph": "E436EBB3-524F-11CE-9F53-0020AF0BA770",
    "IID_IGraphBuilder": "56A868A9-0AD4-11CE-B03A-0020AF0BA770",
    "IID_IDirect3DTexture9": "85C31227-3DE5-4F00-9B3A-F11AC38C18B5",
    "IID_ID3DXEffect": "F6CEB4B3-4E4C-40DD-B883-8D8DE5EA0CD5",
}

STRING_KEYWORDS = (
    "vorbis", "xiph", "ogg", "zlib", "inflate", "deflate", "libpng", "png",
    "copyright", "microsoft", "visual c++", "runtime error", "dsound", "dinput",
    "d3d", "d3dx", ".fx", "technique", "pass ", "vertexshader", "pixelshader",
    "th123", "th105", "hisoutensoku", "version", "1.10", ".dat", ".cv", ".pat",
    ".csv", ".ogg", ".wav", ".bmp", "replay", ".rep", "profile", "thread",
    "socket", "winsock", "ws2", "imm", "font", "ms gothic", "ｍｓ",
)

SECTION_EXEC = 0x20000000


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = collections.Counter(data)
    n = len(data)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


def guid_bytes(text: str) -> bytes:
    return uuid.UUID(text).bytes_le


def ascii_strings(data: bytes, base: int, minimum: int = 5):
    for match in re.finditer(rb"[\x20-\x7e]{%d,}" % minimum, data):
        yield base + match.start(), match.group().decode("ascii")


def rich_header(pe: pefile.PE):
    rich = getattr(pe, "RICH_HEADER", None)
    if not rich:
        return []
    values = rich.values
    rows = []
    for index in range(0, len(values), 2):
        comp_id, count = values[index], values[index + 1]
        prod, build = comp_id >> 16, comp_id & 0xFFFF
        rows.append({"prodid": prod, "build": build, "count": count,
                     "toolchain_guess": MSVC_BUILDS.get(build)})
    return rows


def imports(pe: pefile.PE):
    table = {}
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        dll = entry.dll.decode("ascii", "replace")
        for imp in entry.imports:
            name = imp.name.decode("ascii", "replace") if imp.name else f"#ord{imp.ordinal}"
            table[imp.address] = (dll, name)
    return table


def census(pe: pefile.PE, iat: dict[int, tuple[str, str]]):
    base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    mnemonics = collections.Counter()
    classes = collections.Counter()
    call_targets = set()
    padding_starts = set()
    import_sites = collections.Counter()
    jump_tables = []
    total = 0
    mem_abs = re.compile(r"\[0x([0-9a-f]+)\]")
    for section in pe.sections:
        if not section.Characteristics & SECTION_EXEC:
            continue
        start = base + section.VirtualAddress
        code = section.get_data()[: section.Misc_VirtualSize]
        end = start + len(code)
        previous_pad = True
        for ins in md.disasm(code, start):
            total += 1
            mnem, ops = ins.mnemonic, ins.op_str
            mnemonics[mnem] += 1
            if mnem in (".byte",):
                classes["undecodable_bytes"] += 1
                continue
            is_pad = mnem == "int3" or (mnem == "nop" and ins.size == 1)
            if previous_pad and not is_pad:
                padding_starts.add(ins.address)
            previous_pad = is_pad
            if mnem.startswith("f") and mnem not in ("femms",):
                classes["x87"] += 1
            if "xmm" in ops:
                classes["sse"] += 1
            if re.search(r"\bmm[0-7]\b", ops):
                classes["mmx"] += 1
            if "fs:" in ops:
                classes["fs_segment(seh/tls)"] += 1
            # Without capstone detail mode, prefixes are folded into the mnemonic text.
            if mnem.startswith("rep"):
                classes["rep_string"] += 1
            if mnem.startswith("lock"):
                classes["lock_atomic"] += 1
            if mnem in ("cpuid", "rdtsc", "int", "into", "in", "out", "sysenter", "hlt", "ud2"):
                classes[f"special:{mnem}"] += 1
            if mnem in ("call", "jmp"):
                if ops.startswith("0x"):
                    if mnem == "call":
                        target = int(ops, 16)
                        if start <= target < end:
                            call_targets.add(target)
                    continue
                absolute = mem_abs.fullmatch(ops.replace("dword ptr ", ""))
                if absolute and int(absolute.group(1), 16) in iat:
                    import_sites[iat[int(absolute.group(1), 16)]] += 1
                    classes[f"{mnem}_import"] += 1
                elif mnem == "jmp" and re.search(r"\*\s*4\s*\+\s*0x", ops):
                    classes["jmp_table"] += 1
                    jump_tables.append(ins.address)
                elif ops.startswith("e") and "[" not in ops:
                    classes[f"{mnem}_register"] += 1
                else:
                    classes[f"{mnem}_memory(vtable/pointer)"] += 1
            elif mnem == "mov":
                absolute = mem_abs.search(ops)
                if absolute and int(absolute.group(1), 16) in iat:
                    import_sites[iat[int(absolute.group(1), 16)]] += 1
                    classes["mov_import_pointer"] += 1
    return {
        "instructions": total,
        "unique_mnemonics": len(mnemonics),
        "mnemonics": dict(mnemonics.most_common()),
        "classes": dict(sorted(classes.items())),
        "direct_call_targets": len(call_targets),
        "padding_delimited_starts": len(padding_starts),
        "function_estimate_union": len(call_targets | padding_starts),
        "jump_table_sites": len(jump_tables),
        "import_sites": {f"{dll}!{name}": count for (dll, name), count in import_sites.most_common()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--output", type=Path, default=None,
                        help="output directory (default artifacts/pe-inventory/<sha>)")
    args = parser.parse_args()

    raw = args.exe.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"reference SHA256 mismatch: {digest}")
    out = args.output or ROOT / "artifacts/pe-inventory" / digest
    out.mkdir(parents=True, exist_ok=True)

    pe = pefile.PE(data=raw)
    base = pe.OPTIONAL_HEADER.ImageBase
    fh, oh = pe.FILE_HEADER, pe.OPTIONAL_HEADER
    sections = [{
        "name": s.Name.rstrip(b"\0").decode("ascii", "replace"),
        "va": f"0x{base + s.VirtualAddress:08x}", "vsize": s.Misc_VirtualSize,
        "rawsize": s.SizeOfRawData, "flags": f"0x{s.Characteristics:08x}",
        "executable": bool(s.Characteristics & SECTION_EXEC),
        "entropy": round(entropy(s.get_data()), 3),
    } for s in pe.sections]

    iat = imports(pe)
    by_dll = collections.defaultdict(list)
    for dll, name in iat.values():
        by_dll[dll].append(name)

    data_blob = b"".join(s.get_data() for s in pe.sections)
    guids = {name: data_blob.find(guid_bytes(text)) >= 0 for name, text in COM_GUIDS.items()}

    strings = []
    for s in pe.sections:
        strings.extend(ascii_strings(s.get_data(), base + s.VirtualAddress))
    keyword_hits = collections.defaultdict(list)
    for address, text in strings:
        lower = text.lower()
        for keyword in STRING_KEYWORDS:
            if keyword in lower:
                keyword_hits[keyword].append(f"0x{address:08x} {text[:120]}")
    (out / "strings.txt").write_text(
        "\n".join(f"0x{a:08x}\t{t}" for a, t in strings) + "\n", encoding="utf-8")

    tls = getattr(pe, "DIRECTORY_ENTRY_TLS", None)
    relocs = getattr(pe, "DIRECTORY_ENTRY_BASERELOC", None)
    resources = collections.Counter()
    if hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            label = pefile.RESOURCE_TYPE.get(entry.id, str(entry.name or entry.id))
            resources[label] += len(entry.directory.entries)

    inventory = {
        "sha256": digest,
        "size": len(raw),
        "machine": f"0x{fh.Machine:04x}",
        "timestamp": fh.TimeDateStamp,
        "image_base": f"0x{base:08x}",
        "entry_point": f"0x{base + oh.AddressOfEntryPoint:08x}",
        "subsystem": oh.Subsystem,
        "linker_version": f"{oh.MajorLinkerVersion}.{oh.MinorLinkerVersion}",
        "os_version": f"{oh.MajorOperatingSystemVersion}.{oh.MinorOperatingSystemVersion}",
        "dll_characteristics": f"0x{oh.DllCharacteristics:04x}",
        "has_relocations": bool(relocs),
        "relocation_blocks": len(relocs) if relocs else 0,
        "tls_callbacks": bool(tls and tls.struct.AddressOfCallBacks),
        "exports": len(pe.DIRECTORY_ENTRY_EXPORT.symbols) if hasattr(pe, "DIRECTORY_ENTRY_EXPORT") else 0,
        "resources": dict(resources),
        "sections": sections,
        "rich_header": rich_header(pe),
        "imports": {dll: sorted(names) for dll, names in sorted(by_dll.items())},
        "import_count": len(iat),
        "com_guids_present": guids,
        "string_count": len(strings),
        "string_keyword_hits": {k: v[:40] for k, v in sorted(keyword_hits.items())},
        "string_keyword_counts": {k: len(v) for k, v in sorted(keyword_hits.items())},
        "code": census(pe, iat),
    }
    (out / "inventory.json").write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")

    code = inventory["code"]
    print(f"sha256 {digest}  size {len(raw)}  base {inventory['image_base']}  entry {inventory['entry_point']}")
    print(f"linker {inventory['linker_version']}  relocs {inventory['has_relocations']}  tls_cb {inventory['tls_callbacks']}")
    for s in sections:
        print(f"  section {s['name']:<8} {s['va']} vsize={s['vsize']:>8} raw={s['rawsize']:>8} H={s['entropy']} exec={s['executable']}")
    print("rich:", [(r["prodid"], r["build"], r["count"], r["toolchain_guess"]) for r in inventory["rich_header"]])
    print(f"imports {len(iat)}:", {dll: len(n) for dll, n in inventory["imports"].items()})
    print("com guids:", [k for k, v in guids.items() if v])
    print(f"instructions {code['instructions']}  unique mnemonics {code['unique_mnemonics']}")
    print(f"functions: call-targets {code['direct_call_targets']}  padding-starts {code['padding_delimited_starts']}  union {code['function_estimate_union']}")
    print("classes:", code["classes"])
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
