# Iteración 2.42: offsets de los segmentos animados BG02

Fecha: 2026-10-17.

La lectura del renderer original `FUN_004716d0` (PE SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`) completa el contrato parcial de BG02. El callback de update `FUN_00473f40` incrementa `Background+0x64` una vez. El renderer escoge `frame=(counter/3)%16`, calcula el primer índice `frame*3` y usa sus tres entradas consecutivas. El constructor `FUN_00471c50` carga esas entradas como `left/aNN`, `center/bNN`, `right/cNN`.

Los offsets locales que el renderer suma mediante `FUN_00406ee0` son `left=(-332,-472)`, `center=(Background+0x44, Background+0x48)` y `right=(312,-472)`. Los valores 312, -332 y -472 se leyeron directamente del PE en `0x85ab24`, `0x85ab2c` y `0x85ab30`. Luego el callback aplica la transformación de escena compartida. Por eso ya está fijado el layout local, pero aún no la proyección final de cámara ni el aspecto compuesto del escenario dentro de una pelea.

El helper C y el visor registran esos offsets; la prueba de host contrasta el ciclo, las instrucciones del renderer y los floats del PE. El gate de Vita3K schema40 requiere el contrato, captura la página y decodifica los 48 CV2 de BG02.

Build automática: `artifacts/Touhou123Vita-bg02-layout.vpk`, 104,518 bytes, SHA-256 `a067312031adbcaf0cfdee15dcbcb511f342c9ae11c854e1c365367143872ea0`. Vita3K SDL aislado pasó 600 frames; captura [stage-bg02-segment.bmp](../artifacts/screenshots/stage-bg02-segment.bmp). La suite Python completa pasó 71/71 tras actualizar una expectativa estática de BG12 para reconocer que BG02 también conserva sus tiles base. No se ha ejecutado una prueba en PS Vita física.

Siguiente paso: recuperar las transformaciones de `Background+0x44/+0x48` durante la selección/transición de escenario y el camino de cámara/render que convierte estos offsets locales a pantalla; después contrastar la composición y animación contra captura o replay del juego PC. BG04, BG16, BG35 y el resto de capas aún requieren su propia reconstrucción.
