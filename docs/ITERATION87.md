# Iteración 1.87: inventario de flags de ataque PAT

Se agregó `tools/summarize_pat_attack_flags.py` para cruzar las poses PAT con daño y `attack_flags` no nulos. El reporte conserva las combinaciones por personaje, acción, índice, valor raw del flag y presencia de cajas explícitas; no asigna semántica a los bits.

El inventario del roster actual encuentra 1,987 combinaciones con cajas explícitas (7,129 poses), 1,442 sin cajas explícitas (4,891 poses) y 164 valores distintos de flag dentro del grupo sin cajas. Remilia 2C/412 aparece con una pose de 750 de daño y `0x00204002`; sus acciones aéreas 416:0 y 416:1 tienen una pose de 800 y `0x0000240a`. Alice 418:0 también figura sin caja directa (`0x00088404`), en concordancia con su ruta de objeto 849.

El script y su prueba sintética pasan con el Python incluido en el runtime de Codex. El reporte generado desde `artifacts/pat-detail.tsv` está en [PAT_ATTACK_FLAGS.md](PAT_ATTACK_FLAGS.md). No se cambió el motor ni se infirió una colisión a partir de los bits. El siguiente paso es exportar y ejecutar en Ghidra el flujo de conversión de FrameData y colisión que consume esos campos, y contrastar Remilia 412 con una ejecución original.

El entorno actual conserva el proyecto/exportes Ghidra previos, pero no se localizó `analyzeHeadless.bat`; solicité la ruta de GhidraHome para reanudar la descompilación. Mientras tanto, el roadmap sigue activo y el inventario puede guiar la extracción de contratos de flags para el resto del roster.
