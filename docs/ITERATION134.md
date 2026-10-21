# Iteración 2.34: plano de rejilla y anclajes de BG36

Fecha: 2026-10-17.

El visor ya no deja BG36 únicamente como una lámina de miniaturas. Añadí una vista de inspección que coloca los tiles usando el contrato del loader original `0046fe40`: seis columnas por cinco filas, tamaño nominal de 256, `x = 700 - 256*col` y `y = 0x56 + 0x35c - 256*row` (946 para la primera fila). La orientación y separación del plano provienen del PE de referencia `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.

Un diagrama aparte muestra los anclajes que el constructor de BG36 pasa a `00406c60`: `tori1` y `tori2` en `(320,480)`, `clowd_l` en `(0,0)` y `clowd_s` en `(320,480)`. El esquema evita presentar esos puntos como posiciones finales de blit: aún no se han recuperado el origen de dibujo de cada bitmap ni la transformación de cámara. El método virtual de actualización `00476260` también está identificado; sus offsets con wrap aún no se aplican al renderer. La rejilla muestra los recursos presentes (25/30 en el DAT actual); los cinco nombres faltantes siguen sin clasificación concluyente.

La prueba automática avanzó a schema33, recorre la nueva vista BG36 y después vuelve a BG34. Vita3K SDL aislado completó 600 frames con `status=passed`, `stage_bg36_layout=1`, máscara de auxiliares `31`, BG34 con 30+30 tiles, 4 bitmaps y 30 sprites `objectFa`; roster PAT, tarjetas e imágenes 20/20; práctica, combate y las regresiones previas aprobadas. El reporte fresco está en `artifacts/vita3k-result.json` y la captura en `artifacts/screenshots/stage-bg36-layout.bmp`. La suite Python pasó 52/52.

VPK reproducible de esta iteración: `artifacts/Touhou123Vita-bg36-layout.vpk`, 99,864 bytes, SHA-256 `e1b03dfdf267f662c711d7dd69575f0f0f823406473561be2a9377674906cfed`. Contiene el programa de prueba; los DAT del usuario siguen fuera del paquete.

La vista verifica geometría de recursos y anclajes constructor, no paridad visual del escenario, cámara, movimiento de nubes, colisión, clima ni mecánicas de combate. BG36 queda como el primer plano auxiliar compuesto a partir de evidencia estática; quedan pendientes las posiciones efectivas de los otros escenarios y la clasificación de los huecos.
