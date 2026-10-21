# Iteración 2.193: orientación de filas BG36 corregida desde el constructor PE

La lectura de `FUN_0046fe40` aclara que el constructor genérico solicita BG36 en orden ascendente: slot 0 carga `0000[01][01].cv2`, slot 1 `0000[01][02].cv2`, y así sucesivamente. `draw_battle_bg36` consume slots en ese mismo orden. La carga anterior asignaba `[05]` a la primera fila, invirtiendo la retícula sin base en el PE. Ahora `row` usa `[row+1]` y la regresión fija esa relación.

Los cinco recursos ausentes del inventario local ocupan slots 0, 1, 5, 6 y 11; por eso el patrón correcto para las 25 celdas presentes es `0x3ffff79c`. El gate antiguo esperaba `0x1c7bffff`, el patrón verticalmente invertido. Se actualizaron tanto la condición del guest como el runner Vita3K para requerir el patrón derivado de los nombres de recurso ausentes.

Pruebas focales BG36/BG37/BG38: 7/7. Vita3K SDL pasó schema46/600, `regression_gate=1`, `battle_stage_selected_interactively=1`, 25 tiles BG36, máscara `1073739676` (`0x3ffff79c`), cuatro auxiliares y renderer BG33 con 24 tiles. Auto VPK SHA-256 `bd7f3c82b324ee2f64b4b9625313129f6e314d0d42867bc6ecea47dfd85bcc4f`; el interactivo reconstruido desde el mismo código es SHA-256 `b00cba720528162339750dfb30f6122676758f3e14f55d7f9de9469d4e1c076d`. Ambos pasan `check_vpk.py` sin advertencias ni errores. La captura [fight-bg36.bmp](../artifacts/screenshots/fight-bg36.bmp) muestra que el piso y la estructura vuelven a enlazar sin el corte vertical anterior.

Esto corrige una inversión real de recursos, pero la coincidencia visual con el juego original sigue sin probarse. Falta capturar el mismo replay/frame en PC y comparar origen, cámara, zoom, escala y scroll; el porcentaje global permanece en 27%.
