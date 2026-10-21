# Iteración 2.105: el callback Story y los flags usan el mismo objeto de input

La inspección del PE original 2009 (SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`) cierra una relación que antes estaba abierta:

- `0x43cec0` devuelve `[0x85ec98]`.
- La configuración de input en `0x4281a2` pasa ese objeto a `0x42d6b0`, que escribe su byte `+0xf0` a partir de la presencia de fuentes en el estado configurado.
- El callback Story `0x47ee10`, cuando `0x43ced0()` devuelve 2, vuelve a obtener `[0x85ec98]` mediante `0x43cec0` y entrega exactamente ese objeto a `0x42a410`.

Por tanto, el `+0xf0` escrito por esa ruta sí pertenece al mismo objeto que el callback Story usa como `this` del decoder. Esto no determina su valor efectivo: depende de las dos fuentes preparadas por el backend y de la ruta de configuración elegida.

Además, `0x43d8e0` guarda su primer argumento en `[0x85ec10]` (selector del manager) y el segundo en `[0x85ec08]` (estado que consulta el callback mediante `0x43ced0`). En el bloque `0x426de2–0x426de6` se empujan `2` y luego `6`, por lo que una ruta de código solicita modo 6/estado 2. El selector de modo 6 construye el manager Story y el estado 2 habilita el decoder dentro de `0x47ee10`.

Esto forma una ruta estática compatible con playback Story: modo 6 → manager Story → estado 2 → decoder sobre el objeto de input configurado. Falta demostrar que la rama `0x426de6` es efectivamente la que toma el replay Sanae, determinar si el objeto trae una o dos fuentes activas y medir cuántas llamadas ocurren por frame. No se conectó el playback al runtime Vita.

La prueba `tests/test_replay_manager_selection_probe.py` ahora comprueba la identidad del objeto compartido, los dos stores del setter y el bloque que solicita `(6,2)`. La sonda regenera `artifacts/kernel/replay-manager-selection-original-2009.json`.
