"""Compare native decoder output to independent Shady Packer conversions (local artifacts)."""
import csv,json,struct
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1];out=root/'artifacts';results={}
for character in ['reimu','chirno']:
    original=out/'vanilla-decoded/data/character'/character/(character+'.xml')
    native=set(tuple(map(int,row)) for row in csv.reader((out/(character+'-pattern.csv')).open()))
    pattern=ET.parse(original).getroot()
    converted=set((int(m.get('id')),int(m.get('index')),j,int(f.get('duration')),int(f.find('traits').get('damage')),int(f.get('xoffset')),int(f.get('yoffset')),len(f.findall('hit/box')),len(f.findall('attack/box'))) for m in pattern.findall('move') for j,f in enumerate(m.findall('frame')))
    if native!=converted:raise AssertionError(f'{character}: PAT differs from reference')
    results[character+'_poses']=len(native)
    data=(out/(character+'-native.rgba')).read_bytes();width,height=struct.unpack('<II',data[:8])
    reference=root/'assets'/('player.rgba' if character=='reimu' else 'cpu.rgba')
    if data!=reference.read_bytes():raise AssertionError(f'{character}: bitmap differs from reference')
    results[character+'_pixels']=width*height
(out/'dat-comparison.json').write_text(json.dumps(dict(schema=1,passed=True,**results),indent=2)+'\n')
print(results)
