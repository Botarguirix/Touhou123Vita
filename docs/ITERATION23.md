# Iteración 1.19: siembra de 90 muestras al inicializar o cambiar estado

Esta revisión corrige la hipótesis de la iteración 1.18. El deque no queda vacío durante el combate: el constructor `0046c330` lo inicializa vacío, pero una ruta de inicialización del jugador llama a `0046d950`, que reconfigura la cola antes de empezar el flujo normal de updates.

## Evidencia del ejecutable 1.10a

- En `0046ba22–0046ba29`, después de limpiar los estados temporales con `0046cac0`, el código llama a `0046d950` sobre el jugador. `0046cac0` deja en cero `+0x774..+0x790` y el contador de transición `+0x7ac`.
- `0046d950` empaqueta la dirección y botones desde `+0x754..+0x768`, obtiene `Player+0x7b0` y pasa `0x5a` (90) junto con el puntero al word empaquetado a `0046d890`.
- El orden de shifts de `0046d950` permite reconstruir el byte bajo: cuatro flags de botón `+0x768,+0x764,+0x760,+0x75c` ocupan sus bits altos `D,C,B,A` (`0x80,0x40,0x20,0x10`); luego los signos de `verticalAxis` (`+0x758`) y `horizontalAxis` (`+0x754`) ocupan los cuatro bits bajos. Esto coincide con las máscaras de A/B/C/D y direcciones que consulta `0046cc90`. `0046d5d0` además empaqueta `+0x770` y `+0x76c` en los dos bits superiores del word (spellcard/change-card, según el layout de `InputInfo`); el matcher usa las máscaras del byte bajo.
- `0046d890` usa sus dos argumentos (cantidad y puntero al word), construye los rangos de la cola, llama a `0042bc40` sobre el rango existente y luego a `0046d050` para la operación de inserción por cantidad. Esto corresponde a reemplazar el contenido por 90 copias de la muestra actual. La secuencia de instrucciones está fijada en [player-input-window-seed.capstone.txt](../artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/input-state/player-input-window-seed.capstone.txt).
- El barrido lineal encuentra llamadas adicionales a `0046d950` justo antes de dispatches de acción/movimiento, por ejemplo `0048792a`, `0048794d`, `00487972` y las rutas de dash en `0048a...`. Esto indica que el juego resiembra el historial al inicializar y en varias transiciones, para que las muestras anteriores no se arrastren a otro estado. El listado completo está en `ring-range-callers.tsv`; los candidatos de ese listado deben validarse en función/contexto, aunque estos ejemplos aparecen inmediatamente antes de llamadas virtuales con el ID de acción.
- Con 90 muestras cargadas, el update `0046d5d0` añade la muestra del tick actual y expulsa la más antigua: el tamaño se conserva en 90. El matcher puede limitar la búsqueda al tramo reciente solicitado (15 o 20 ticks).

## Consecuencia para el port

La política de retención del ring y el byte bajo del formato ya quedan explicados por la inicialización y la resiembra. Aún no se porta el matcher: falta confirmar todas las rutas exactas de resiembra y derivar el tratamiento de neutral, diagonales, orientaciones y botón sostenido en todas las ramas de `0046cc90`. El gate Vita de 15 ticks sigue siendo aproximado. No hubo cambios de runtime ni VPK nuevo.

El siguiente trabajo es contrastar `0046d950` y `0046d5d0` bit por bit, modelar la operación de resiembra en un contrato host y comparar secuencias fijas contra los helpers originales y replays antes de sustituir el gate.
