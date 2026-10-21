# Iteración 2.35: scroll de las nubes BG36

Fecha: 2026-10-17.

El desensamblado hash-pinned identifica los dos objetos móviles del constructor BG36: `clowd_l` (`0x85b02c`) y `clowd_s` (`0x85b008`). El constructor `00475eb0` inicializa `this+0x68=-400` y `this+0x6c=-300`. El callback `00476260` resta `1.5` y `1.0` por tick respectivamente; si el primer valor baja de `-1200`, lo cambia a `800`, y si el segundo baja de `-800`, también lo cambia a `800`. El método de render `004757a0` aplica el primer campo al transform de `clowd_l` (`+0x1d0`) con desplazamiento vertical base `-750`; aplica el segundo a `clowd_s` (`+0x2b8`) con desplazamiento vertical `-320`. Los anclajes del constructor producen `clowd_l=(0,0)` y `clowd_s=(320,480)`, así que la vista muestra las traslaciones locales previas a cámara; no afirma que sean todavía coordenadas de pantalla.

Porté el estado y la actualización a `src/stage.c`/`include/t123/stage.h`, añadí pruebas C de inicio, pasos, límites y wrap en `tests/stage_tests.c`, y una prueba Python que contrasta constantes, instrucciones y hash del PE original. La vista BG36 dibuja las dos texturas móviles dentro de un diagrama de transformaciones y reporta las coordenadas resultantes. El runner reproduce el número de updates del reporte y exige que ambas coordenadas coincidan; el gate pasó. El target C `stage_contract` quedó agregado a CTest; `stage_tests.c` compiló con VitaSDK, pero no se ejecutó como prueba host en esta sesión. El build VitaSDK también compiló `stage.c`.

Vita3K SDL aislado pasó 600 frames con `schema=34` y `stage_bg36_scroll_seen=1`. En la captura registrada, siete updates producen `clowd_l x=-410` y `clowd_s x=13` (incluida su ancla X=320), según el contrato portado. Se conservaron las pruebas de los cinco grupos auxiliares, BG34 30+30 tiles, 4 bitmaps/30 objetos, roster/tarjetas/recursos 20/20 y práctica/combate. La suite Python pasó 54/54.

VPK: `artifacts/Touhou123Vita-bg36-cloud-scroll.vpk`, 100,306 bytes, SHA-256 `a3eeb31bdba139506776fc61eb90f9ce74ac3e15d675ff362d67cbc1b17211c6`. Evidencia: `artifacts/vita3k-result.json` y `artifacts/screenshots/stage-bg36-layout.bmp`.

Alcance abierto: falta recuperar la transformación de cámara que coloca estos objetos en la escena final, el orden de capas y la paridad de encuadre/píxeles con el PC. Las otras nubes/parallax, composición de los otros escenarios, colisiones, clima y mecánicas siguen pendientes; el objetivo integral continúa abierto.
