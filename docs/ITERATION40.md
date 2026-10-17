# Iteración 1.36: ráfaga de Suwako 418 portada y contada en Vita3K

## Cambio

El combate ya no produce un solo 808 cerca del inicio de Suwako 418. `Fighter.object_counter` se siembra en 1 cuando la animación 418/seq. 0 cruza a pose 10; en cada tick siguiente, el contador crea un objeto PAT 808 en los valores impares 1–19 y termina en 20. La pose PAT gobierna el frame del ejecutable; el rango 5–17 solo controla el ajuste de movimiento `+0x0f4`, no el gate de spawn.

El estado cuenta creaciones exitosas (`Fight.object_spawns`) y se incluye en el digest. La asociación de `DI` con secuencia 0/subframe 0 es una hipótesis del port que requiere una traza del juego PC. La posición y altura actuales, velocidad, vida y daño del objeto siguen provisionales; esta iteración verifica la cadencia y el conteo.

## Prueba y VPK

- Se añadió el fixture host `suwako_418_burst`: comienza en pose 9/subframe 2, comprueba la transición a pose 10 y propone contar diez objetos en los siguientes 19 ticks. El fixture compiló como ARM, pero no se ejecutó en host.
- `tests/fight_tests.c` compila como unidad ARM con `-Wall -Wextra -Werror`. No se ejecutó como binario host: `wsl.exe -l -q` responde `E_ACCESSDENIED` y no hay compilador C host instalado.
- El probe dentro del VPK exige `suwako_418_burst_spawns == 10` y termina en fallo si el conteo difiere.
- VitaSDK compiló el VPK automático [Touhou123Vita-suwako-burst-auto.vpk](../artifacts/Touhou123Vita-suwako-burst-auto.vpk), SHA-256 `4477b6173f5ac4bae6d2807fd56f2afa5c25112e1366c4958c289bcfb53476bc`.
- Vita3K SDL pasó schema 19 en 600 frames: 10 objetos Suwako 418, cinco rutas de objeto, cuatro variantes ofensivas, roster/PAT/tarjetas 20/20, BG34 y 145 texturas decodificadas sin fallos.
- La suite Python pasó 8/8 y `git diff --check` quedó limpio. El analizador PE confirmó el hash de referencia esperado.

## Siguiente paso

Capturar una traza PC de 418 para confirmar el sentinel `DI` y el conteo; luego recuperar el callback por índice 6, la escala temporal de `+0x5e4`, transformación de coordenadas, trayectoria, vida, colisión y daño del 808. La paridad visual y funcional completa sigue pendiente.
