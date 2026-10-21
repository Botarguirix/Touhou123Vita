# recomp: recompilación estática de th123.exe

Pipeline de la [ruta de recompilación](../docs/ROADMAP_RECOMP.md): `th123.exe` (x86, del usuario) → análisis → C generado → build para PC host y para Vita.

| Ruta | Estado | Contenido |
|---|---|---|
| `analysis/image.py` | F1 | Vista del PE (o de una imagen sintética) por direcciones virtuales |
| `analysis/discover.py` | F1 | Descubrimiento de funciones por descenso recursivo, tablas de switch de MSVC y funciones noreturn |
| `discover.py` | F1 | CLI: ejecuta el descubrimiento sobre `original/th123.exe` |
| `lift/lifter.py`, `lift_functions.py` | F1.2 | Traductor x86 → C y su CLI ([F1_LIFTER.md](../docs/F1_LIFTER.md)) |
| `runtime/` | F1.2 | Runtime guest: CPU, memoria, dispatch y modelo x87 de estado explícito |
| `verify/differential.py`, `tests/*.c` | F1.2 | Runner diferencial contra Unicorn y programas de prueba |

```powershell
python recomp/discover.py
python recomp/lift_functions.py 438c60 --output artifacts/recomp/out.c
python -m unittest tests.test_recomp_discover tests.test_recomp_lift -v
```

Las salidas (`discovery.json`, `unexplained.tsv`) se escriben en `artifacts/recomp/<sha>/` y **no se versionan**: contienen direcciones y estructura del binario comercial. El código C generado tampoco se versionará.
