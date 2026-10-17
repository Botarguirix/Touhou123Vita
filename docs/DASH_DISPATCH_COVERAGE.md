# Cobertura de dispatcher dash/B/C por roster

Generado desde `artifacts/pat-detail.tsv` con `tools/summarize_dash_dispatch.py`. Se muestran las acciones PAT explícitas (no aliases) y sus pares `move_lock/action_lock`; `hit` significa que al menos una pose tiene daño y caja ofensiva. El campo se repite por pose, por lo que se consolida por variante.

| Personaje | 200 dash | 408 66B (índice: move/action lock) | 418 66C (índice: move/action lock) |
|---|---|---|---|
| `reimu` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (sin hitbox dañina), 1:50/100 (hit), 2:50/100 (sin hitbox dañina) | 0:50/100 (hit), 1:40/100 (sin hitbox dañina), 2:40/100 (sin hitbox dañina) |
| `marisa` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (hit), 1:50/100 (hit), 2:50/100 (sin hitbox dañina) | 0:50/100 (hit) |
| `sakuya` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (hit) | 0:50/100 (hit) |
| `alice` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:40/50 (sin hitbox dañina) | 0:50/100 (sin hitbox dañina) |
| `patchouli` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/50 (hit) | 0:50/100 (hit) |
| `youmu` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (hit) | 0:50/100 (hit) |
| `remilia` | 0:5/10 (sin hitbox dañina), 1:5/10 (sin hitbox dañina), 2:5/10 (sin hitbox dañina), 3:5/10 (sin hitbox dañina) | — | — |
| `yuyuko` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:20/100 (hit) | 0:50/100 (hit), 1:50/100 (sin hitbox dañina), 2:50/100 (sin hitbox dañina) |
| `yukari` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/50 (hit) | 0:50/100 (hit) |
| `suika` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (hit) | 0:50/50 (sin hitbox dañina), 1:20/50 (sin hitbox dañina), 2:20/50 (hit), 3:20/50 (sin hitbox dañina), 4:20/50 (sin hitbox dañina), 5:20/50 (sin hitbox dañina) |
| `udonge` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina), 2:5/50 (sin hitbox dañina) | 0:50/100 (sin hitbox dañina), 1:50/100 (hit), 2:50/100 (sin hitbox dañina) | 0:50/100 (sin hitbox dañina), 1:50/100 (hit), 2:50/100 (sin hitbox dañina), 3:50/100 (sin hitbox dañina), 4:50/100 (sin hitbox dañina), 5:50/100 (sin hitbox dañina) |
| `aya` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (hit) | 0:50/100 (hit), 1:50/100 (sin hitbox dañina), 2:50/100 (sin hitbox dañina) |
| `komachi` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (hit) | 0:50/100 (hit) |
| `iku` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (hit) | 0:50/100 (hit), 1:50/50 (sin hitbox dañina), 2:50/50 (sin hitbox dañina) |
| `tenshi` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (sin hitbox dañina), 1:50/100 (hit), 2:50/100 (hit), 3:50/50 (hit) | 0:50/100 (hit) |
| `sanae` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (hit) | 0:50/100 (hit) |
| `chirno` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (sin hitbox dañina), 1:50/100 (hit), 2:50/100 (sin hitbox dañina) | 0:50/100 (hit) |
| `meirin` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (hit) | 0:50/100 (hit) |
| `utsuho` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina) | 0:50/100 (sin hitbox dañina), 1:50/100 (hit), 2:50/50 (sin hitbox dañina), 3:50/100 (sin hitbox dañina) | 0:50/100 (sin hitbox dañina), 1:50/100 (hit), 2:50/100 (sin hitbox dañina), 3:50/100 (sin hitbox dañina) |
| `suwako` | 0:5/50 (sin hitbox dañina), 1:5/50 (sin hitbox dañina), 2:5/50 (sin hitbox dañina) | 0:50/50 (sin hitbox dañina), 1:50/50 (hit), 2:50/50 (sin hitbox dañina), 3:50/50 (sin hitbox dañina) | 0:50/100 (sin hitbox dañina) |

## Lectura y límites

**`hit` en esta tabla solo cuenta daño y caja ofensiva dentro del PAT del personaje.** No significa que la acción no ataque cuando el campo dice “sin hitbox dañina”. El análisis del ejecutable fijado encontró rutas a `Player::createObject` (`0046eb30`) para Alice 408/418 y Suwako 408/418, y los inicializadores confirman la secuencia: Alice crea move 849 secuencia 19 en 408 (sin caja) y secuencias 21/23 en 418 (con cajas); Suwako crea move 989 secuencia 5 en 408 y move 808 secuencia 0 en 418 (ambos con cajas). La selección estática ya está resuelta; trayectoria, colisión y daño efectivo del objeto siguen pendientes en el port. Ver [ITERATION34.md](ITERATION34.md).

Los 20 PAT tienen una definición explícita de acción 200. Diecinueve tienen 408 y 418; Remilia no define esas dos acciones y no debe recibir este dispatcher genérico por inferencia. Sí contiene 412 (2C): índice 0: move/action lock 40/50, 1 poses con daño y flags, 0 con caja ofensiva explícita, flags 0x00204002. Las locks de 408 no son uniformes: el índice 0 toma 20 en Yuyuko, 40 en Alice y 50 en la mayoría. Las variantes también pueden diferir entre sí, por ejemplo 418 de Reimu e Iku. Por eso, usar un único lock o asumir que toda variante tiene el mismo comportamiento no cubre el roster.

El cruce PAT prueba disponibilidad y valores. El análisis de handlers (ver [ITERATION31.md](ITERATION31.md)) encontró candidatos 408/418 en 19 vtables y confirma la secuencia completa desde dash 200, `getMoveLock` y `setAction` en Reimu; no se han reconstruido todos los guards ni selectores. El probe de Vita3K verifica que la implementación acepte el borde del lock y rechace el frame siguiente usando el lock de la variante de demo seleccionada para los 19 PAT. Esto valida el port y los datos PAT, pero no es una comparación dinámica del juego original en el roster. Remilia no tiene 408/418: su 2C 412 tiene daño/flags, cero cajas ofensivas PAT explícitas, y su ruta de impacto/objetos sigue pendiente. Los datos vienen de la copia local del usuario; el juego no forma parte de Git.
