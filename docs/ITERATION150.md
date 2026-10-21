# Iteración 2.50: rasterización afín de los slots BG33

Fecha: 2026-10-17.

Se añadió `soft2d_draw_texture_quad`, que rasteriza un quad afín/paralelogramo por inversión de base y muestreo UV, con clipping al framebuffer y rechazo de quads degenerados/no paralelogramos. La página BG33 obtiene los cuatro vértices por slot de `t123_bg33_project_slot_quad` —geometría base del constructor, traslación/wrap, viewport/cámara y escala del PE— y ahora usa el rasterizador en los 30 slots. El gate sólo marca una ranura después de que la primitiva acepta el quad.

Para que la galería local sea legible, la matriz se calcula en una referencia de cámara cero y después se encaja en el mapa diagnóstico. No equivale al estado vivo del manager ni a la composición final durante la pelea. La prueba guest comprueba los cuatro vértices del slot fuente 0, el wrap inferior y exige `stage_bg33_quad_draws=30` junto con la máscara `0x3fffffff`.

Verificación: VitaSDK compiló; Vita3K SDL aislado pasó 600 frames con `schema=46`, `regression_gate=1`, viewport/quad contracts=1, BG33 layout/scroll capturados, 30 slots y 30 quads dibujados. Suite Python: 80/80. Captura: `artifacts/screenshots/stage-bg33-scroll.bmp`. VPK `artifacts/Touhou123Vita-latest.vpk`, 106,902 bytes, SHA-256 `acd7394bc493454e9983eed84c92c0c50080fb9570df68db8c5533e79e9b90f7`.
