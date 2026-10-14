"""Generate a local bitmap atlas using Pillow's bundled default font."""
from pathlib import Path
import struct,sys
from PIL import Image, ImageDraw, ImageFont
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
atlas=Image.new('RGBA',(192,128));draw=ImageDraw.Draw(atlas);font=ImageFont.load_default()
for ch in range(32,127):draw.text((ch%16*12,ch//16*16),chr(ch),font=font,fill=(255,255,255,255))
(out/'font.rgba').write_bytes(struct.pack('<II',*atlas.size)+atlas.tobytes())
