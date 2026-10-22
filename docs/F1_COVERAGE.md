# F1.3: traducción del ejecutable completo

Fecha: 21 de octubre de 2026. Tercer entregable de F1 en el [roadmap de recompilación](ROADMAP_RECOMP.md).

**Resultado:** las 6 406 funciones de `th123.exe` se traducen a C (104 MB en 69 unidades), compilan y enlazan en un solo programa. **El código del juego no tiene ninguna instrucción sin soporte.** Lo que queda sin soporte son 856 instrucciones SSE2 de rutinas matemáticas del CRT, que no se ejecutan por la política de `cpuid` descrita abajo.

```powershell
python recomp/discover.py                 # ~2 min
python recomp/lift_all.py --compile       # ~1,5 min de traducción + ~3 min de gcc -O1 en paralelo
python -m unittest tests.test_recomp_discover tests.test_recomp_lift tests.test_recomp_instructions -v
```

Las salidas (`gen/*.c`, `faults.json`, `coverage.json` y el ejecutable de prueba) quedan en `artifacts/recomp/<sha>/gen/` y no se versionan.

## Cifras

| Medida | Antes de F1.3 | Ahora |
|---|---|---|
| Funciones | 6 414 | 6 406 (algunos huérfanos pasaron a formar parte de su función) |
| Cobertura de `.text` no-padding | 99,40 % | **99,48 %** |
| Switch sin tope fiable (todo el binario) | 80 | 48 |
| Switch sin tope fiable en el juego | 21 | **2** |
| Saltos indirectos sin resolver | 9 | 2 |
| Instrucciones sin soporte en el juego | 118 (sin contar `int3`: 46) | **0** |
| Instrucciones sin soporte en CRT y librerías | 1 013 | 856, todas SSE2 salvo un `mov cs, [m]` (que también es `#UD` en hardware) |
| Trampas (`int3`, `hlt`, `ud2`) alcanzables | — | 72 en el juego y 26 en librerías; se traducen como fallo visible, igual que en el original |
| Compilación del programa completo | — | 69 unidades, 180 s con `-O1` en paralelo, ejecutable host de 26 MB que enlaza las 6 406 funciones |

La frontera juego/librerías es `0x81F000`: a partir de ahí están el CRT de MSVC, zlib, libpng y vorbis (ver [PE_INVENTORY.md](PE_INVENTORY.md)).

## Descubrimiento: topes de switch por flujo de datos

Las funciones enormes de los personajes (por ejemplo `0x4bd430`, con 19 549 instrucciones, o `0x765ab0`, con 28 595) guardan el tope del switch en un registro preservado (`cmp eax, ebp`). Ese registro se carga con constantes **distintas** en regiones distintas de la misma función. Se añadieron dos análisis sobre el grafo de control completo de la función, ejecutados después de explorarla:

1. **Constante que llega por todos los caminos** (`_reaching_constant`): desde el `cmp`, se recorren los predecesores reales hasta la definición del registro. Se acepta si todos los caminos lo definen con la misma constante, directamente (`mov`, `xor r,r`) o a través de copias y `lea r, [otro + k]`. Resolvió 19 switch (`flow:ebp`, `flow:ebx`, `flow:edi`).
2. **Comparación en otro bloque** (`_guarding_cmp`): cuando el `cmp idx, imm` está en otro bloque que salta al switch, quizá varias instrucciones neutras para los flags después. Resolvió 9 (`flow:cmp`).

Si una tabla resuelta aporta destinos nuevos, la exploración continúa desde ellos y el proceso se repite. Siguen sin tope fiable en el juego `0x4cfc80` y `0x4cfdaa`, ambos en `0x4bd430`: `edi` llega con valores distintos por caminos distintos. El lifter los traduce como `switch` sobre el valor real de la tabla: si llega un caso no descubierto, el resultado es `guest_fault` y nunca un salto silencioso.

## Instrucciones añadidas

