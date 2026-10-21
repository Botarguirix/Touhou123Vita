"""Execute the pinned PE's ordinary Player rectangle transform (0x4640b0)."""
import hashlib
import struct
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local/python-deps'))
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_FPCW,UC_X86_REG_EIP

SHA256='f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e'

def transform(box, x, y, facing, exe=ROOT/'original/th123.exe'):
    raw=exe.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA256:
        raise ValueError('Unexpected reference executable')
    pe=pefile.PE(data=raw);image=pe.get_memory_mapped_image()
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    uc.mem_map(pe.OPTIONAL_HEADER.ImageBase,(len(image)+4095)&~4095)
    uc.mem_write(pe.OPTIONAL_HEADER.ImageBase,image)
    player=0x1000000;stack=0x2000000;stop=0x3000000
    for address in (player,stack,stop):uc.mem_map(address,4096)
    source=player+0x900;dest=player+0xA00
    uc.mem_write(player+0xEC,struct.pack('<2f',x,y))
    uc.mem_write(player+0x104,struct.pack('<b',facing))
    uc.mem_write(source,struct.pack('<4i',*box))
    uc.mem_write(stack+2048,struct.pack('<3I',stop,source,dest))
    uc.reg_write(UC_X86_REG_ECX,player);uc.reg_write(UC_X86_REG_ESP,stack+2048)
    uc.reg_write(UC_X86_REG_FPCW,0x037F)
    uc.hook_add(UC_HOOK_CODE,lambda machine,address,size,data:
                machine.emu_stop() if address==stop else None)
    uc.emu_start(0x4640B0,stop,count=10000)
    if uc.reg_read(UC_X86_REG_EIP)!=stop:
        raise RuntimeError('Original rectangle transform did not return')
    return struct.unpack('<4i',uc.mem_read(dest,16))

if __name__=='__main__':
    print(transform((-40,-120,80,0),480,25,1))
    print(transform((-40,-120,80,0),480,25,-1))
