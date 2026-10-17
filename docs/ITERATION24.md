# Iteración 1.20: matcher x86 ejecutado con ring sintético

Estado de esa iteración. El matcher C y su comparación ARM/x86 avanzaron en [ITERATION26.md](ITERATION26.md).

La función original `0046cc90` ya se puede ejecutar en Unicorn con fixtures explícitas. El harness verifica el SHA-256 de `original/th123.exe` (`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`), configura el stack de la llamada thiscall y construye el deque con 90 muestras en bloques de 8. El código x86 del matcher y del lookup interno corre directamente; solo se neutralizan los asserts/stack-cookie externos.

Resultado actual: 17/17 vectores coinciden con el resultado esperado. Incluye `NRNR`, `NLNL` y `DD` en ambas orientaciones; `N09`, `N07`, `N08`; el token especial de abajo en `2N2A`; una secuencia direccional alterada que debe rechazarse; el límite de historial; y `X` con A/B/C/D. Los vectores detallados están en `artifacts/x86-motion-vectors.json` y CSV, ignorados por Git.

Herramienta reproducible: [x86_motion_oracle.py](../tools/x86_motion_oracle.py). La búsqueda acotada de combinaciones de nibbles encontró, por ejemplo, secuencias sintéticas `[0,8,6]`, `[0,8,5]` y `[0,8,4]` para `N09`, `N07` y `N08`; esto descubre el contrato del matcher, pero no significa que cada word corresponda ya a una combinación validada de botones físicos. El byte y la cadencia de input todavía deben contrastarse contra el productor real `0046d5d0`, neutralización de ejes y replays.

## Límites de esta prueba

- Los fixtures construyen el layout del deque a partir de `0042cf90` y `0046cc90`; no llaman a la inicialización completa del jugador ni prueban todos los caminos de resiembra.
- `X` se prueba con los botones empaquetados A/B/C/D; su búsqueda de binding pasa por `0042a950`, que corre como x86 usando un objeto de key-map sintético. Esta fixture valida el retorno por tecla, pero todavía no lee bindings reales de configuración.
- Esto es validación dinámica del helper x86, no aún comparación del matcher C/Vita contra x86. El gate de dash del runtime no se ha sustituido y el VPK no cambió.

## Siguiente

El helper C inicial está en `src/input.c` y sus contratos en `tests/input_tests.c`; compila con VitaSDK, pero aún no se ejecuta como test host ni se ha probado diferencialmente en todos los 17 casos. Siguiente: ejecutar tests host, conectar el matcher C a cada vector x86 y a muestras del productor/replays, cerrar diagonales y sostenido; integrar al dispatch solo al demostrar paridad y después correr un VPK fresco en Vita3K.