| Instrucción | Notas |
|---|---|
| `xadd` (con y sin `lock`) | La forma de memoria es atómica de verdad (`__atomic_fetch_add`), porque el juego usa hilos |
| `imul r/m8` | `ax = al × src` con CF/OF |
| `rcl`/`rcr`; `rol`/`ror` de 8/16/32 bits | Con las reglas de cuenta de Intel (módulo tamaño+1 para las de acarreo) |
| `shld`/`shrd` | Con cuenta inmediata o en `cl` |
| `bt`/`bts`/`btr`/`btc` | Con desplazamiento en registro sobre memoria, que direcciona una cadena de bits con signo |
| `scas`/`cmps` con `rep`/`repe`/`repne`; `xlatb` | Con DF=0 (DF=1 → `guest_fault`) |
| `pushfd`/`popfd` | CF, PF, ZF, SF, DF, OF e ID; AF no se modela |
| `cpuid` | Ver la política abajo |
| `mov r/m16, sreg` | Selectores fijos de Windows en modo usuario (cs `0x1B`, ds/es/ss `0x23`, fs `0x3B`, gs 0) |
| `fprem1`, `fnstenv`/`fldenv`, `fnsave`/`frstor` | Entorno de 28 bytes en modo protegido de 32 bits; etiquetas solo válida/vacía |
| Switch heurísticos o pendientes | Antes eran una falta; ahora se traducen a un `switch` con caso por defecto `guest_fault` |

### Política de `cpuid`: el CRT usa sus rutas x87

`cpuid` anuncia un Pentium Pro con FPU, TSC, CX8 y CMOV, **sin MMX/SSE/SSE2**. El CRT decide en su arranque `__sse2_available` (`0x8a1148`) y con eso sus rutinas matemáticas y `_ftol2` toman la ruta x87, que ya está validada bit a bit. El código SSE2 queda traducido como `guest_fault` y no se ejecuta. Esto también evita un problema en Vita, que no tiene SSE. Si una prueba futura lo necesitara, habría que implementar SSE2 escalar; no hace falta para el juego.

## Validación

| Prueba | Resultado |
|---|---|
| `tests/test_recomp_instructions.py`: 12 fragmentos x86 ensamblados a mano, ejecutados en Unicorn y como C traducido (200 estados aleatorios cada uno; registros, flags materializados con `setcc`, memoria) | **Todos coinciden**. No usa `th123.exe` |
| `fprem1` contra la FPU real del host (`x87_native_test.c`) | 0 discrepancias. Unicorn **no** sirve de oráculo para `fprem1`: redondea mal el cociente con divisor negativo (`621,447 rem −122,139` da −111,385 en vez de 10,753) |
| Puertas de F1.2 con el descubrimiento y el lifter nuevos | Kernel de animación 2 048/2 048, modelo x87 0 discrepancias en 2,74 M comprobaciones, 55/57 funciones x87 reales (las mismas 2 exclusiones) |

`cpuid` y la lectura de registros de segmento no se comparan con Unicorn a propósito: el runtime devuelve valores fijos elegidos.

## Qué no demuestra todavía

- Que el programa **arranque**: el `main` de prueba solo registra la tabla de funciones. Ejecutar `WinMain` necesita las capas de plataforma (KERNEL32, USER32, D3D9, DirectSound, DirectInput, Winsock), que son F2.
- Equivalencia de funciones no hoja: el runner diferencial cubre funciones hoja y fragmentos. Las funciones con llamadas se validarán con intercepciones de importaciones.
- Rendimiento: `-O1` en x86-64. El tamaño y el tiempo en ARM/Vita están por medir (F3).

## Siguiente

F2.0: arranque en PC host. El código del CRT de arranque (`0x8218b2`) y `WinMain` se ejecutan traducidos sobre una primera capa Win32 mínima: heap, TLS, archivos, tiempo y `GetModuleHandle`/`GetProcAddress` para el CRT. Se registra hasta dónde llega antes de necesitar D3D9.
