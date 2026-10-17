# Iteración 1.51: movimiento horizontal de Reimu 560

Fecha: 2026-10-16.

## Contrato x86 observado

El ejecutable `original/th123.exe` (SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`) contiene el integrador de posición del jugador en `00463550`. Su ruta normal suma a `x` la velocidad horizontal del propio jugador (`Player+0xF4`) y la velocidad suplementaria horizontal del oponente (`opponent+0x74C`), aplica el signo de dirección (`Player+0x104`) y `speedPower` (`Player+0x564`), y actualiza la posición (`Player+0xEC`). El loop de jugador lo llama desde `0046E010`. El handler de Reimu 560 en `004A0639` prepara `speed.x=4.5`, `speed.y=14` y gravedad `0.75` al entrar a seq. 1/pose 0.

`tools/x86_physics_oracle.py` ejecuta el helper del PE original bajo Unicorn y valida cuatro vectores de orientación, potencia y velocidad suplementaria. El nuevo test forma parte de la suite completa: 20 tests Python pasan.

## Cambio del port

La skill Reimu 560 ahora integra el desplazamiento horizontal de 4.5 unidades por tick en ambos sentidos, en unidades de cuarto para conservar la media unidad, y limita la posición a los bordes actuales del escenario prototipo. Las pruebas C cubren dirección positiva y negativa además del arco vertical y el aterrizaje. La corrida automática de Vita requiere esos dos resultados en su reporte schema 22.

El límite de escenario es la aproximación que ya usa este prototipo. La suma de velocidad suplementaria de otros estados, `speedPower` variable, el flag de bloqueo de escenario, colisiones y el instante exacto de la primera integración requieren más trazas antes de afirmar paridad completa.

## Artefacto y verificación

- Build VitaSDK exitoso: `artifacts/reimu-air-motion.vpk`, 93,881 bytes.
- SHA-256: `b2c990c80676ad739c9d2f01db1b9fb8cb9cb546a180b2b4bae90da2bde5a2b6`.
- La suite Python completa pasa (20/20).
- La primera corrida Qt del emulador local terminó con código `-1` antes del invitado. Con el frontend SDL la misma compilación sí produjo evidencia fresca y pasó el runner completo: schema 22, 600 frames, `skill_x_delta=175`, movimiento inverso, aterrizaje seq. 3, roster 20/20 sin fallas de textura, y escenario BG34/capa 3 con 30 tiles y 30 assets de objetos. SHA del VPK reportado por Vita3K coincide con el build. `tools/vita3k-test.ps1` ahora usa SDL por defecto para que nuevas corridas no caigan en la ruta Qt que falló.
