# Iteración 1.9: recursos auxiliares BG34 decodificados

## Referencia de Ghidra y DAT

La función `00474f70` del ejecutable 1.10a (SHA-256 fijado en la iteración 1.8) carga dos rejillas de 30 tiles, cuatro bitmaps estáticos `0001.bmp`–`0004.bmp` y 30 sprites `object/objectFa000.bmp`–`objectFa029.bmp`. El constructor coloca los bitmaps estáticos en coordenadas fijas y registra los sprites de objeto con separación inicial de 232 unidades en x. El pseudocódigo completo está en `artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/stage-layout/00474f70.c`.

## Implementación y prueba

La vista de BG34 ahora permite recorrer con Up/Down tres páginas: catálogo de tiles `0000`, composición `0000`/`0001`, y catálogo de bitmaps y objetos. La última página escala las miniaturas a celdas, etiqueta cada sprite `objectFa` de `00` a `29` y reporta la cobertura cargada.

Corrida fresca de 600 frames en Vita3K SDL pasó. `stage=bg34`, página 2; 30/30 tiles por rejilla, 4/4 bitmaps y 30/30 sprites objeto decodificados; PAT/tarjetas de roster 20/20, cero fallos de textura. Evidencia: `artifacts/vita3k-result.json` y captura `artifacts/screenshots/stage-assets.bmp`, revisada para confirmar que las miniaturas no se pisan.

VPK de validación: `artifacts/Touhou123Vita-stage-assets-auto.vpk`, 80,227 bytes, SHA-256 `5bdd62132545170611293f1e83127133f7c1e44d4a2d5f2083c4912ea54268ec`.

## Trabajo que sigue

La galería probó disponibilidad y decodificación. La cadencia del ciclo de sprites se recuperó en la iteración siguiente; aún no están reconstruidas su transformación de cámara, las ubicaciones dinámicas ni colisiones o lógica interactiva. Ver [ITERATION14.md](ITERATION14.md).
