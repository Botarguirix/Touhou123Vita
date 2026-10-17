# Iteración 1.50: salto y aterrizaje natural de Reimu 560

## Evidencia x86 y port

El dispatcher original `004A0639` inicializa la trayectoria al llegar action 560 a seq. 1, pose/subframe/frame 0 (`004A0772`). Escribe `+0xF8=14.0` como velocidad vertical y `+0x100=0.75` como gravedad; también escribe `+0xF4=4.5`, que corresponde a velocidad horizontal y queda pendiente de integrar con el modelo de facing/colisión. La rama seq. 1/2 resta gravedad antes de evaluar `applyAirMechanics`; al tocar suelo descendiendo y sin el flag de colisión, selecciona seq. 3. Bytes y constantes se verificaron contra el PE fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.

El runtime ahora inicia la velocidad vertical al entrar a seq. 1 y representa posición/velocidad en cuartos de unidad, con `vy=14` y gravedad `0.75` por tick. La trayectoria lleva naturalmente a contacto con el suelo y la transición existente selecciona PAT seq. 3. La velocidad horizontal de 4.5 aún no está aplicada; no se afirma paridad de trayectoria completa.

## Verificación

- Se amplió `tests/fight_tests.c` para recorrer en el fixture PAT secuencias 0→1→2, vuelo, descenso y seq. 3 sin inyectar posición de aterrizaje.
- El auto-test del VPK hace la misma secuencia con el DAT/PAT real de Reimu card 103 y reporta `skill_air_launch_ok=1`, `skill_landing_ok=1`, `skill_landing_sequence=3`.
- Build VitaSDK y prueba fresca en Vita3K SDL: schema21, 600 frames, `status=passed`; roster, cartas y sprites 20/20; BG34, dashes, B/C y objetos pasan.
- VPK: `artifacts/reimu-air-combo.vpk`; SHA-256 `2d4df513bee85c2747fa8c97d3bc8849beb391216974912270e84241e5c78dfd`.
- VPK interactivo para revisión manual: `artifacts/reimu-air-combo-demo.vpk`; SHA-256 `8c301f2f35c9f4b272991779726c42486db94f242a2f3bd43ff2a092d6323c89`. Compilado; Vita3K automático probó el mismo código del motor, pero esta variante interactiva todavía no se ejecutó manualmente.
- Suite Python sigue 19/19. No se ejecutó el binario de pruebas C host debido a WSL `E_ACCESSDENIED`.

## Pendiente

Aplicar la velocidad horizontal `+0xF4=4.5` con su orientación y reglas de movimiento verificadas; recuperar la salida de seq. 3 y el gate real de cartas/cancelación. La carta 103 sigue seleccionada como sonda fija del prototipo, y la prueba aún no compara frame a frame con una replay del juego de PC.
