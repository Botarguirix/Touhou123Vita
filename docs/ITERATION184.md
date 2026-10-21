# Iteración 2.84: oracle de cámara desde el constructor real

Se corrigió el setup de las pruebas verticales ejecutando `FUN_00429560` del PE fijado por hash con argumentos en orden `(x0,y0,x1,y1)`. Este constructor inicializa campos auxiliares, llama dos veces a `FUN_00428e20` con el zoom actualizado entre ambas llamadas y ejecuta el primer `FUN_00429040`. Así quedan observables el target Y, la posición Y actual y la traslación vertical que recibe el renderer.

Resultados x86 relevantes:

- En suelo, `(200,0)` contra `(200,0)`: target Y `0`, cámara Y `0`, traslación Y `420`.
- `(200,0)` contra `(900,-500)`: zoom `0.59145278`, target Y `-18.29056`, cámara Y `-76.82034`, traslación Y `786.93622`.
- Ambos en `y=500`: target/cámara Y `-269.23077`, traslación Y `781.10577`.

Esto invalida el supuesto anterior de que el centro Y fuera `max(420,minY)`: ese valor provenía de llamar al target con un estado artificial de zoom y sin el constructor. Se retiró `center_y` del helper stateless; el eje vertical solo debe portarse desde el estado de instancia completo. `tests/test_stage_camera_oracle.py` ahora verifica la secuencia del constructor en tres casos.

Suite completa: 107/107. El VPK automático corregido pasó 600 cuadros en Vita3K SDL, schema46, `regression_gate=1`, `stage_camera_pair_contract=1`. Automático: `artifacts/Touhou123Vita-camera-constructor-auto.vpk`, SHA-256 `d44ffc6effb21f06dd2f5781a9e17ea90cc7fff229d6e464ca33039eda441aeb`. Interactivo: `artifacts/Touhou123Vita-camera-constructor.vpk`, SHA-256 `f95d09aabaedb872ed22dcc476340621fabeadf02b28c017110f66122f2d7816`. Comparten `eboot.bin` SHA-256 `10f2e34fcd43eb7dfa49f872af0ca664b988c87b33e7f9fdf3143e5817cc14b2`; solo el auto-test se corrió en Vita3K.

Quedan el easing vertical por estado, overrides persistentes y conectar la matriz completa a los personajes/escenarios durante la pelea. Los contratos siguen aislados del renderer jugable. Esta iteración corrige las afirmaciones verticales de [ITERATION181.md](ITERATION181.md) y [ITERATION183.md](ITERATION183.md).
