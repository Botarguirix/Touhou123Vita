"""Mezclador real, PCM sintético, sin dispositivo ni datos del juego."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CC = shutil.which('gcc') or r'C:\msys64\ucrt64\bin\gcc.exe'

@unittest.skipUnless(Path(CC).is_file(), 'Falta GCC host')
class AudioMixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.exe = Path(cls.tmp.name) / 'audio-mix.exe'
        cls.env = os.environ.copy()
        cls.env['PATH'] = str(Path(CC).parent) + os.pathsep + cls.env.get('PATH', '')
        result = subprocess.run([CC, '-std=gnu11', '-O1', '-Wall', '-Wextra', '-Werror',
            '-I', str(ROOT/'recomp/host'), str(ROOT/'recomp/host/audio_mix.c'),
            str(ROOT/'tests/audio_mix_harness.c'), '-lpthread', '-lm', '-o', str(cls.exe)],
            capture_output=True, text=True, env=cls.env)
        if result.returncode:
            raise RuntimeError(result.stderr)

    def check_case(self, case):
        result = subprocess.run([str(self.exe), case], capture_output=True, text=True,
                                env=self.env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS', result.stdout)

    def test_frequency_volume_pan(self): self.check_case('signal')
    def test_cursors_looping_streaming(self): self.check_case('cursor')
    def test_formats_saturation_errors(self): self.check_case('formats')
    def test_concurrent_control_and_callback(self): self.check_case('threads')

if __name__ == '__main__': unittest.main()
