# Iteración 2.49: BG33 con las 30 ranuras del callback

Fecha: 2026-10-17.

Al reconstruir `FUN_00406c60` → `FUN_00406d30` → `FUN_00406ea0` se confirmó que el ancla de cada tile ya está codificada en los vértices base `+0x80..+0xac`, y que el constructor base inicializa `Background+0x44/+0x48` a cero. Por tanto, el callback `0x473620` no vuelve a pasar el ancla: suma `x=+0x44` y `y=+0x48-counter`, con `+0x400` cuando el índice fuente está envuelto. El helper C que antes devolvía anclas duplicadas se corrigió para devolver únicamente `x=0` y esa traslación de scroll.

El visor BG33 ahora tiene una cuarta página que dibuja los 30 slots con la selección de las 24 fuentes y el wrap derivado del PE. La página es una visualización del layout local remapeada a un origen diagnóstico; aún no aplica los transforms de matriz viewport/cámara al escenario de combate. La autoprueba captura `stage-bg33-scroll.bmp` y exige la máscara completa `0x3fffffff`, 24 tiles cargados, el layout anterior y el contrato viewport. Se corrigió la secuencia automatizada con frames de liberación entre pulsaciones para visitar también layouts BG36 y volver a BG34.

Verificación: VitaSDK compiló; Vita3K SDL aislado pasó 600 frames con `schema=44`, `regression_gate=1`, viewport=1, layout/scroll/capturas BG33=1, `stage_bg33_slots=1073741823`, 24 tiles y seis updates/counter=6. Suite Python: 80/80. Captura: `artifacts/screenshots/stage-bg33-scroll.bmp`. VPK `artifacts/Touhou123Vita-latest.vpk`, 105,074 bytes, SHA-256 `291629337de0787795a8ef6c9177beb0b3ed8408763cff46579af684d2262534`.
