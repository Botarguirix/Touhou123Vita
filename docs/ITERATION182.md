# Iteración 2.82: easing asimétrico de zoom de cámara

El oracle ahora ejecuta el update x86 `FUN_00429040` de la cámara hasta la salida de la rutina y captura sus campos. Con `zoom actual=1` y objetivo `0.82051283`, el original entrega `0.96210259`; con actual `0.5` y objetivo `1`, entrega `0.50825`. Esto confirma la regla asimétrica: al alejar usa `current + (target-current)/5 - 0.002`; al acercar usa `current + (target-current)/80 + 0.002`. El método ajusta al objetivo si se excede y mantiene el piso 0.5.

La transición quedó implementada como `t123_stage_camera_zoom_step` y se incluyó en el contrato automático de Vita. La primera corrida detectó un fixture de borde mal elegido (`0.51` no cruza el límite); corregido a `0.501`, el VPK fresco pasó 600 cuadros/schema46, regresión general y contrato de cámara. Suite completa: 105/105.

VPK automático probado: `artifacts/Touhou123Vita-camera-easing-auto-v2.vpk`, SHA-256 `e152b37a2355cf35de160e2b20b9eba3ab74f276b3c63c6690c1394af6a98182`. Interactivo: `artifacts/Touhou123Vita-camera-easing.vpk`, SHA-256 `c3cd39419063adcd44c91fe54528ac03011d5dc43ab61d5245459b9b1912bc53`. Ambos comparten `eboot.bin` SHA-256 `46019dd2663207220ff848c0b644326c5295a20429568d426558b9cdfb6c4429`; el interactivo no se ejecutó en Vita3K, pero contiene el mismo ejecutable del auto-test.

Alcance aún pendiente: transición exacta del centro horizontal/vertical, overrides manuales y composición de esos valores con zoom durante la pelea. El helper de zoom se valida aislado y todavía no controla la cámara real del renderer. Ver [ITERATION181.md](ITERATION181.md), `tools/x86_stage_camera_oracle.py` y `tests/test_stage_camera_oracle.py`.
