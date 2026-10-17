# Iteración 1.31: objetos PAT visibles de Alice y Suwako

## Cambio

Se añadió un pool determinista de 16 objetos. Cada objeto conserva dueño, acción/secuencia PAT, posición, velocidad, vida y animación; su caja PAT puede colisionar con hurtboxes y aplicar daño. El renderer muestra la imagen PAT del dueño. El digest de combate incorpora el estado de los objetos.

| Personaje (índice) | Acción | Objeto/variante PAT | Movimiento y vida del prototipo |
|---|---:|---|---|
| Alice (3) | 408 | 849, secuencia 19 | quieto, 12 ticks; sin caja ofensiva |
| Alice (3) | 418 | 849, secuencias 21/23 en subestados 2–5 | 7 unidades/tick, 90 ticks |
| Suwako (19) | 408 | 989, secuencia 5 | 3 unidades/tick, 90 ticks |
| Suwako (19) | 418 | 808, secuencia 0 | 4 unidades/tick, 90 ticks |

El probe Vita comprueba cinco spawns (cuatro rutas más las dos secuencias de Alice 418), cuatro variantes ofensivas y decodificación de la imagen PAT. Las velocidades, vidas, transformación, temporización de creación y eliminación son aún valores de prueba, no reconstrucciones del original. La colisión implementada aún necesita comparación con la referencia por frame antes de contar estos movimientos como fieles.

## Build y validación

- VitaSDK compiló el core ARM y generó [Touhou123Vita-object-render-auto.vpk](../artifacts/Touhou123Vita-object-render-auto.vpk); SHA-256 `efc1ea98c018af96e7b59c9826d9ed06746e6a68423466a44c3b67abbbe6a62d`.
- Vita3K con frontend SDL pasó autotest schema 17: 600 frames, roster/PAT y tarjetas 20/20, 137 texturas, BG34, cero fallos, `object_route_probe=5`, `object_attack_routes=4` e imagen renderizada.
- Captura generada en Vita3K: [object-probe.bmp](../artifacts/screenshots/object-probe.bmp). El VPK incluye solo el ejecutable, fuente, SFO y autotest; no incluye recursos propietarios.
- El frontend Qt de Vita3K produjo una excepción de lectura nula antes de lanzar la app; el frontend SDL completó la misma regresión.
- CTest host sigue pendiente porque CMake y un compilador host no están disponibles en PATH.

## Siguiente paso

Recuperar y comparar en el PE fijado por hash los callbacks completos de update, colisión y eliminación de los objetos 849, 989 y 808. Reemplazar las trayectorias provisionales por transformaciones y ventanas de vida verificadas; añadir fixtures host por ruta y trazas por frame frente al juego original. Mantener Vita3K SDL como regresión visual y funcional.
