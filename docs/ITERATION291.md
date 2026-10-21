# Iteración 2.191: orden de capas BG36 según el renderer PE

La secuencia del renderer `0x4757a0` fija la composición: dibuja `clowd_l` y `clowd_s`, después llama al renderer base `0x46f380` para la retícula de tiles y termina con los dos torii. `draw_battle_bg36` ahora conserva ese orden: cielo, nubes, tiles, torii. La prueba verifica la secuencia de llamadas del PE y el orden en el render Vita. También se confirmó que el constructor base pone los tres deltas de tinte en cero y que el update BG36 identificado mueve solo los dos torii; no se inventó una animación/tinte de nube.

El VPK autotest mide 108,432 bytes, SHA-256 `983ef4d0b520b4dbbd613817da3718730f4254fd638d4211b8615e5b59659f7f`. Vita3K SDL pasó 600 frames, `regression_gate=1`, base BG36 25/25 presentes (máscara `477888511`), auxiliares 4/4 y captura confirmada; el hash del reporte fresco coincide. El VPK interactivo mide 108,266 bytes, SHA-256 `f9c74b09a3776adf4f5425b10cae7dbff8f8c7f087f180f6d2c1fecb25771542`. Ambos pasan la validación estructural sin errores ni advertencias.

Contratos unittest: BG36 3/3 (incluye orden del renderer PE y orden del port) y BG37/BG38 4/4. La captura [fight-bg36.bmp](../artifacts/screenshots/fight-bg36.bmp) deja la nube detrás de los edificios y los torii delante de la retícula; falta comparación sincronizada contra PC para confirmar paridad visual. El porcentaje global permanece en 27%, pues BG36 aún carece de selección interactiva completa y validación contra referencia.

Siguiente: conectar BG36 al selector de escenario de combate, capturar el mismo punto en el juego original y el port, medir diferencias de cámara/scroll, y después implementar el siguiente renderer con orden PE trazado.
