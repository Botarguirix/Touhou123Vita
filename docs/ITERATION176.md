# Iteración 2.76: recursos auxiliares BG36 visibles y export de renderer

La página de diagnóstico BG36 ahora itera las cuatro imágenes auxiliares cargadas por el constructor (`tori1`, `tori2`, `clowd_l`, `clowd_s`); antes solo mostraba los dos torii. Conserva el scroll medido para los torii y deja explícito que todavía no conocemos el anclaje de las nubes ni la cámara completa, por lo que esta vista no afirma una composición equivalente a PC.

Se añadió `tools/export_stage_renderer_disasm.py`, que verifica el SHA-256 del PE local y exporta instrucciones de los métodos BG36/BG37/BG38 a `artifacts/kernel/<sha>/stage-layout/renderers-disasm.tsv`. La extracción produjo 1,667 instrucciones sobre el ejecutable fijado. Este material permite avanzar de manera reproducible el análisis de las draw calls, las transformaciones y la cámara de escenario.

VPK interactivo recompilado: 93,279 bytes, SHA-256 `911a5205bb25cf646f70cfda8126f797f27c608498f30c9e8ac5302ff0202060`. VPK automático: 93,445 bytes, SHA-256 `b68de072479793007f921bc39b472b6167976700ceb216fb89157d0a53d41078`. Vita3K SDL completó 600 cuadros/schema46 con gate pasado y captura BG36 fresca; suite Python completa 100/100.

Pendiente para paridad: modelar posición/tamaño exactos de las nubes, la cámara y composición de capas, integrar todos los fondos al combate y cubrir sus mecánicas en secuencias jugables. Este paso amplía la inspección de recursos; no cierra un escenario completo.


**Actualización (Iteración 2.77):** el anclaje relativo de las dos nubes ya se recuperó: ambas reciben +0x44/+0x48, con pivotes de constructor distintos. Sigue pendiente el mapeo de cámara/escala de combate. Véase [ITERATION177.md](ITERATION177.md).
