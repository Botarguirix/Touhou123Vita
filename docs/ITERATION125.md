# Iteración 2.25: respuesta completa del resolver de dos Players

Fecha: 2026-10-17.

## Resultado

La sonda `tools/x86_player_pair_hit_probe.py` ya ejecuta la ruta original `0x47c770` sobre dos Players de Remilia creados por el constructor x86. Atacante acción 320/seq.0/frame3 y defensor acción 321/seq.0/frame0 producen geometría superpuesta desde `0x47a5b0`; el dispatcher registra `CollisionType=1`, suma el combo y `0x47b11c–0x47b123` resta 200 HP (1000→800).

El resolver también completa la selección de reacción del defensor, cambia a acción 50/seq.0 y obtiene tres poses del PAT auténtico. Fue necesario poner el vtable de `PlayerRemilia` (`0x85D284`) después del constructor base para que el dispatch virtual de `initializeAction` llegue a `0x59AAA0`. La fixture de lookup enruta por ID de acción hacia los datos PAT reales. El administrador global de efectos aún es un stub observable: recibe solicitud `0xC9`, pero no instancia ni dibuja el efecto real.

## Verificación

- `python -m unittest tests.test_x86_player_pair_hit_probe tests.test_remilia_412_spawn_probe -v`: 6/6 aprobadas.
- El VPK interactivo se recompiló con `tools/build-vita-native.ps1` y se probó en una instancia aislada de Vita3K SDL: schema31, 600 frames, estado `passed`.
- SHA-256 de `artifacts/Touhou123Vita-current.vpk`: `7682b3131861735ddb50ff1999c5d8e6c08aaf812040586a43545b2aadce1bf6`; coincide con `artifacts/vita3k-result.json`.
- El auto-test confirma PAT, sprites y tarjetas 20/20; escenario BG34; A natural 20/20; B 14/20 y C 15/20. Estas últimas rutas son diagnósticos, no paridad total del roster.
- `cmake --build`/CTest no se ejecutó: `cmake` no está disponible en PATH en este entorno.

## Próximo paso

Conectar el resolver a una actualización/input x86 reproducible con selección natural de poses y posición, sustituir el stub del administrador de efectos y comparar el resultado por frame con una pelea/replay de PC. El límite de esta iteración es una fixture de dos Players; no demuestra combate completo ni cambia el runtime ARM más allá de regenerar el VPK vigente.
