# Iteración 2.41: cobertura de escenarios heredados y recursos de constructor

Fecha: 2026-10-17.

El inventario inicial de la Iteración 2.32 contaba sólo el manifiesto TH123, aunque `t123_resources_open` abre primero `th105a.dat`/`th105b.dat` y luego `th123a/b/c.dat`; `t123_resource_read` resuelve desde TH123 hacia TH105 como fallback. Al unir los manifiestos, los 25 IDs del dispatcher tienen directorios fuente para 24: BG00–06, BG10–18 y BG30–34/BG36–38. BG35 continúa sin directorio. De los nombres base convencionales, BG00–02 y BG06 tienen 30/30 en TH105; BG03 27/30, BG04 30/30, BG05 24/30; BG10–18 combinan recursos TH105 y TH123. Estas cuentas son sólo presencia por nombre, no prueba de celdas consumidas por la composición.

La procedencia ahora queda en la columna `source_archives` de [STAGE_RESOURCE_AUDIT.tsv](STAGE_RESOURCE_AUDIT.tsv); `tools/audit_stage_resources.py` acepta varios manifiestos y mantiene de forma separada rutas esperadas y archivos adicionales. Pruebas 3/3 de auditoría, incluidas prioridad/procedencia, BG35 ausente y clases auxiliares.

El cruce con constructores Ghidra fijó tres grupos que antes aparecían como CV2 sobrantes: BG02 `FUN_00471c50` llama al cargador de base y a 16 sprites por cada ruta `left/a00..15`, `center/b00..15` y `right/c00..15` (48 en total); BG04 `FUN_00472230` carga `cloud2`; BG16 `FUN_00473270` carga `0001..0004` con pivotes `(128,128)`, `(128,128)`, `(0,64)` y `(32,32)`. El auditor clasifica esos nombres como referencias de constructor. Todavía falta recuperar los callbacks de render/update y mostrar todos esos recursos en el visor con su composición real; no se infieren posiciones ni movimiento a partir de los pivotes de carga.

Comando reproducible:

```powershell
python tools/audit_stage_resources.py artifacts/th105-resource-manifest.tsv artifacts/th123-resource-manifest.tsv --output docs/STAGE_RESOURCE_AUDIT.tsv --json artifacts/stage-resource-audit.json
```

No cambia el VPK. Sigue vigente la build schema37 de Iteración 2.40; este análisis corrige la evidencia del inventario, no demuestra paridad de fondo, cámara, clima ni colisiones.
