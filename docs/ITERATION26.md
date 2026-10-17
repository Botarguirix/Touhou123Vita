# Iteración 1.22: matcher ARM integrado al combate

## Cambio

El matcher de movimientos C ya no queda como prototipo aislado. `Fight` mantiene dos rings de 90 muestras, los vuelve a sembrar al resetear y agrega cada entrada empaquetada por tick. El dash usa `NRNR` cuando mira a la derecha y `NLNL` cuando mira a la izquierda, con el límite de 15 muestras del caller original. Se retiró el gate anterior basado solo en dos bordes direccionales.

La traducción y la lógica de comparación están en [input.c](../src/input.c); el combate y su empaque de entrada están en [fight.c](../src/fight.c). El script de build Vita también incluye ahora el nuevo módulo.

## Diferencial x86/ARM

[test_input_arm_oracle.py](../tools/test_input_arm_oracle.py) compila el código con el compilador ARMv7 de VitaSDK, ejecuta ese ELF ARM en Unicorn y compara su retorno con `0046cc90` ejecutado como x86 desde `original/th123.exe` (SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`). Pasaron 401/401 vectores: 17 casos contractuales, 128 secuencias positivas generadas y 256 casos determinísticos de exploración. El mismo harness verifica el reset, la capacidad 90 y el wrap del ring. Reporte local: `artifacts/x86-arm-input-vectors.json`.

Reproducción: `python tools/test_input_arm_oracle.py` (requiere el `original/th123.exe` con ese hash, VitaSDK en `C:\vitasdk` y las dependencias Unicorn/pefile locales).

## Build y regresión Vita3K

- VPK automático creado: `artifacts/Touhou123Vita-matcher.vpk`, SHA-256 `e9be67a7dff4b3400a0bb52752589ad66bdbe356bde02a87df701e64f0ea0361`.
- Vita3K SDL terminó con `schema=13`, `status=passed` y 600 frames; el probe de dash pasó con 3 dashes. Se cargaron 31 DAT, 137 texturas, los 20 PAT y 20 tarjetas; también se comprobaron 30+30 tiles y 4+30 recursos auxiliares de `bg34`. Hubo un impacto B y uno C en la secuencia automática.
- El probe de límites ahora acepta 12 muestras neutrales entre toques y rechaza 13, como dicta el historial de 15 muestras al incluir la secuencia `N-R-N-R`.

## Pendiente para paridad del juego

La entrada de combate sigue siendo una traducción del control simplificado de esta demo. Falta capturar estados reales producidos por `0046d5d0`, aplicar bindings configurados y neutralización de ejes, contrastar movimientos contra replays y comparar por frame con la versión PC. Tampoco se recuperaron aún locks/cancelaciones, habilidades y mecánicas completas por personaje. Esta iteración mejora el dash y el matcher; no demuestra que el motor esté decompilado ni que el combate sea completo.
