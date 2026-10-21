# Iteración 2.43: layout constructor BG33

Fecha: 2026-10-17.

El constructor x86 `FUN_00473af0` asigna BG33, construye un grid de 24 entradas y llama al loader para `0000[row][col]` con cuatro filas y seis columnas. Luego carga `0001.bmp` y `0002.bmp`; sus dimensiones devueltas se pasan a `FUN_00406c60` con anclas inferiores `(700,228)` y `(350,152)`. El visor ahora solicita el nombre base correcto de 24 tiles para BG33 (sin dibujar seis rutas no usadas), muestra la rejilla 6×4 y coloca los dos sprites por su pivote inferior centrado en el diagrama local. La cámara/proyección del escenario y un callback de render dedicado no se han reconstruido, por lo que esta vista se etiqueta como layout local de constructor.

El escenario BG33 ahora tiene tres páginas de visor: tiles, auxiliares y layout. La autoprueba entra a la tercera página y guarda `artifacts/screenshots/stage-bg33-layout.bmp`. El gate exige que la página haya sido dibujada, la captura se haya escrito y se hayan cargado exactamente 24 tiles. `regression_gate` incluye los contratos runtime previos; el reporte schema41 añade los resultados BG33. No se debilitaron los requisitos de build/ejecución.

Verificación: 72 pruebas Python aprobadas; VitaSDK compiló el VPK automático; Vita3K SDL aislado completó 600 frames y produjo `status=passed`, `regression_gate=1`, `stage_bg33_layout=1`, `stage_bg33_layout_capture=1` y `stage_bg33_tiles=24`. VPK: `artifacts/Touhou123Vita-latest.vpk`, 103,852 bytes, SHA-256 `948029ff04b90799aebf9510e85ec73f6e9dd7d3d7b9340682a82f21693e49c3`. Esta prueba no establece paridad visual con PC ni fue ejecutada en una PS Vita física.

Siguiente: recuperar del PE el camino de render/cámara de BG33 y comparar las anclas/escala contra captura PC; después clasificar las celdas faltantes por constructor para otros escenarios, y recuperar los fondos que no aparecen en los DAT inspeccionados. Las posiciones del constructor son coordenadas locales hasta demostrar su transformación final.
