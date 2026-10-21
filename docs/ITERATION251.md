# Iteración 2.151: dash Suika 200→418 avanza hasta PAT ofensivo

Se extendió la cadena de Iteración 2.150 en el mismo Player construido por `0x609d40`: luego del dispatch natural determinista `200→418`, se completa el cleanup original `0x46cac0` y se invoca el update virtual de Suika (`0x5ee620`). Dieciséis updates originales avanzan la animación sin errores ni accesos inválidos.

El timeline observado es action 418/seq.0/pose.0 al tick 1, seq.1/pose.0 al tick 8 y seq.2/pose.0 al tick 16. En tick 16, el frame PAT original reporta daño 900 y una caja ofensiva. Esto enlaza entrada C+NRNR → handler → setter → cleanup → update PAT en un único objeto. El combate sigue sin ser end-to-end: captura de KeyManager, suelo/escenario y callbacks se controlan, no hay rival ni resolver de colisión en esta corrida, y no es playback de replay.

La prueba focalizada pasa 1/1 y verifica además la transición al frame ofensivo; las tres sondas Suika relacionadas pasan 3/3. No se modificó el runtime Vita ni se generó VPK nuevo.

Evidencia: [reporte](../artifacts/x86-suika-constructed-handler.json), [sonda](../tools/x86_suika_constructed_handler_probe.py), [regresión](../tests/test_x86_suika_constructed_handler_probe.py). Siguiente: conectar el tick de PAT con dos Players y el resolver PE `0x47c770`, conservando el mismo despacho de entrada, para observar contacto/daño real y comparar las condiciones de posición.
