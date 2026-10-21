# Iteración 2.197: límites de mundo para combate PAT

El combate con PAT aún restringía X a 35–605, el rango de la demo inicial de 640 unidades. La cámara reconstruida del PE admite un mundo de 1280 unidades y seguía calculando zoom/traslación para ese espacio, pero la lógica de movimiento impedía recorrer su mitad derecha. El movimiento con PAT y el integrador aéreo en cuartos de unidad usan ahora límites 40–1240. No se modificaron posiciones iniciales, velocidad, colisiones entre personajes ni offsets de sprite.

Evidencia original: PE SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`, función `0x463550`; en `0x4635fc` carga float 40 de `0x8596b8` y en `0x463619` carga float 1240 de `0x85a25c`. Esa rama está condicionada por Player+0x571. El harness PhysicsOracle ahora puede activar esa rama con dos consultas de colisión sustituidas por respuestas de una arena plana sin obstáculos. La integración y los clamps se ejecutan en el código x86 original: 42−4.5 → 40, 1238+4.5 → 1240, 700+4.5 → 704.5. Esto no reconstruye colisión de escenarios especiales ni prueba la política de flags de todos los modos.

`arena_tests` ejercita el combate PAT real del port con datos mínimos de caminar/reposo: cruza X=605, alcanza 1240, mueve la cámara más allá de 640 y mantiene la pared derecha dentro del viewport; también confirma la pared izquierda en 40. Está registrado como `arena_world_contract` en CMake. Se compiló/ejecutó nativamente con GCC UCRT; pasó. Las pruebas Python de física y BG36/BG37/BG38 pasaron 11/11.

La suite nativa general `fight_tests` sigue fallando en el fixture Suika 530: una segunda llamada a bind reinicia el nivel y las posiciones configuradas antes. Se verificó el mismo fallo con los límites anteriores y los actuales (exit 1, misma aserción). No se alteraron sus aserciones para declarar verde la suite. Logs locales: `artifacts/fight-baseline-tests.log`, `artifacts/fight-arena-tests.log`.

Vita3K SDL pasó schema46/600 y gate 1 con los chequeos existentes, incluidos tiles/auxiliares BG36, bandas laterales y habilidades. Ese recorrido sigue usando posiciones de sonda: la prueba específica del alcance 40–1240 es la nativa, no una afirmación de que el recorrido Vita3K lo haya atravesado.

- Interactivo: 108,677 bytes; SHA-256 `fe586a273f3a138ec1d6cfe78365d37eed68579ed24f183d5d201f0e63176219`.
- Auto: 108,843 bytes; SHA-256 `f71dec3b22d7060bbe99f1bab49ae38e0608f22f7c54697d4cbdf44b1aba642f`.
- Ambos pasan check_vpk.py sin errores/advertencias.

Pendiente: recuperar el reset normal de posiciones iniciales, comparar suelo/sprites con PC y revisar las cajas PAT (el resolvedor aún aplica media escala mientras el dibujo usa unidades completas). El fallback sin patrones conserva sus límites de demo; no se presenta como física original. Avance global conservado en 27%.
