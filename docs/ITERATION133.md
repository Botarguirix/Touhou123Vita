# Iteración 2.33: recursos auxiliares de escenarios en Vita3K

Fecha: 2026-10-17.

Los constructores originales exportados por Ghidra permitieron vincular estos CV2 con sus escenarios: `bg12` usa `tori1/2`; `bg33`, `0001/0002`; `bg36`, `tori1/2` y `clowd_l/s`; `bg37`, `tori1` y `clowd_l/s`; `bg38`, `clowd_l/s`. La nueva vista de recursos los carga desde los DAT externos y los presenta junto al catálogo de tiles. `bg34` mantiene sus vistas compuesta, auxiliares y mapa de colocación. Navegar cada grupo vuelve a cargar las texturas del stage correspondiente.

El auto-test ahora recorre los cinco grupos de auxiliares, guarda una captura para cada uno y regresa a `bg34`. VitaSDK compiló el VPK automático; Vita3K SDL aislado completó 600 frames con `schema=32`, `status=passed`, `stage_constructor_asset_mask=31`, BG34 30+30 tiles, 4 bitmaps/30 objetos, galería/roster 20/20, práctica y combate. Reporte: `artifacts/vita3k-result.json`; capturas: `artifacts/screenshots/stage-bg12-assets.bmp`, `stage-bg33-assets.bmp`, `stage-bg36-assets.bmp`, `stage-bg37-assets.bmp` y `stage-bg38-assets.bmp`.

VPK generado localmente: `artifacts/Touhou123Vita-stage-extra-audit.vpk`, SHA-256 `30affdcf6c377d6ba989a84f6c36f0601d5b2966f1198b9a9dcb78b852be7091`. DAT originales se mantienen externos al VPK.

Alcance: se prueba lectura/decodificación y presentación de las texturas en un catálogo, no su composición de combate. Las posiciones de BG12/33/36/37/38, movimiento de nubes, parallax, cámara, animación por callbacks, colisiones y clima aún no se reconstruyen. Las capturas con tiles parciales tampoco prueban que los huecos del manifest sean errores; hay que clasificarlos desde el constructor/runtime original. La auditoría está en [ITERATION132.md](ITERATION132.md) y [STAGE_RESOURCE_AUDIT.tsv](STAGE_RESOURCE_AUDIT.tsv).
