"""Contrato portable, constantes de SDK y evidencia del teclado original."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
CC=shutil.which('gcc') or r'C:\msys64\ucrt64\bin\gcc.exe'
SDL=Path(r'C:\msys64\ucrt64\include\SDL2\SDL_scancode.h')
DI=ROOT/'local/SokuLib/directx/dinput.h'
PE=ROOT/'original/th123.exe'

@unittest.skipUnless(Path(CC).exists(),'GCC host no disponible')
class InputMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.exe=Path(cls.tmp.name)/'input-map.exe';cls.env=os.environ.copy()
        cls.env['PATH']=str(Path(CC).parent)+os.pathsep+cls.env.get('PATH','')
        r=subprocess.run([CC,'-std=gnu11','-O1','-Wall','-Wextra','-Werror','-I',str(ROOT/'recomp/host'),
                          str(ROOT/'recomp/host/input_map.c'),str(ROOT/'tests/input_map_harness.c'),'-o',str(cls.exe)],
                         capture_output=True,text=True,env=cls.env)
        if r.returncode:raise RuntimeError(r.stderr)
    def test_contract_and_all_button_combinations(self):
        r=subprocess.run([str(self.exe)],check=True,capture_output=True,text=True,env=self.env,timeout=30)
        self.assertIn('PASS input mapping and 2048 Vita button combinations',r.stdout)
    @unittest.skipUnless(SDL.exists() and DI.exists(),'Faltan cabeceras SDL2/DirectInput de referencia')
    def test_every_declared_mapping_matches_public_header_values(self):
        # El binario C se contrasta con valores del SDK, no solo con su fuente.
        s=re.sub(r'/\*.*?\*/','',SDL.read_text(),flags=re.S)
        sdl={k:int(v) for k,v in re.findall(r'SDL_SCANCODE_(\w+)\s*=\s*(\d+)',s)}
        dik={k:int(v,16) for k,v in re.findall(r'^#define DIK_(\w+)\s+(0x[0-9A-Fa-f]+)',DI.read_text(),re.M)}
        pairs=re.findall(r'/\* SDL_SCANCODE_(\w+) -> DIK_(\w+) \*/',(ROOT/'recomp/host/input_map.c').read_text())
        expected={sdl[a]:dik[b] for a,b in pairs}
        r=subprocess.run([str(self.exe),'dump'],check=True,capture_output=True,text=True,env=self.env)
        actual=dict(tuple(map(int,line.split())) for line in r.stdout.splitlines())
        self.assertEqual(len(actual),512)
        for i in range(512):self.assertEqual(actual[i],expected.get(i,0),f'SDL {i}')
        self.assertEqual(len(expected),141)
    @unittest.skipUnless(PE.exists(),'Falta original/th123.exe')
    def test_original_default_bindings_and_menu_escape(self):
        raw=PE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e')
        sys.path.insert(0,str(ROOT/'local/python-deps'))
        import pefile
        import capstone as cs
        pe=pefile.PE(data=raw);md=cs.Cs(cs.CS_ARCH_X86,cs.CS_MODE_32);md.detail=True
        ins=md.disasm(pe.get_data(0x435909-0x400000,0x435977-0x435909),0x435909)
        stores={x.operands[0].mem.disp:x.operands[1].imm for x in ins if x.mnemonic=='mov'
                and x.operands[0].type==cs.CS_OP_MEM and x.operands[1].type==cs.CS_OP_IMM}
        self.assertEqual(stores,dict(zip(range(0x144,0x170,4),[0xc8,0xd0,0xcb,0xcd,0x2c,0x2d,0x2e,0x1e,0x1f,0x20,0x10])))
        menu=list(md.disasm(pe.get_data(0x442b9c-0x400000,11),0x442b9c))[0]
        self.assertEqual((menu.mnemonic,menu.operands[1].imm),('mov',1))

if __name__=='__main__':unittest.main()
