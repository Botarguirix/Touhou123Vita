# Iteración 2.40: catálogo x86 completo y captura real de BG36

Fecha: 2026-10-17.

La tabla de `FUN_00470e40` del PE TH123 incluye el case `0x23`; ese camino llama el constructor genérico `FUN_00477550(0x23, 0x56, 1)`, que usa el modo de rejilla 5×6 del loader. El catálogo local saltaba BG35 entre BG34 y BG36. Se agregó BG35, con 25 IDs ahora alineados con los casos soportados (0–6, 10–18 y 30–38). BG35 no aparece como carpeta bajo `data/background` en los manifiestos locales TH123 ni TH105, así que el visor muestra un aviso cuando no decodifica tiles en vez de presentar el área negra sin contexto. Esto prueba despacho del PE y ausencia en los DAT inspeccionados, no que todos los 25 IDs tengan contenido utilizable.

La primera ejecución tras añadir BG35 mostró una debilidad en el gate anterior: el archivo llamado `stage-bg36-layout.bmp` se capturaba por número de frame y mostraba BG35 vacío. Ahora la secuencia visita BG36/capa 2 y el runner captura el esquema sólo cuando el nombre seleccionado es BG36 y la capa realmente es 2; el reporte schema37 exige esa captura fresca. Los captures de auxiliares BG36/37/38 también se disparan por nombre de escenario y vista de assets.

Build con VitaSDK: `artifacts/Touhou123Vita-stage-catalog.vpk`, 102,428 bytes, SHA-256 `0975ffc38dc9ead584e0a6787595cc0361552cf2122e4e97bb29f02b54cf3d29`. Vita3K SDL aislado pasó schema37 en 600 frames. BG12 capturado en capa 2; BG36 layout/capture=1, siete ticks, offsets grandes/pequeños `-410`/`13`; máscara de auxiliares `31`; BG34 base/upper 30+30, cuatro bitmaps y 30 objetos; roster 20/20; gates actuales de práctica y combate pasan. La captura [stage-bg36-layout.bmp](../artifacts/screenshots/stage-bg36-layout.bmp) ahora contiene la rejilla y el esquema de nubes, aunque no representa todavía la composición ni la cámara del juego.

La auditoría reproducible ahora lista 25 IDs en [STAGE_RESOURCE_AUDIT.tsv](STAGE_RESOURCE_AUDIT.tsv). Suite Python completa pendiente de ejecutar para esta iteración. No se ha probado hardware PS Vita; cámara/composición, recursos ausentes, clima, colisiones de escenario y paridad completa siguen pendientes.
