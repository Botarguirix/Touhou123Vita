# Iteración 2.142: gate PE de aterrizaje explica transición de Suika 418

La traza del update original identifica `0x487ea0` como predicado de límite vertical: compara la posición Y actual con el resultado del helper de suelo `0x4397f0`, exige velocidad vertical no positiva y que `Player+0x4c4` esté despejado. El caller de `0x5f49d0` usa ese retorno para entrar a `0x60362f`; el vtable setter en `0x603644` solicita secuencia 5. La observación ejecutada en tick 27 confirma secuencia 2/pose 5, velocidad `-0.5`, retorno verdadero y setter desde `0x603646` con secuencia destino 5. En tick 26 la velocidad era `0.0` y la rama aún no cambió.

El probe `x86_suika_action_setter_probe.py` registra entrada/salida del gate y el artefacto se actualizó en [x86-suika-418-sequence.json](../artifacts/x86-suika-418-sequence.json). La regresión verifica el tick, callsite, velocidad, retorno y setter destino. Suite focalizada 1/1 y Python completa 119/119.

Alcance: el PE original y el PAT local están fijados por hashes, pero la fixture mantiene Y=0 y establece la acción 418 directamente. Esto demuestra el gate y la transición de recuperación bajo los campos suministrados; no demuestra un salto natural, input de dash, colisión ni combate completo. No cambia el runtime Vita ni se reconstruye VPK.

Siguiente: alimentar el límite vertical real del stage y un estado inicial de física derivado del constructor/update, observar el cruce de suelo sin fijar Y, y recuperar el productor natural de 418 desde input; después contrastar Suika, Udonge y Utsuho antes de modelar transiciones en `fight.c`.
