# Iteración 2.86: easing vertical de cámara

El update `FUN_00429040` fue ejecutado en el oracle Unicorn sobre el PE original. Para el eje vertical usa `difference / 20 + sign(difference)` cuando el menor Y de los jugadores es ≤ 270 y `difference / 10 + sign(difference)` cuando es > 270. Si el paso cruza el objetivo, fija el valor exactamente en target. Después limita la coordenada a `[-420 * (2*zoom - 1), 0]`.

Se implementó `t123_stage_camera_y_step` en `src/stage.c` con su declaración en `include/t123/stage.h`; las pruebas C, Python/oracle y el gate de Vita cubren ambos divisores, clamp y snap. La batería Python completa pasó 109/109.

Vita3K SDL ejecutó el VPK automático durante 600 cuadros: schema 46, `status=passed`, `regression_gate=1`, `stage_camera_pair_contract=1`; se generaron capturas frescas. Auto VPK: `artifacts/Touhou123Vita-camera-y-easing-auto.vpk`, SHA-256 `6fd0b66167a7438953e37e718e7bbd53593958257483011ee7f900176a4b9c22`. Interactivo: `artifacts/Touhou123Vita-camera-y-easing.vpk`, SHA-256 `2d8afb9005b08597d7751b2f8bc588d085aec9e7818f00ccb8b2b63301698010`. Ambos tienen `eboot.bin` SHA-256 `0f4d5ba690c6b29165d372ffef07de6a16344b0b1b5706317533d1b99339dc1a`.

La prueba todavía valida un helper aislado: el estado de seguimiento dinámico no se alimenta desde las posiciones de los luchadores ni controla aún la composición del fondo en combate. El siguiente paso es conectar target, easing X/Y y zoom a cada tick de juego y contrastar una ronda con la ejecución original.
