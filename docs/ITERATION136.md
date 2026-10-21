# Iteración 2.36: clasificación verificable de recursos de escenario

Fecha: 2026-10-17.

La auditoría anterior trataba las 30 celdas del visor como nombres requeridos por cada stage y agrupaba todos los auxiliares. Eso confundía convenciones del viewer con contrato del juego. `tools/audit_stage_resources.py` ahora reporta nombres base presentes/faltantes, auxiliares candidatos, bitmaps, sprites y CV2 todavía sin consumidor asociado como clases separadas. No clasifica por sí sola una celda faltante como defecto del juego.

La regeneración sobre el manifiesto local de TH123 clasifica las 24 IDs que exponía el visor en esa iteración, 14 carpetas fuente y cero archivos CV2 adicionales sin asignar entre las carpetas presentes tras reconocer candidatos auxiliares. BG34 presenta sus 30 tiles base y los 64 auxiliares esperados por el viewer (30 tiles superiores, cuatro bitmaps y 30 sprites `objectFa`). BG12 y BG33 tienen sus dos auxiliares candidatos; BG36 4/4, BG37 3/4 y BG38 2/4. Los nombres base convencionales están presentes: BG10 29/30, BG11 y BG14 30/30, BG12 25/30, BG13 24/30, BG17 21/30, BG30–32 30/30, BG33 24/30, BG34 30/30, BG36/37 25/30 y BG38 11/30. Estos denominadores describen el naming convencional, no prueban que el juego requiera todas las celdas.

Pruebas de `tests/test_audit_stage_resources.py`: 2/2. El VPK, el runtime de combate y la validación Vita3K no cambian: esta iteración mejora la evidencia de cobertura y evita guiar el trabajo con falsos faltantes. El JSON regenerado es local (`artifacts/stage-resource-audit.json`); la tabla versionable está en [STAGE_RESOURCE_AUDIT.tsv](STAGE_RESOURCE_AUDIT.tsv).

Siguiente paso: usar la tabla de referencias x86/Ghidra de constructores de stage y llamadas de carga para determinar nombres, capas y posiciones reales de BG12/BG33/BG36–38. Después integrar una escena con transformaciones derivadas del PE y una captura Vita3K contrastable, en vez de extrapolar el grid genérico.
