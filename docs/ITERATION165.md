# Iteración 2.65: semántica de selección e input del replay

## Bytes de personaje

La función `0x42d560` indexa registros a stride `0x50` y lee los dos primeros bytes de cada registro. Copia esos bytes a las dos configuraciones que la rutina de inicio consume para crear los jugadores. En la misma ruta de inicio, el estado de replay (`0x43ced0 == 2`) llama a `0x42d560` antes de inicializar los combatientes. Por tanto, los bytes de offset `+0` y `+1` son los IDs de personaje de los dos canales.

En el replay Sanae local, las parejas decodificadas son `(15,16)`, `(15,17)` y `(15,0)`. Coinciden con la tabla de 20 entradas del runtime (`15=sanae`, `16=chirno`, `17=meirin`, `0=reimu`) y con una secuencia de tres combates de historia. Esta correlación apoya la asignación del byte a `character_id`; los bytes restantes del canal no se renombraron.

## Secuencia de input

El vector final `uint16` está en `record+0x3c`. La ruta de grabación de modo `1` llama `0x42cce0`, que agrega el estado global de input `[0x85eb58]` a ese vector mediante `0x42c500`. El lector `0x45bc50` consulta el siguiente valor sin avanzar; `0x42a3a0` consume el word actual y actualiza el cursor/contador. En modo `2`, `0x45fb...` contrasta el valor esperado con `[0x85eb58]` antes de avanzar. Además, `0x42a410` consume un valor y separa su máscara baja `word & 0x03ff` de los bits altos que activa como inputs de IDs `0x3b`, `0x3c`, `0x3d`, `0x3f`, `0x40` y `0x41`.

`tools/replay_layout.py` ahora llama `character_id` al primer byte y ofrece `decode_input_word()` para exponer los bits observados sin inventar nombres de botones. El inspector añade una decodificación de muestra al JSON. El parser no interpreta todavía los campos restantes, la cadencia con que se consumen los words, ni pausas/repeticiones; falta comparar una ejecución frame-stepped del replay con el juego original.

## Verificación

- El replay suministrado se decodifica con IDs `(15,16)`, `(15,17)`, `(15,0)` y consume exactamente 67,881 bytes.
- Las pruebas sintéticas verifican IDs, límites del word, máscara de diez bits y mapeo de los seis flags altos, además de truncación y límites estructurales.
- Estos cambios afectan herramientas de análisis Python, no el runtime Vita. No se recompiló el VPK ni se afirma paridad temporal completa.

Siguiente: preparar un runner de referencia que pause el juego en el primer input divergente, y fijar con observación frame-stepped la relación entre un word, una muestra del estado `[0x85eb58]` y el tick de combate antes de integrar replay al VPK.
