# Iteración 2.109: inventario de escrituras de los dos slots de input

La sonda inspecciona ahora las ocho entradas de la tabla `0x43e248` leída por `0x43dee0` y sigue cada rama hasta sus escrituras directas a `0x8602ac/+0x44` y `0x8602cc/+0x44`. En el PE original 2009 (SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`), el inventario es:

| Selector | Configuración directa de fuentes |
|---|---|
| 1, 2 y 8 | `0x85ef20` y null: un slot presente |
| 3 | `0x85ef20` y `0x85f70c`: dos slots presentes |
| 4 y 5 | punteros al manager `+0x1f0` y `+0x1f8` |
| 6 y 7 | ruta común sin escritura directa: conserva lo preparado antes |

La inicialización común observada en `0x43ccf0` también deja `0x85ef20/null`. El escritor `0x42d6b0` calcula `+0xf0` del objeto `0x85ec98` con la presencia de los dos slots de la estructura global en `0x860288`: bit 0 si `+0x24` es no nulo y bit 1 si `+0x44` es no nulo. Por eso, el selector 6 no basta para fijar `f0`: el resultado depende del estado previo efectivo. Esta sonda es estática; todavía no demuestra el orden de llamadas en la sesión de replay Sanae ni el estado cargado en vivo.

La prueba focalizada `tests/test_replay_manager_selection_probe.py` verifica las ocho entradas y los efectos de slots de cada rama. No cambian runtime ni VPK. Reporte actualizado: `artifacts/kernel/replay-manager-selection-original-2009.json`.

Siguiente: encontrar el caller real de `0x43dee0`/`0x43ccf0`, reconstruir la secuencia que antecede al setter Story `(6,2)` y, si no basta el control estático, capturar los globals en una sesión del ejecutable antes de conectar el playback Vita.
