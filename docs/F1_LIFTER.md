# F1.2: lifter mínimo y modelo x87 de estado explícito

Fecha: 21 de octubre de 2026. Segundo entregable de F1 en el [roadmap de recompilación](ROADMAP_RECOMP.md).

**Resultado:** el código x86 original traducido a C reproduce el oráculo del kernel de animación en 2 048 de 2 048 casos. El modelo x87 coincide bit a bit con la FPU real del host en 12 configuraciones del control word. Además, 55 funciones x87 reales del juego coinciden con el original en 5 control words.

```powershell
python recomp/discover.py                       # una vez: límites de función
python recomp/lift_functions.py 438c60 464ae0 --output <dir>/out.c
python -m unittest tests.test_recomp_lift -v     # ~20 s
```

## Piezas

| Ruta | Contenido |
|---|---|
| `recomp/runtime/guest.h`, `guest.c` | Estado de CPU guest, memoria guest de 32 bits, cargador PE, dispatch de llamadas, intercepciones, `guest_fault`, flags enteros y modelo x87 |
| `recomp/lift/lifter.py` | Traductor x86 → C: una función C por función guest, una etiqueta por instrucción |
| `recomp/lift_functions.py` | CLI; los límites de función salen de `discovery.json` (F1.1) |
| `recomp/verify/differential.py` | Runner diferencial: los mismos estados iniciales en Unicorn y en el C traducido |
| `recomp/tests/anim_harness.c`, `diff_runner.c`, `x87_native_test.c` | Programas de prueba escritos a mano; no contienen código del juego |
| `tests/test_recomp_lift.py` | Las tres puertas de equivalencia |

El C generado se escribe en directorios temporales o en `artifacts/` y **nunca se versiona**.

## Diseño del runtime

- **Registros** como uniones de 32/16/8 bits (`c->eax.d`, `.w`, `.b.l`, `.b.h`). **Flags** calculados en el momento (CF, ZF, SF, OF, PF) por helpers de cada operación y tamaño, siguiendo la semántica de Intel, incluidos `inc`/`dec`, que preservan CF, y desplazamientos con contador 0.
- **Memoria guest** de 32 bits: `G(a) = guest_base + a`. En el host se reservan 4 GB y se comprometen las regiones usadas. La imagen se carga en su base original (no tiene relocaciones). Los accesos usan `memcpy` (sin problemas de alineación ni de aliasing).
- **Llamadas:** `call` apila la dirección de retorno real en la pila guest y llama a la función C. `ret n` hace `esp += 4 + n`. Las llamadas indirectas y virtuales pasan por `guest_call`, que busca primero las intercepciones del host y después la tabla ordenada de funciones traducidas. Las importaciones van por `guest_call_import(slot_IAT)`.
- **Control de flujo:** `goto` dentro de la función, tail calls hacia otras funciones y los switch de F1.1 como `switch` sobre el valor leído de la tabla original. Un switch heurístico o un salto sin resolver produce `guest_fault`.
- **Instrucción no soportada:** produce `guest_fault(dirección, texto)` y nunca se omite en silencio. En el lote de 62 funciones de esta fase quedaron tres: `cvttsd2si` (SSE2 en `_ftol2`) y dos `shld` del CRT, en rutas que no se ejecutan en las pruebas.

## Modelo x87 de estado explícito

Lo decidido con la tarea T1 ([X87_MODE.md](X87_MODE.md)): el juego cambia de precisión y de redondeo en tiempo de ejecución, así que el control word forma parte del estado guest (`c->fpu.cw`) y se aplica en **cada** operación, no a través del modo de la FPU del host.

- **PC=24:** la operación se calcula en `double` y se redondea a 24 bits de significando con el RC del guest, **conservando el exponente** (sin desnormalizar ni desbordar a infinito, igual que un registro x87). El doble redondeo 53 → 24 es inocuo para + − × ÷ √ con operandos de precisión float (53 ≥ 2·24+2), y en los modos dirigidos porque la rejilla de 24 bits está contenida en la de 53.
- **PC=53:** se calcula en `double`.
- **PC=64:** se calcula en `long double` en hosts x86. **En ARM (Vita) baja a 53 bits**: desviación conocida.
- **RC distinto del más cercano:** se aplica con `fesetround` solo alrededor de la operación. Con RC al más cercano no se toca el entorno del host.
- **Almacenamiento** a float o double y `fist` usan el RC del guest. `fisttp` trunca.
- **Decodificación por opcode y ModRM**, no por mnemónico, para no heredar la confusión `fsub`/`fsubr` y `fdiv`/`fdivr` de las formas `DC`/`DE`.

