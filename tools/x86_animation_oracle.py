"""Execute original PE32 counter/pose/sequence routines; graphics refresh is intercepted.
No original code or resource bytes are exported. Vectors stay under artifacts/.
"""
import argparse,hashlib,json,random,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'local/python-deps'))
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
REFERENCES={
 'f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e':(0x438c60,0x464b70,0x464b50,0x464bf0,0x43a250),
 '24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3':(0x437d50,0x463b30,0x463b10,0x463bb0,0x4390e0),
}
OBJ,SEQ,FRAMES,VT,STACK,STOP=0x1000000,0x1010000,0x1020000,0x1030000,0x2000000,0x3000000
def oracle(exe,output):
    raw=exe.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if sha not in REFERENCES:raise ValueError('Reference executable SHA256 mismatch')
    advance,next_pose,set_pose,next_sequence,graphics=REFERENCES[sha]
    pe=pefile.PE(data=raw);image=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(base,(len(image)+4095)&~4095);u.mem_write(base,image)
    for address,size in [(OBJ,4096),(SEQ,4096),(FRAMES,4096),(VT,4096),(STACK,65536),(STOP,4096)]:u.mem_map(address,size)
    # The original routine calls a render-info refresh after choosing the frame.
    # Preserve all counter and frame-pointer changes, then return before graphics code.
    refresh_calls=[0]
    def hook(uc,address,size,user):
        if address==graphics:
            refresh_calls[0]+=1;esp=uc.reg_read(UC_X86_REG_ESP)
            ret=struct.unpack('<I',uc.mem_read(esp,4))[0]
            uc.reg_write(UC_X86_REG_ESP,esp+4);uc.reg_write(UC_X86_REG_EIP,ret)
    u.hook_add(UC_HOOK_CODE,hook)
    def w(address,fmt,*v):u.mem_write(address,struct.pack('<'+fmt,*v))
    w(VT+5*4,'I',next_sequence);w(VT+7*4,'I',set_pose);w(VT+8*4,'I',next_pose)
    rng=random.Random(123);rows=[]
    for case in range(2048):
        n=rng.choice([1,2]);a,b=rng.randint(1,20),rng.randint(1,20);loop=rng.randrange(2)
        pose=rng.randrange(n);pf=rng.choice([0,1,a-1,a,32766,32767,65534,65535,rng.randrange(30)])
        cf=rng.choice([0,1,0xffffffff,rng.randrange(65536)]);dt=[a,b][pose]
        u.mem_write(OBJ,bytes(4096));u.mem_write(SEQ,bytes(4096));u.mem_write(FRAMES,bytes(4096))
        w(OBJ,'I',VT);w(OBJ+0x13e,'HHHIHHH',0,pose,pf,cf,n,0,dt)
        w(OBJ+0x15c,'I',SEQ)
        w(SEQ+4,'II',FRAMES,FRAMES+n*0xa8);w(SEQ+0x14,'B',loop);w(SEQ+0x18,'II',0,SEQ)
        w(FRAMES+8,'H',a);w(FRAMES+0xa8+8,'H',b)
        w(STACK+65532,'I',STOP);u.reg_write(UC_X86_REG_ECX,OBJ);u.reg_write(UC_X86_REG_ESP,STACK+65532)
        u.emu_start(advance,STOP,count=5000)
        if u.reg_read(UC_X86_REG_EIP)!=STOP:raise RuntimeError('Original routine did not return')
        result=u.reg_read(UC_X86_REG_EAX)&255
        es,ep,ef,ec,_,_,ed=struct.unpack('<HHHIHHH',u.mem_read(OBJ+0x13e,16))
        rows.append(','.join(map(str,[n,a,b,loop,0,pose,pf,cf,dt,result,es,ep,ef,ec,ed])))
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(rows)+'\n',encoding='ascii')
    output.with_suffix('.json').write_text(json.dumps(dict(schema=1,reference_sha256=sha,cases=len(rows),graphics_refresh_intercepted=refresh_calls[0],addresses=[hex(n) for n in REFERENCES[sha]]),indent=2)+'\n')
    print(f'Original x86 vectors: {len(rows)}; graphics refresh callbacks: {refresh_calls[0]}')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('exe',type=Path);p.add_argument('output',type=Path);a=p.parse_args();oracle(a.exe,a.output)
