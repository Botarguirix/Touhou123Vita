# Iteración 1.11: mapa de colocación BG34 legible

## Cambio

La página 4 del visor BG34 dibuja las dos rejillas de 30 tiles y las cuatro imágenes estáticas usando las coordenadas recuperadas del constructor. Se ajustó la escala de cada bitmap para que quepa en su celda nominal de 256 unidades, y la escala global para encajar las dos rejillas en el panel. La secuencia `objectFa` usa el frame `floor(tick/2)` dentro del ciclo de 60 ticks. El mapa sirve para inspeccionar posiciones de carga; la cámara y la proyección del juego siguen provisionales.

La evidencia Ghidra indica que `+0x3a0` y `+0xe8` forman parte de arreglos/instancias y no representan coordenadas X. Las cuatro coordenadas estáticas observadas son (700,187), (350,230), (350,480) y centro del bitmap para `0004`. Aún hay que recuperar la transformación aplicada por `00429440` antes de tratar la captura como composición final.

## Validación

Vita3K SDL completó 600 frames con estado `passed`: escenario `bg34`, página 3, tiles 30/30 en cada rejilla, imágenes estáticas 4/4, sprites de objeto 30/30, animación tick 47/frame 23, roster y tarjetas 20/20, cero fallos de textura, práctica y combate con impactos B/C.

VPK interactivo para revisión: `artifacts/Touhou123Vita-bg34-layout.vpk`, 81,870 bytes, SHA-256 `044262752b6c761b0b38554063b4f3439baf3f841575d91fff5452be87f6ee06`.

VPK automático validado: `artifacts/Touhou123Vita-bg34-layout-auto.vpk`, 82,036 bytes, SHA-256 `d341c69694488fcdba190278296b018b20631e72b832ed8d35d2ee3a259bb80f`. Reporte: `artifacts/vita3k-result.json`; captura: `artifacts/screenshots/stage-layout.bmp`.

## Pendiente

La vista de mapa es una reconstrucción de posiciones estáticas con escala de inspección, no la escena del combate. Recuperar la proyección/cámara y reglas de parallax/dibujo, luego comparar con el ejecutable PC. La lógica completa de escenario, colisiones y los demás IDs siguen pendientes.
