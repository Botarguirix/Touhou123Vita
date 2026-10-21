"""Execute the position/velocity prefix of the pinned common Player reset."""
import hashlib
import struct
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local/python-deps'))
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESI,UC_X86_REG_ESP

SHA256='f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e'

def reset_position(side, exe=ROOT/'original/th123.exe'):
    raw=exe.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA256:
        raise ValueError('Unexpected reference executable')
    pe=pefile.PE(data=raw);image=pe.get_memory_mapped_image()
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    uc.mem_map(pe.OPTIONAL_HEADER.ImageBase,(len(image)+4095)&~4095)
    uc.mem_write(pe.OPTIONAL_HEADER.ImageBase,image)
    player=0x1000000;stack=0x2000000
    uc.mem_map(player,4096);uc.mem_map(stack,4096)
    uc.mem_write(player+0x350,bytes([side]))
    uc.reg_write(UC_X86_REG_ESI,player);uc.reg_write(UC_X86_REG_ESP,stack+2048)
    uc.hook_add(UC_HOOK_CODE,lambda machine,address,size,data:
                machine.emu_stop() if address==0x46BAA7 else None)
    # Stop before unrelated sprite reset calls; no instruction in this prefix
    # is substituted, and the position/facing/zero velocities are real writes.
    uc.emu_start(0x46BA2E,0x46BAA7,count=100)
    x,y,vx,vy=struct.unpack('<4f',uc.mem_read(player+0xEC,16))
    return dict(x=x,y=y,vx=vx,vy=vy,
                facing=struct.unpack('<b',uc.mem_read(player+0x104,1))[0])

if __name__=='__main__':
    import json
    print(json.dumps({'sha256':SHA256,'left':reset_position(0),'right':reset_position(1)},indent=2))
