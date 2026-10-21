# Iteración 2.83: easing horizontal y límites del viewport

Las ejecuciones de `FUN_00429040` muestran el paso horizontal automático: desde el centro actual hacia el objetivo aplica `delta/30 + 5` si avanza a la derecha, o `delta/30 - 5` si va a la izquierda; hace snap si rebasa el objetivo. Después limita el centro visible al escenario de 1280 unidades usando el zoom ya actualizado: `[320/zoom, 1280-320/zoom]`. Los casos x86 incluyen movimiento interior y ambos límites con zoom reducido.

La lógica quedó como `t123_stage_camera_x_step` en el core, junto con el easing de zoom previamente derivado. El gate automático de cámara compara las tres salidas contra el método x86. Vita3K SDL pasó 600 cuadros, schema46, `regression_gate=1`, `stage_camera_pair_contract=1`; suite completa 106/106.

VPK automático probado: `artifacts/Touhou123Vita-camera-x-easing-auto.vpk`, SHA-256 `9de3c0d08b38d13387f5173131f2fb01909faf78670f9f435d138d4c4aacb9f4`. Interactivo: `artifacts/Touhou123Vita-camera-x-easing.vpk`, SHA-256 `8db0dadb87a2b9fab16eaf92b35339e7af58914ea9ae90e9095dc7a5c5d044b0`. Ambos comparten `eboot.bin` SHA-256 `461e075f900c4471593cef4820b91a6dcc33ab01c622f1610ad3a036af0aa010`; solo el auto-test se ejecutó en Vita3K.

El eje Y, el override persistente, el estado del constructor completo y el enlace de esta cámara al transform de la pelea siguen pendientes. Estos helpers son contratos de core, todavía no un encuadre jugable. Ver [ITERATION182.md](ITERATION182.md) y `tests/test_stage_camera_oracle.py`.
