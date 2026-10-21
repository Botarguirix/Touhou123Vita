# Iteración 2.47: inventario del constructor BG33 contrastado con PE

Fecha: 2026-10-17.

El oracle hash-pinned ahora comprueba el constructor `0x473af0`: reserva 24 objetos para la cuadrícula, ejecuta el bucle de celdas y conserva en el binario el patrón de ruta `BG33/0000[%02d][%02d].bmp`; también localiza los dos auxiliares `0001.bmp` y `0002.bmp`. El helper de slot y su renderer se mantienen separados de esos auxiliares: el callback usa tres rutas de transformación independientes para `+0xe8`, aplicando escala, rotación y presentación antes de componer cámara/viewport. La suite host completa pasó 77/77.

La evidencia del constructor confirma las fuentes, pero no proporciona una cronología de animación para los auxiliares: el tiempo proviene del gestor global de sprites y la posición de pantalla depende de la matriz/cámara. No se cambiaron fuentes de runtime ni se generó VPK en esta iteración; la última build verificada sigue siendo la de Iteración 2.45. Ghidra aún no está instalado, así que la exportación ampliada de la Iteración 2.46 todavía no se ejecutó.

Fuente: `original/th123.exe`, SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`; disassembly `artifacts/kernel/bg33-render-disasm.tsv`, `artifacts/kernel/bg33-render-full.tsv`.
