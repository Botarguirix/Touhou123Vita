"""Contratos C y comparacion exhaustiva Python/Windows, sin APIs de Windows en C."""
import ctypes
import importlib.util
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
CC=shutil.which('gcc') or (r'C:\msys64\ucrt64\bin\gcc.exe' if Path(r'C:\msys64\ucrt64\bin\gcc.exe').exists() else None)
SPEC=importlib.util.spec_from_file_location('gen_sjis',ROOT/'tools/gen_sjis_table.py')
GEN=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(GEN)

@unittest.skipUnless(CC,'GCC host no disponible')
class SjisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.exe=Path(cls.tmp.name)/'sjis.exe'
        cls.env=os.environ.copy();cls.env['PATH']=str(Path(CC).parent)+os.pathsep+cls.env.get('PATH','')
        subprocess.run([CC,'-std=gnu11','-O2','-Wall','-Wextra','-Werror','-I',str(ROOT/'recomp/host'),str(ROOT/'recomp/host/sjis.c'),str(ROOT/'tests/sjis_harness.c'),'-o',str(cls.exe)],check=True,env=cls.env,capture_output=True)
        dump=Path(cls.tmp.name)/'dump.bin'
        subprocess.run([str(cls.exe),'dump',str(dump)],check=True,env=cls.env,timeout=30)
        rows=list(struct.iter_unpack('<HHH',dump.read_bytes()));cls.dec=rows[:65792];cls.enc=rows[65792:]
        assert len(cls.enc)==65536
    def test_contracts(self):
        r=subprocess.run([str(self.exe)],check=True,env=self.env,capture_output=True,text=True,timeout=30)
        self.assertIn('PASS sjis contracts',r.stdout)
    def test_all_byte_inputs_against_python(self):
        # Windows invalida un par completo; no reutiliza el segundo byte salvo NUL.
        for n,row in enumerate(self.dec):
            raw=bytes([n]) if n<256 else (n-256).to_bytes(2,'big')
            expected=[];i=0
            while i<len(raw):
                a=raw[i];length=2 if a in GEN.LEADS and i+1<len(raw) and raw[i+1] else 1
                try:expected.extend(ord(u) for u in raw[i:i+length].decode('cp932'))
                except UnicodeDecodeError:expected.append(0x30fb)
                i+=length
            self.assertEqual((row[0],list(row[1:row[0]+1])),(len(expected),expected),raw.hex())
    def test_all_bmp_against_python_plus_documented_windows_rules(self):
        _,reverse=GEN.mappings();mapping=dict(reverse)
        differences=0
        for u,row in enumerate(self.enc):
            try:py=chr(u).encode('cp932');default=False
            except UnicodeEncodeError:py=b'?';default=True
            b=mapping.get(u)
            if u<=0x80:b=u
            elif 0xff61<=u<=0xff9f:b=0xa1+u-0xff61
            elif u==0xf8f0:b=0xa0
            elif 0xf8f1<=u<=0xf8f3:b=0xfd+u-0xf8f1
            raw=b.to_bytes(2 if b>255 else 1,'big') if b is not None else b'?'
            used=b is None
            self.assertEqual(row,(len(raw),int.from_bytes(raw,'little'),int(used)),hex(u))
            differences+=int(raw!=py or used!=default)
        self.assertEqual(differences,458)
    @unittest.skipUnless(os.name=='nt','Oracle kernel32 solo en Windows')
    def test_all_inputs_against_windows(self):
        k=ctypes.WinDLL('kernel32',use_last_error=True)
        mb=k.MultiByteToWideChar;mb.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_int]
        wc=k.WideCharToMultiByte;wc.argtypes=mb.argtypes+[ctypes.c_void_p,ctypes.c_void_p]
        for n,row in enumerate(self.dec):
            raw=bytes([n]) if n<256 else (n-256).to_bytes(2,'big');out=(ctypes.c_uint16*2)()
            size=mb(932,0,raw,len(raw),out,2)
            self.assertEqual(row,(size,*out),raw.hex())
        for u,row in enumerate(self.enc):
            code=ctypes.c_uint16(u);out=(ctypes.c_ubyte*2)();used=ctypes.c_int()
            size=wc(932,0,ctypes.byref(code),1,out,2,None,ctypes.byref(used))
            self.assertEqual(row,(size,int.from_bytes(bytes(out),'little'),used.value),hex(u))
    def test_generated_table_and_budget(self):
        text,stats=GEN.render()
        self.assertEqual(text,(ROOT/'recomp/host/sjis_table.h').read_text(encoding='utf8'))
        self.assertLess(stats['table_bytes'],65536)
        self.assertEqual(stats['valid_double_byte'],9604)

if __name__=='__main__':unittest.main()
