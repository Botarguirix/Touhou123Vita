"""Convert locally extracted reference PNGs to simple RGBA textures; output is gitignored."""
import argparse, struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
def raw(im,path):
    im=im.convert('RGBA');path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(struct.pack('<II',*im.size)+im.tobytes());im.save(path.with_suffix('.png'))
def sprite(base,character,pattern,target):
    folder=base/'data'/'character'/character
    im=Image.open(next(folder.glob(pattern)))
    if im.mode=='P':
        palettes=list(folder.glob('palette000.act')) or list(folder.glob('palette001.act'))
        if not palettes:raise ValueError('Missing character palette')
        im.putpalette(palettes[0].read_bytes());im.info['transparency']=0
    raw(im,target)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('extracted',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    sprite(a.extracted,'reimu','stand000*.png',a.output/'player.rgba')
    sprite(a.extracted,'chirno','stand000.png',a.output/'cpu.rgba')
    # First environment tile provides a temporary backdrop, not recovered stage layout.
    stage=Image.open(a.extracted/'data/background/bg10/0000_10.png').convert('RGBA').resize((640,400))
    raw(stage,a.output/'stage.rgba')
    atlas=Image.new('RGBA',(192,128));d=ImageDraw.Draw(atlas);font=ImageFont.load_default()
    for ch in range(32,127):d.text((ch%16*12,ch//16*16),chr(ch),font=font,fill=(255,255,255,255))
    raw(atlas,a.output/'font.rgba')
