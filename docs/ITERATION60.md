# Iteración 1.60: fórmula de spawn de Suwako 418

## Evidencia del PE

En `0076f3b4`, el PE 1.10a fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` carga el registro desde `Player+0x158`. Para cada creación calcula el spawn como:

- `x = Player+0xec + s8(Player+0x104) * s32(record+0x98)`.
- `y = Player+0xf0 - s32(record+0x9c)`.
- crea el objeto `0x328` (808) mediante `0046eb30`.

El analizador fija las instrucciones de carga, operación y llamada para detectar cambios del binario. Los valores del registro en la acción 418 y su productor todavía no están identificados; el port no sustituye esos valores por `ox/oy` del sprite PAT 808, que pertenecen al transform visual del objeto.

## Transferencia desde Touhou75Vita

Seguimos usando sus ideas de análisis CFG, cobertura acotada y pruebas fail-loud, documentadas en [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md). No se copió código ni se mezclaron direcciones; para el comportamiento manda el PE de Touhou 12.3.

## Verificación

- `tools/analyze_object_motion.py original/th123.exe` validó el hash y las nuevas firmas.
- `python -m unittest discover -s tests -p 'test_*.py'`: 23/23 aprobadas.
- `git diff --check`: sin errores; quedan avisos de conversión de fin de línea en archivos preexistentes.
- No se recompiló el VPK porque esta iteración actualiza análisis y evidencia, no el runtime.

## Pendiente

Rastrear quién llena `Player+0x158` y cuáles son sus dos valores durante la acción 418. Después integrar esa posición y contrastar trayectoria, aterrizaje, colisión y daño con el juego de PC y Vita3K.
