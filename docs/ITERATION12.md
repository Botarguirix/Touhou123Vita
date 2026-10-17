# Iteración 1.8: dispatch y geometría de tiles de escenarios

## Evidencia de la referencia

Se verificó el SHA-256 del PE 1.10a (`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`) y, con Ghidra headless en modo de solo lectura, se exportó el selector `00470e40`, el selector de escenario `00424280`, el constructor de selección `00426900` y las funciones concretas de backgrounds. Los fuentes y callers están en `artifacts/kernel/<sha>/stage-layout/`; `tools/analyze-stages.ps1` y `ExportStages.java` repiten el análisis. No se modificó el proyecto Ghidra archivado.

El dispatcher distingue IDs `0–6`, `10–18` y `30–38` (con algunas variantes por ID); los manifiestos locales contienen 24 carpetas combinando DAT 10.5 y 12.3. El loader común `0046fe40` carga 30 piezas en una rejilla de seis columnas por cinco filas. El índice de archivo da fila `n/6` y columna `n%6`; la posición x usa `700 - 256*col`, así que las columnas se dibujan en orden inverso al nombre del archivo. Los escenarios antiguos usan `0000_%02d`; los tiled usan `0000[row][col]`.

El constructor especial de `bg34` (`00474f70`) carga dos rejillas de 30 tiles, prefijos `0000` y `0001`, con la segunda desplazada verticalmente 1200 unidades respecto a la primera. También carga bitmaps adicionales y objetos animados. Esto confirma que los dos números entre corchetes son coordenadas de celda, y no un selector de capa.

## Cambio y validación

El visor ahora lista las 24 carpetas presentes en los DAT locales, refleja el orden horizontal x de ambas rejillas y presenta `bg34` con la separación vertical recuperada. Up/Down alterna entre la cuadrícula base y la vista compuesta de prefijos `0000`/`0001`. El autotest recorre IDs hasta `bg34` y exige 30 tiles decodificados en cada prefijo. La corrida fresca de Vita3K SDL pasó 600 frames: `stage=bg34`, `stage_layer=1`, `stage_tiles=30`, `stage_alt_tiles=30`, roster 20/20 y combate experimental B=2/C=2. La captura guest [stage.bmp](../artifacts/screenshots/stage.bmp) fue revisada.

El VPK de validación es `artifacts/Touhou123Vita-stage-auto.vpk`, SHA-256 `3aad88ba732fd3672b8bc91bbf7aeef4cab18dd1325a0c6c462aff9213265bbd`. La vista compuesta usa el orden x y el offset entre planos recuperados en Ghidra; aún no integra cámara/scroll, parallax, bitmaps estáticos, animación de objetos, colisiones ni mecánicas de los 24 escenarios.

## Siguiente paso

Recuperar la cámara/scroll y los datos y animaciones de objetos; validar contra captura/replay PC. Después ampliar pruebas de recursos por cada ID que realmente exista en las copias DAT y distinguir assets 10.5 heredados de los propios de 12.3.
