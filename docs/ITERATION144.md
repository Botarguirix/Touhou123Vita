# Iteración 2.44: ciclo de actualización BG33

Fecha: 2026-10-17.

La tabla virtual BG33 en `0x85ae44` apunta al slot 1 `0x473610` y al slot 4 `0x473620`. La función de update original contiene exactamente `mov eax,[ecx+0x64]; add eax,1; and eax,0x3ff; mov [ecx+0x64],eax; ret`. El renderer slot 4 lee ese mismo campo. El puerto ahora aplica el wrap de diez bits para stage ID 33, lo ejecuta en cada update de BG33 seleccionado y muestra el contador/fase de 256 ticks en la vista del layout.

Se añadieron contratos de host para 255→256 y 1023→0, y un oracle local al PE hash-pinned que verifica los slots y bytes originales. La autoprueba de Vita3K recorre la página de composición BG33 y valida su layout/captura, 24 tiles y el contador frente al número de updates. En la corrida de 600 frames BG33 recibió cuatro updates y acabó en contador 4.

Verificación: 74 pruebas Python aprobadas; VitaSDK compiló el VPK; Vita3K SDL aislado pasó 600 frames con `schema=42`, `regression_gate=1`, `stage_bg33_layout=1`, `stage_bg33_layout_capture=1`, `stage_bg33_tiles=24`, `stage_bg33_updates=4`, `stage_bg33_counter=4`. VPK: `artifacts/Touhou123Vita-latest.vpk`, 104,121 bytes, SHA-256 `10e2dad560d4c703b2c5228ea3c9e32f36b1e8b51f7b9bdaba7f0c6d33017e92`.

El ciclo del contador es exacto, pero la composición local anterior todavía no mueve los tiles. El renderer x86 recorre 30 slots desde una tabla de 24 sprites, rota índices según `counter>>8`, agrega una corrección de wrap y transforma coordenadas con el estado global de cámara. La siguiente tarea es derivar esa fórmula slot por slot y recuperar el transform compartido antes de representar el desplazamiento durante el combate. No se ha probado una PS Vita física.
