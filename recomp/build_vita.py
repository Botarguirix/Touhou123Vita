#!/usr/bin/env python3
"""Build the Vita VPK of the recompiled game (H1: boot test).

Compiles the generated units (artifacts/recomp/<sha>/gen, from recomp/lift_all.py),
the runtime and the portable host for ARM with VitaSDK, and packs a VPK that holds
only code and the locally generated font/LiveArea assets. The user's th123.exe and
th123a/b/c.dat are read at run time from ux0:data/touhou123vita/.

  python recomp/build_vita.py                 # -> artifacts/recomp/<sha>/vita/T123Recomp.vpk
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
VITASDK = Path(os.environ.get("VITASDK", r"C:\vitasdk"))
BIN = VITASDK / "bin"
CC = BIN / "arm-vita-eabi-gcc.exe"
TITLE_ID, TITLE = "THSV12302", "Touhou123Vita Recomp"
VITA_LIBS = ROOT / "artifacts/vita-libs"  # zlib 1.2.3 built by third_party/vita-libs/build.ps1 (T4)
RUNTIME, HOST, VITA = ROOT / "recomp/runtime", ROOT / "recomp/host", ROOT / "recomp/vita"
LIBS = ["-lvitaGL", "-lvitashark", "-lSceShaccCgExt", "-lmathneon", "-ltaihen_stub", "-lSceShaccCg_stub",
        "-lSceKernelDmacMgr_stub", "-lSceGxm_stub", "-lSceCommonDialog_stub", "-lSceAppUtil_stub",
        "-lSceSysmodule_stub", "-lSceIme_stub", "-lSceAppMgr_stub", "-lSceDisplay_stub", "-lSceCtrl_stub", "-lSceAudio_stub", "-lSceSysmem_stub", "-lSceLibKernel_stub", "-lSceKernelThreadMgr_stub",
        "-lSceProcessmgr_stub", f"-L{VITA_LIBS / 'lib'}", "-lvorbisfile", "-lvorbis", "-logg", "-lz", "-lstdc++", "-lpthread", "-lm", "-lgcc", "-lpthread"]


def run(cmd, **kw):
    result = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if result.returncode:
        raise SystemExit(f"{' '.join(map(str, cmd[:3]))} ...\n{result.stdout}\n{result.stderr[-4000:]}")
    return result


def compile_one(task):
    src, obj, flags, deps = task
    newest = max([src.stat().st_mtime] + [d.stat().st_mtime for d in deps])
    if obj.exists() and obj.stat().st_mtime >= newest:
        return None
    r = subprocess.run([str(CC), *flags, "-c", str(src), "-o", str(obj)], capture_output=True, text=True)
    return f"{src.name}:\n{r.stderr[-3000:]}" if r.returncode else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    parser.add_argument("--opt", default="-O2")  # -O2 build: ~70 min cold, cached in obj-O2
    parser.add_argument("--trace-calls", action="store_true",
                        help="record guest function entries (crash reports name the last ones; slower)")
    args = parser.parse_args()
    gen = ROOT / "artifacts/recomp" / SHA / "gen"
    out = ROOT / "artifacts/recomp" / SHA / "vita"
    objs = out / ("obj" if args.opt == "-O1" else "obj" + args.opt)  # one cache per level
    objs.mkdir(parents=True, exist_ok=True)
    if not (gen / "table.c").exists():
        raise SystemExit("run recomp/lift_all.py first")

    common = ["-std=gnu11", args.opt, "-frounding-math", "-fno-strict-aliasing", f"-I{RUNTIME}"]
    if args.trace_calls:
        common.append("-DT123_TRACE_CALLS")
        objs = out / "obj-trace"
        objs.mkdir(parents=True, exist_ok=True)
    gen_flags = common + ["-w", f"-I{gen}"]
    host_flags = common + ["-Wall", "-Wno-unused-parameter", f"-I{HOST}", f"-I{VITA_LIBS / 'include'}",
                           "-DT123_PACKED_TEXTURES"]
    header = [RUNTIME / "guest.h"]
    tasks = [(s, objs / (s.stem + ".o"), gen_flags, header + [gen / "lifted.h"])
             for s in sorted(gen.glob("unit_*.c")) + [gen / "table.c"]]
    host_sources = [s for s in sorted(HOST.glob("*.c")) if s.name not in ("platform_pc.c", "glyph.c", "audio_out_sdl.c", "profile_pc.c")]  # glyph.c: FreeType not in VitaSDK yet (vita/glyph_none.c)
    tasks += [(s, objs / ("host_" + s.stem + ".o"), host_flags, header + [HOST / "win32.h"])
              for s in host_sources + sorted(VITA.glob("*.c")) + [RUNTIME / "guest.c"]]
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        errors = [e for e in pool.map(compile_one, tasks) if e]
    if errors:
        raise SystemExit("\n".join(errors))
    compile_seconds = time.monotonic() - started

    elf, velf, self_, sfo = out / "t123.elf", out / "t123.velf", out / "eboot.bin", out / "param.sfo"
    run([CC, "-Wl,-q", "-Wl,-z,nocopyreloc", *[t[1] for t in tasks], *LIBS, "-o", elf])
    run([BIN / "vita-elf-create.exe", elf, velf])
    run([BIN / "vita-make-fself.exe", "-c", velf, self_])
    run([BIN / "vita-mksfoex.exe", "-s", "APP_VER=00.01", "-s", f"TITLE_ID={TITLE_ID}", TITLE, sfo])
    sce_sys = out / "sce_sys"
    run([sys.executable, ROOT / "tools/make_livearea_assets.py", sce_sys])
    font = ROOT / "assets/font.rgba"
    if not font.exists():
        run([sys.executable, ROOT / "tools/font.py", ROOT / "assets"])
    vpk = out / "T123Recomp.vpk"
    pack = [BIN / "vita-pack-vpk.exe", "-s", sfo, "-b", self_,
            "-a", f"{font}=assets/font.rgba",
            "-a", f"{sce_sys / 'icon0.png'}=sce_sys/icon0.png",
            "-a", f"{sce_sys / 'livearea/contents/bg.png'}=sce_sys/livearea/contents/bg.png",
            "-a", f"{sce_sys / 'livearea/contents/startup.png'}=sce_sys/livearea/contents/startup.png",
            "-a", f"{sce_sys / 'livearea/contents/template.xml'}=sce_sys/livearea/contents/template.xml",
            vpk]
    run(pack)
    text_size = run([BIN / "arm-vita-eabi-size.exe", elf]).stdout.strip().splitlines()[-1].split()
    print(f"compiled {len(tasks)} objects in {compile_seconds:.0f} s")
    print(f"ELF text={int(text_size[0]) // 1024} KiB data={int(text_size[1]) // 1024} KiB "
          f"bss={int(text_size[2]) // 1024} KiB; eboot.bin {self_.stat().st_size // 1024} KiB")
    print(f"VPK {vpk} ({vpk.stat().st_size // 1024} KiB) sha256 "
          f"{hashlib.sha256(vpk.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
