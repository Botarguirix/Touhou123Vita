"""Genera CP932 desde Python con correcciones Windows medidas (sin descargas).

Windows 932/flags=0: 9604 pares validos, no 7915 (incluye 1880 PUA).
Decodificacion valida identica a Python. Invalidos: U+30FB; consume dos bytes
salvo que el segundo sea NUL. Codificacion BMP: 458 diferencias frente a Python:
373 duplicados IBM prefieren FA40..FC4B; 82 best-fit adicionales; U+2016,
U+2212 y U+301C usan '?' y used_default=1. Los sustitutos UTF-16 se sustituyen
individualmente, incluso una pareja valida. Evidencia: oracle --windows-report,
Windows kernel32 MultiByteToWideChar / WideCharToMultiByte(932,0), todos los BMP.

Las correcciones best-fit siguientes se midieron en Windows y son datos del
estandar, nunca del juego. --check es reproducible sin Windows ni dependencias.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEADS = list(range(0x81, 0xa0)) + list(range(0xe0, 0xfd))
TRAILS = list(range(0x40, 0x7f)) + list(range(0x80, 0xfd))
# Best-fit de Windows, medido exhaustivamente; Python levanta UnicodeEncodeError.
BEST_FIT = {161: 33, 165: 92, 166: 124, 169: 99, 170: 97, 171: 33249, 173: 45, 174: 82, 175: 33104, 178: 50, 179: 51, 181: 33738, 183: 33093, 184: 33091, 185: 49, 186: 111, 187: 33250, 192: 65, 193: 65, 194: 65, 195: 65, 196: 65, 197: 65, 198: 65, 199: 67, 200: 69, 201: 69, 202: 69, 203: 69, 204: 73, 205: 73, 206: 73, 207: 73, 208: 68, 209: 78, 210: 79, 211: 79, 212: 79, 213: 79, 214: 79, 216: 79, 217: 85, 218: 85, 219: 85, 220: 85, 221: 89, 222: 84, 223: 115, 224: 97, 225: 97, 226: 97, 227: 97, 228: 97, 229: 97, 230: 97, 231: 99, 232: 101, 233: 101, 234: 101, 235: 101, 236: 105, 237: 105, 238: 105, 239: 105, 240: 100, 241: 110, 242: 111, 243: 111, 244: 111, 245: 111, 246: 111, 248: 111, 249: 117, 250: 117, 251: 117, 252: 117, 253: 121, 254: 116, 255: 121, 12436: 33684, 12441: 33098, 12442: 33099}
REJECT = {0x2016, 0x2212, 0x301c}


def mappings():
    forward = []
    duplicates = {}
    for a in LEADS:
        for b in TRAILS:
            try:
                u = ord(bytes([a,b]).decode('cp932'))
            except UnicodeDecodeError:
                u = 0
            forward.append(u)
            if u and a >= 0xfa:
                duplicates[u] = (a << 8) | b
    reverse = {}
    for u in range(65536):
        if u in REJECT:
            continue
        try:
            raw = chr(u).encode('cp932')
        except UnicodeEncodeError:
            continue
        reverse[u] = int.from_bytes(raw, 'big')
    # Windows prefiere IBM frente a duplicados NEC ED/EE, pero conserva otros
    # codigos estandar/NEC (p. ej. U+2116 -> 8782, no FA59).
    reverse.update({u:b for u,b in duplicates.items()
                    if 0xed40 <= reverse.get(u,0) <= 0xeefc})
    reverse.update(BEST_FIT)
    # Unidades de un byte se resuelven aritmeticamente en C.
    reverse = {u:b for u,b in reverse.items() if not
               (u <= 0x80 or 0xff61 <= u <= 0xff9f or 0xf8f0 <= u <= 0xf8f3)}
    return forward, sorted(reverse.items())


def render():
    forward, reverse = mappings()
    size = len(forward)*2 + len(reverse)*4
    assert size < 65536, size
    lines = ['/* Generado por tools/gen_sjis_table.py; CP932 Python + Windows. */',
             '#ifndef T123_SJIS_TABLE_H', '#define T123_SJIS_TABLE_H',
             '#include <stdint.h>', f'#define SJIS_TABLE_BYTES {size}u',
             'static const uint16_t sjis_decode[] = {']
    for i in range(0,len(forward),12):
        lines.append('    '+','.join(f'0x{x:04x}' for x in forward[i:i+12])+',')
    lines += ['};', 'typedef struct { uint16_t unicode, bytes; } SjisPair;',
              'static const SjisPair sjis_encode[] = {']
    for i in range(0,len(reverse),6):
        lines.append('    '+','.join(f'{{0x{u:04x},0x{b:04x}}}' for u,b in reverse[i:i+6])+',')
    lines += ['};', '#endif', '']
    return '\n'.join(lines), {'table_bytes':size,'valid_double_byte':sum(bool(x) for x in forward),
                              'reverse_entries':len(reverse)}


def windows_report():
    import ctypes
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    mb=k.MultiByteToWideChar
    mb.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_int]
    wc=k.WideCharToMultiByte
    wc.argtypes=mb.argtypes+[ctypes.c_void_p,ctypes.c_void_p]
    diffs=[]
    for u in range(65536):
        c=ctypes.c_uint16(u);out=(ctypes.c_ubyte*8)();used=ctypes.c_int()
        n=wc(932,0,ctypes.byref(c),1,out,8,None,ctypes.byref(used))
        try: py=chr(u).encode('cp932'); default=False
        except UnicodeEncodeError: py=b'?'; default=True
        actual=bytes(out[:n])
        if py!=actual or default!=bool(used.value):
            diffs.append({'unicode':f'U+{u:04X}','python':py.hex(),'windows':actual.hex(),
                          'used_default':bool(used.value)})
    return {'encoding_differences':diffs,'difference_count':len(diffs)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--windows-report',type=Path)
    args=parser.parse_args()
    content,stats=render();target=ROOT/'recomp/host/sjis_table.h'
    if args.check:
        if not target.exists() or target.read_text(encoding='utf8') != content:
            parser.exit(1,'FAIL: tabla distinta; regenerar con tools/gen_sjis_table.py\n')
    else:
        target.write_text(content,encoding='utf8',newline='\n')
    if args.windows_report:
        args.windows_report.parent.mkdir(parents=True,exist_ok=True)
        args.windows_report.write_text(json.dumps(windows_report(),indent=2)+'\n',encoding='utf8')
    print(json.dumps(stats,sort_keys=True))

if __name__=='__main__':
    main()
