# Iteración 1.16: orientación del selector de patrones confirmada

El campo usado por `0046cc90` en `this+0x104` se puede nombrar con el layout público de SokuLib: `AnimationObject::direction` está en ese offset, después de `position`, `speed` y `gravity` ([AnimationObject.hpp](https://github.com/SokuDev/SokuLib/blob/master/src/AnimationObject.hpp#L17-L25)). La rutina compara el byte como signed: positivo elige la tabla de tokens de `0x883b08`; cero/negativo, la de `0x883adc`.

Las dos tablas coinciden para `N/R/L/D` y A/B/C/X, pero remapean `4` y `6` al sentido opuesto y cambian las diagonales. Esto explica la numeración relativa al cambiar hacia dónde mira el jugador. `Player.hpp` confirma el layout de `commandInputBuffer` en `0x7b0`, `movementCombination` en `0x7c4` y `commandCombination` en `0x7c8` ([Player.hpp](https://github.com/SokuDev/SokuLib/blob/master/src/Player.hpp#L124-L141)).

No hubo cambio de runtime ni build nuevo. El siguiente problema abierto es el ciclo de vida del deque: cómo se inicializa el conteo que ve el matcher, cómo `0046d78f` desplaza la ventana y cuándo se descartan/repueblan muestras. Ver el análisis local de ring en [INPUT_STATE.md](INPUT_STATE.md) y los dumps Capstone en `artifacts/kernel/<sha>/input-state/`.
