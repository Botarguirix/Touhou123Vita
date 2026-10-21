# Iteración 2.134: B aéreo 409 de Udonge conecta con su PAT ofensivo

El TSV diagnóstico ahora registra, para cada personaje, qué rutas candidatas alcanzan su acción y qué variante PAT seleccionó el runtime. Udonge alcanzaba 408/409/418, pero `409:0` no tiene ataque; el dato del PAT local confirma que `409:1` tiene caja ofensiva y 400 de daño. `action()` ahora elige la variante dañina de la acción aérea 409 usando el mismo selector provisional de PAT ya usado para 408/418.

La prueba natural por personaje conecta Udonge `409:1` al cuadro 12, con 400 de daño y separación registrada de 28 unidades. Tenshi y Cirno también conectan B por 409:1; la cobertura B natural sube de 15/20 a 18/20. Solo Reimu y Remilia quedan sin impacto B en este sondeo; el PAT de Remilia carece de 408/409. C normal permanece en 17/20; Udonge 418:1 sí se selecciona pero aún no conecta, junto con los faltantes C de Suika y Utsuho. El 623C especial de Suika se prueba por separado.

El runner ahora exige la regresión Udonge (acción 409, variante 1, cuadro 12, daño 400) y pasó Vita3K SDL schema46/600 frames, junto con los gates existentes de Suika, Remilia, sprites, objetos y escenarios. El reporte fresco y TSV están en [vita3k-result.json](../artifacts/vita3k-result.json) y [roster-bc-natural.tsv](../artifacts/roster-bc-natural.tsv).

- Autotest: [Touhou123Vita-udonge-409-auto.vpk](../artifacts/Touhou123Vita-udonge-409-auto.vpk), SHA-256 `DA7B2DA4B19DF9F21A98B1C19E28B90FFE8A44D3D951AB44227D7F40DD5A9363`.
- Interactivo: [Touhou123Vita-udonge-409-interactive.vpk](../artifacts/Touhou123Vita-udonge-409-interactive.vpk), SHA-256 `64AB8EA453C1A2183C3089C1F176BF73AE69E5CF8DAA99EE68CFB75350F44954`.
- Ambos incluyen el mismo `eboot.bin`, SHA-256 `5BBF5848B37925E074CF948AB32062B1437923ACE324620C30B97331BF055354`; Vita3K ejecutó el autotest.

La selección por mayor daño/cajas PAT sigue siendo provisional: demuestra que la ruta conecta con el dato local, no que el selector coincida bit a bit con el handler original en todos los estados. Falta recuperar los selectores originales, resolver los B de Reimu y las C normales de Udonge/Suika/Utsuho, y cotejar movimiento/defensa/replay contra el PE.
