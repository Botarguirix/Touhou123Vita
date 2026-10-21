# Iteración 2.155: el downed loop de Suika persiste 300 ticks

Se amplió la corrida post-impacto del oráculo de Suika 97 de 60 a 300 ticks, conservando el temporizador común PE `0x46a330` y el update virtual `0x5ee620`. Después de que termina el hitstop, cada tick también despacha `handleInputs` (`0x609dc0`) del defensor, con su Player construido y entrada neutral. La ejecución enlaza con el resolver de la iteración anterior: daño 1200, HP de fixture 2000→800, reacción 74 y hitstop 10→0.

Desde el tick10, el defensor pasa a action97; la ruta PAT autenticada es `0→1→3→0→1→2`, con `setSequence(3)` en tick17 y entrada al seq.2 de loop mode 1 en tick43. Al tick300 continúa action97/seq.2, Y=500 (piso controlado del harness), velocidad vertical 0, sin error de input/update ni accesos inválidos. `handleInputs` neutral no emite setters de acción ni secuencia adicionales. La lógica del Player y su handler neutral no bastan para salir del loop; la búsqueda se acota al estado/callback PE de combate que coordina round/recuperación. No prueba que el juego completo carezca de esa transición.

El desensamblado del dispatcher confirma que action97 usa el handler `0x485115` a través del switch genérico `0x483f40`. Su rama de secuencias 1/2 reduce la velocidad vertical y consulta el gate original `0x487ea0`; en contacto descendente con suelo corrige Y y llama el setter virtual de secuencia. La traza dinámica fija el retorno de ese setter en `0x4851e7` (tick17, solicitud seq.3 desde seq.1). Cuando ya está en seq.2 loop con vy=0, no se repite el gate de aterrizaje y ni el handler neutral ni este update solicitan levantamiento.

Diagnóstico separado: después de guardar los 300 ticks auténticos, se cambia solo el byte `loop_mode` del nodo seq.2 de 1 a 0 y se corre el PE 60 ticks más con input neutral. Recorre nodos PAT (seq.3→0→1…) pero sigue en action97 y no emite setters de acción. Esta mutación del fixture no representa una configuración del juego ni prueba la transición natural; sí descarta que apagar únicamente el bit de loop baste en este grafo. Sigue faltando el estado/caller externo que inicie el wake-up.

Una corrida de diagnóstico previa se detuvo en tick182 con fetch inválido `0xf1a`; no se reprodujo al habilitar captura de traza desde tick175. La corrida repetida completó 300 ticks y el test ahora fija ese horizonte.

Verificación focal: 7/7 tests (Suika construido, matcher, rama 418 y cuatro pruebas del factory compartido), incluidos 300 ticks de `handleInputs` neutral; `py_compile` y `git diff --check`. Sin cambios al runtime Vita ni VPK.

Evidencia: [reporte](../artifacts/x86-suika-constructed-handler.json), [sonda](../tools/x86_suika_constructed_handler_probe.py), [test](../tests/test_x86_suika_constructed_handler_probe.py). Próximo: rastrear el manager/callback de round que solicita la salida de action97 y repetir con stage/input/replay PE conectados; después validar levantamiento, recuperación y KO antes de portar reglas adicionales.
