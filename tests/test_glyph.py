"""Rasterizador FreeType portable; los binarios y bitmaps permanecen locales."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
CC=shutil.which('gcc') or r'C:\msys64\ucrt64\bin\gcc.exe'
FT=Path(os.environ.get('FREETYPE_PREFIX',r'C:\msys64\ucrt64'))
FONT=Path(os.environ.get('T123_FONT',ROOT/'local/fonts/NotoSansMonoCJKjp-Regular.otf'))
READY=Path(CC).exists() and (FT/'include/freetype2/ft2build.h').exists() and FONT.exists()

class FetchFontTests(unittest.TestCase):
    def test_corrupt_font_rejected_without_network(self):
        spec=importlib.util.spec_from_file_location('fetch_font',ROOT/'tools/fetch_font.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/module.FILES[0][1]).write_bytes(b'wrong font')
            with self.assertRaisesRegex(ValueError,'SHA-256 incorrecto'):module.fetch(temp,check=True)
    def test_missing_font_check_does_not_download(self):
        spec=importlib.util.spec_from_file_location('fetch_font',ROOT/'tools/fetch_font.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'Falta'):module.fetch(temp,check=True)

@unittest.skipUnless(READY,'Falta GCC, FreeType o fuente; ejecutar tools/fetch_font.py')
class GlyphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.exe=Path(cls.tmp.name)/'glyph.exe';cls.env=os.environ.copy()
        cls.env['PATH']=str(FT/'bin')+os.pathsep+cls.env.get('PATH','')
        flags=[CC,'-std=gnu11','-O1','-Wall','-Wextra','-Werror','-DT123_GLYPH_TEST',
               '-I',str(FT/'include/freetype2'),'-I',str(ROOT/'recomp/host'),
               str(ROOT/'recomp/host/glyph.c'),str(ROOT/'tests/glyph_harness.c'),
               '-L',str(FT/'lib'),'-lfreetype','-lpthread','-o',str(cls.exe)]
        result=subprocess.run(flags,capture_output=True,text=True,env=cls.env)
        if result.returncode:raise RuntimeError(result.stderr)
    def test_raster_layout_bold_cache_and_threads(self):
        result=subprocess.run([str(self.exe),str(FONT)],capture_output=True,text=True,env=self.env,timeout=60)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('PASS glyph contracts, cache, bold and threads',result.stdout)
    def test_render_own_text_image(self):
        image=Path(self.tmp.name)/'glyph.pgm'
        result=subprocess.run([str(self.exe),str(FONT),'image',str(image)],capture_output=True,text=True,env=self.env,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        data=image.read_bytes();self.assertTrue(data.startswith(b'P5\n640 180\n255\n'))
        self.assertIn(0,data);self.assertIn(255,data)

if __name__=='__main__':unittest.main()
