# Iteración 2.81: centro automático de cámara derivado del PE

Se amplió `tools/x86_stage_camera_oracle.py` para capturar los cinco resultados de `FUN_00428e20`: centro X/Y, zoom y los dos anclajes usados por el renderer. Las corridas confirmaron los límites horizontales automáticos `clamp((x0+x1)/2, 320/zoom, 960)` y el seguimiento vertical `max(420, min(y0,y1))`. También se ejecutaron los flags de override `+0x2c/+0x2d`: seleccionan los valores fijos `+0x20/+0x24`. El override manual se deja fuera de la función pura del core porque depende del estado/flags de la instancia.

`T123StageCameraTarget` ahora incluye centro X/Y además de distancia/zoom. El contrato automatizado compara centro y zoom en cuatro pares, y cubre además a ambos jugadores elevados. Vita3K SDL pasó 600 cuadros, schema46, `regression_gate=1` y el contrato de cámara ampliado. La suite Python completa pasó 104/104.

VPK automático probado: `artifacts/Touhou123Vita-camera-center-auto.vpk`, SHA-256 `cce2367b0d3395ed231d282653dc243c4934c6354ac5560e8a6368038f0ceed7`. VPK interactivo: `artifacts/Touhou123Vita-camera-center.vpk`, SHA-256 `cb31b432498e11329a7ec295d8b962fe61c957bfab3da8a19ff0e82eb3bef8c0`. Ambos comparten el `eboot.bin` SHA-256 `db21aba28ff3234c379f06a2ba95df3eb9e5194f5bec612d92fd58153a43dc48`.

Esto sigue siendo cálculo de objetivos y prueba aislada del core, no cámara funcional conectada a la pelea. Falta portar flags de override, reproducir el ciclo por frame de `FUN_00429040`, resolver límites/movimiento temporal del centro y alimentar el transform de personajes/escenario durante el combate. Ver [ITERATION180.md](ITERATION180.md) y `tests/test_stage_camera_oracle.py`.
