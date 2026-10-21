# Iteración 2.89: inicialización del sprite del jugador localizada

El vtable de Reimu `0x85bf4c`, slot 11, apunta a `0x438d20`. Ese método carga `Player+0x154` y lo dibuja mediante `0x4389d0`; la rutina agrega la cámara con `0x4293f0`. La atribución al jugador queda respaldada por la tabla de vtable, no solo por la proximidad de direcciones.

`0x466670` reemplaza/libera el componente anterior, asigna 0x108 bytes al nuevo objeto y escribe su vtable `0x85772c` en `Player+0x154`. Luego consulta el registro de imagen/pose, pasa sus campos de geometría a `0x406c60` y copia dos palabras con signo del registro a `component+0xf0/+0xf4`. La ruta de dibujo calcula el origen anterior a cámara como `x = x_e8 - facing*x_f0`, `y = -y_ec - y_f4`. Así, los campos no son ancho/alto; son valores del registro de imagen/pose. La correspondencia exacta entre ese registro y `T123Pose.tx/ty/ox/oy` aún debe demostrarse.

La suite focalizada de cámara pasa 10/10 e incluye ahora checks SHA-pinned para vtable, método de dibujo e inicialización del componente. No se cambió el runtime ni se generó VPK. Próximo: reconstruir el selector `0x43f2f0` y el mapeo binario de su registro a `T123Pose`, generar vectores de anclaje para sprites reales y reemplazar solo entonces el offset fijo del prototipo.

Evidencia: [player-render-init-full.tsv](../artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/player-render-init-full.tsv), [player-render-camera-probe.tsv](../artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/player-render-camera-probe.tsv), [manifest.tsv](../artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/manifest.tsv).
