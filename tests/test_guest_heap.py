"""Pruebas del allocator real, sin modificar support.c ni guest.c.

Dos defectos pendientes (expectedFailure, no se disimulan como aprobados):
1. Proceso nuevo: heap_alloc(UINT32_MAX,0) devuelve 0x01000010, heap_used=16.
   round_up desborda a cero; debería devolver 0.
2. Proceso nuevo: heap_alloc(0xfffffff0,0) causa una violacion de acceso: end
   desborda y carve escribe una cabecera en memoria aun no comprometida.
   Reproduccion sin crash: heap_alloc(1,0), heap_alloc(0xfffffff0,0) devuelve
   0x01000030 sin avanzar heap_used=32; heap_alloc(16,0) repite 0x01000030.
   El harness usa esa precarga para mostrar el solapamiento sin causar un crash.
   No escribir el tamaño anunciado por estas reservas.
Propuesta para Claude: comprobar size contra el presupuesto antes de round_up;
calcular HDR+capacity/end en uint64_t o comparar contra espacio restante.

La partición de un payload de 4 MiB en 1 MiB deja 3 MiB MENOS 16 bytes de cabecera,
no 3 MiB exactos. La prueba aleatoria informa bytes solicitados vivos frente a
heap_used/heap_top: la diferencia mezcla huecos, slack de clases y cabeceras;
no representa únicamente fragmentación externa.

Resultado medido sobre 5b01083: 9 pruebas en 9.236s,
OK (expected failures=2). La semilla 0x5EED1234 completó 100000 operaciones:
31071 alloc, 30983 free, 37946 realloc, cero reservas fallidas; 88 bloques vivos,
1878047 bytes solicitados, heap_top=26206704 (0x018FE1F0), heap_used=9429488.
Huecos+slack+cabeceras=7551441 bytes antes de liberar los supervivientes.
No se modificó el allocator ni se probaron cargas multihilo en esta tarea.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
CC=shutil.which('gcc') or r'C:\msys64\ucrt64\bin\gcc.exe'

@unittest.skipUnless(Path(CC).exists(),'Falta GCC host')
class GuestHeapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.exe=Path(cls.tmp.name)/'heap.exe';cls.env=os.environ.copy()
        cls.env['PATH']=str(Path(CC).parent)+os.pathsep+cls.env.get('PATH','')
        # guest.c contiene un parametro sin uso preexistente; no se modifica.
        cmd=[CC,'-std=gnu11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-I',str(ROOT/'recomp/host'),
             '-I',str(ROOT/'recomp/runtime'),str(ROOT/'tests/heap_harness.c'),str(ROOT/'tests/heap_stubs.c'),
             str(ROOT/'recomp/host/support.c'),str(ROOT/'recomp/runtime/guest.c'),'-lpthread','-lm','-o',str(cls.exe)]
        r=subprocess.run(cmd,capture_output=True,text=True,env=cls.env)
        if r.returncode:raise RuntimeError(r.stderr)
    def run_case(self,name):
        r=subprocess.run([str(self.exe),name],cwd=self.tmp.name,capture_output=True,text=True,env=self.env,timeout=60)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('PASS heap '+name,r.stdout);return r.stdout
    def test_alignment_requested_sizes_and_zeroing(self):self.run_case('alignment')
    def test_large_and_small_reuse(self):self.run_case('reuse')
    def test_large_split_accounts_for_header(self):self.run_case('split')
    def test_coalesce_both_neighbours_and_reverse_order(self):self.run_case('coalesce')
    def test_realloc_grow_shrink_preserves_and_zeroes(self):self.run_case('realloc')
    def test_exhaustion_keeps_live_data_and_failed_realloc(self):self.run_case('exhaustion')
    def test_seeded_100000_operations_no_overlap_or_data_loss(self):
        text=self.run_case('random');row=json.loads(next(x for x in text.splitlines() if x.startswith('{')))
        self.assertEqual(row['operations'],100000)
        self.assertEqual(row['allocations']+row['frees']+row['reallocations']+row['failed_requests'],100000)
        self.assertLessEqual(row['live_bytes'],row['heap_used'])
        print('heap random:',json.dumps(row,sort_keys=True))
    @unittest.expectedFailure
    def test_known_round_up_overflow_must_reject_uint32_max(self):self.run_case('oversize-round')
    @unittest.expectedFailure
    def test_known_carve_end_overflow_must_reject_huge_capacity(self):self.run_case('oversize-end')

if __name__=='__main__':unittest.main()
