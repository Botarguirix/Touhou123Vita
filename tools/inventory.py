"""Inventory local reference files; never upload commercial game data."""
import argparse, hashlib, json, struct
from pathlib import Path

def pe_metadata(data):
    if len(data) < 64 or data[:2] != b'MZ':
        raise ValueError('Not a DOS/PE executable')
    off = struct.unpack_from('<I', data, 60)[0]
    if off + 56 > len(data) or data[off:off+4] != b'PE\0\0':
        raise ValueError('Invalid PE header')
    machine, sections = struct.unpack_from('<HH', data, off+4)
    magic = struct.unpack_from('<H', data, off+24)[0]
    if magic != 0x10b: raise ValueError('Expected PE32')
    entry, image_base = struct.unpack_from('<I', data, off+40)[0], struct.unpack_from('<I', data, off+52)[0]
    return dict(machine=hex(machine), sections=sections, entry_rva=hex(entry), image_base=hex(image_base))

def inventory(root):
    result = []
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.suffix.lower() not in ('.exe', '.dll', '.dat'): continue
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
        entry = dict(name=path.name, bytes=path.stat().st_size, sha256=h.hexdigest())
        if path.suffix.lower() in ('.exe', '.dll'):
            try: entry['pe'] = pe_metadata(path.read_bytes())
            except ValueError as e: entry['pe_error'] = str(e)
        result.append(entry)
    return dict(schema=1, files=result)

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('root', type=Path); ap.add_argument('output', type=Path)
    a=ap.parse_args(); a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(inventory(a.root), indent=2)+'\n', encoding='utf-8')
