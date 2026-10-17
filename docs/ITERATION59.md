# Iteración 1.56: Reimu carta 107 / acción 565

Fecha: 2026-10-17.

La tercera ruta de skill de Reimu ya llega a combate con recursos PAT reales. La carta terrestre 107 despacha a acción 565. Su secuencia 0 usa las imágenes 12/13/48 durante 2/2/60 frames (64 en total); al pasar a secuencia 1, imagen 47, la caja PAT aplica 450 de daño. La variante de mayor daño de secuencia 4 no se usa como primer caso porque el paso de secuencias intermedias exige transiciones que aún no están reconstruidas.

Vita3K SDL observó el impacto al entrar a secuencia 1: 63 updates posteriores a la llamada que activa la skill, 64 contando esa actualización, y daño exacto 450. El runner exige carta 107→565, imagen inicial 12, secuencia de impacto 1, imagen 47, daño 450 y ese timing. `tests/fight_tests.c` también verifica el despacho con datos mínimos. La validación de 102→540 (1100 en seq.3, update 48) y 103→560 (vuelo/impacto/aterrizaje) sigue pasando.

Build y regresión:

- VPK `artifacts/reimu-card107-565.vpk`, SHA-256 `d80d3172b0cf4650ffa304c2d8efc6c590a2a673acca434846d8fd110610c38c`.
- Vita3K SDL, schema27/600 frames, `passed`.
- Roster PAT/textura 20/20, BG34 con 30 tiles y 30 assets de objetos, dash 35 impactos directos, B/C y fixtures de la iteración anterior.
- El tiempo coincide con la suma de frames PAT y el advancement de secuencias implementado. Sigue faltando una traza de combate PC end-to-end para comparar el handler/inputs original; mano/costo/consumo, cancelaciones y efectos externos tampoco están completos.