## Validación

| Puerta | Oráculo | Resultado |
|---|---|---|
| Kernel de animación (`0x438c60` + métodos virtuales `0x464ae0`, `0x464b50`, `0x464b70`, `0x464bf0`) | `tools/x86_animation_oracle.py` (código original en Unicorn) | **2 048 / 2 048 filas idénticas**, 1 128 refrescos gráficos interceptados en ambos, pila equilibrada |
| Modelo x87 contra la FPU real | Inline asm sobre la x87 del host, PC {24, 53, 64} × RC {cercano, abajo, arriba, cero}: aritmética, operaciones encadenadas, `fsqrt`, `frndint`, `fst` m32/m64, `fistp` | **0 discrepancias en 2,72 millones de comprobaciones**. Control: en los mismos datos PC cambia 876 845 resultados y RC 464 439, y un runtime que ignora PC falla con 95 536 discrepancias |
| Funciones x87 reales | Unicorn, 57 funciones hoja seleccionadas automáticamente (sin llamadas, ejecutan x87 y no fallan con estados aleatorios), 25 casos por función y CW | **55 / 57 coinciden** (registros, esp, profundidad y valor de la pila x87, 1 KB de memoria) en los 5 CW `0x027F`, `0x037F`, `0x007F`, `0x0E7F` y `0x067F` |

Las dos funciones excluidas de la última puerta, con su motivo:

- `0x827800` (exponencial del CRT, `f2xm1` + `fscale`): Unicorn/QEMU calcula los trascendentes en `double`, así que no sirve de oráculo. Con PC=64 devuelve lo mismo que con PC=53.
- `0x82d6a3`: rutina del CRT que provoca excepciones de coma flotante para fijar los flags pegajosos. Esos flags no se modelan (ver abajo).

### Errores encontrados y corregidos durante la validación

- `fcom`/`fcomp` con operando en memoria o `st(i)` hacían un pop de más.
- PC=24 desnormalizaba resultados que en un registro x87 no se desnormalizan.
- `f2xm1` perdía bits por cancelación (`exp2(x) − 1`); ahora usa `expm1`.
- En el runner, globales de un caso contaminaban el siguiente, y en Unicorn la caché de traducción ejecutaba un stub de la función del caso anterior. Los dos quedaron resueltos (restauración de la imagen y un stub por función).

## Desviaciones conocidas (pendientes o aceptadas)

| Aspecto | Estado |
|---|---|
| PC=64 en ARM | Se calcula a 53 bits. Hay que medir si algún camino del juego (no del CRT) usa PC=64; T1 solo lo encontró en el CRT |
| Rango de exponente extendido con PC=53/64 | No se modela fuera del rango de `double` |
| Payload y selección de NaN | x87 propaga el NaN de mayor significando; aquí sale el del host. Las pruebas evitan entradas NaN |
| Flags pegajosos de excepción (PE, UE, OE, ZE) | No se modelan. El juego solo lee C0–C3 (`test ah`) tras `fnstsw`. IE se marca en desbordamiento de pila e indefinidos |
| Trascendentes (`fsin`, `fcos`, `fpatan`, `fyl2x`, `f2xm1`, `fptan`) | Usan libm y no son bit-exactos con el microcódigo x87. El CRT que los usa se reemplazará por código nativo |
| SSE2 (`cvttsd2si` en `_ftol2`) | Sin soporte. El CRT elige esa ruta según `__sse2_available` (`0x8a1148`); hay que decidir la política al integrar el CRT |
| `shld`/`shrd`, divisiones de 8 y 16 bits, `rol`/`ror` de 8 y 16 bits | Sin soporte; producen `guest_fault` |

## Siguiente

F1.3: **cobertura de traducción del ejecutable completo**. Traducir las 6 414 funciones, compilarlas en PC y medir cuántas instrucciones caen en `guest_fault` por tipo. Ampliar el lifter hasta que el código del juego (sin contar el CRT que se va a reemplazar) quede sin faltas, y extender el runner diferencial a lotes grandes de funciones hoja y no hoja con intercepciones.
