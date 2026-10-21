# Iteración 2.80: zoom automático derivado de la cámara original

Se ejecutó el método x86 `FUN_00428e20` del PE fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` bajo Unicorn. El harness sustituye solamente la llamada CRT `sqrt` por `FSQRT` equivalente y valida cinco separaciones controladas. La regla observada para zoom automático es `max(0.5, 640 / sqrt(max(640, abs(dx)+80)^2 + (abs(dy)*1.5)^2))`.

La regla está implementada en `t123_stage_camera_pair_target`, con pruebas C y un oráculo Python que ejecuta el método original. No representa todavía el ciclo completo de cámara: centro objetivo, límites/modos manuales y suavizado por cuadro siguen pendientes, y el zoom aún no está conectado al encuadre de la pelea.

Validación: pruebas enfocadas de cámara/BG36, 4/4; VPK automático ejecutado en Vita3K SDL durante 600 cuadros, schema46, `regression_gate=1`, `stage_camera_pair_contract=1`. VPK automático: `artifacts/Touhou123Vita-camera-zoom-auto.vpk`, SHA-256 `4b2c7601ed69b34d41bf7baa8daf7b5d15b4ef1eb4575e61e3c96eba8e277b1b`. VPK interactivo: `artifacts/Touhou123Vita-camera-zoom.vpk`, SHA-256 `6e68da9d26382eabb32b4750dacf18a9a36530bbb8fe2969ca6d4230e3fe8a73`. Ambos incluyen el mismo `eboot.bin`, SHA-256 `d245154f856cbdeec19100a6321d82393bab1022c69a70d38fd88a49103fa877`.

Próximo: ejecutar `FUN_00428e20` con pares variados para resolver centro y flags; recuperar las rutinas de transición temporal y después conectar posición/zoom al renderer integrado del fondo y de los jugadores. Ver [ITERATION179.md](ITERATION179.md), `tools/x86_stage_camera_oracle.py`, `tests/test_stage_camera_oracle.py`.
