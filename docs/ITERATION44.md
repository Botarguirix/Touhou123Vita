# Iteración 1.40: cartas de skill de Reimu a acciones PAT

## Relación recuperada

Crucé el `handleInputs` de Reimu `004ae670`, su tabla de cartas de skill, el deck inicial y `artifacts/pat-detail.tsv`, todos correspondientes al ejecutable 1.10a fijado. El switch completo de la línea 415 asocia las doce cartas 100–111 con acciones del PAT de Reimu:

| Carta | Slot (`costOrSlot`) | Acción PAT | Poses | Poses con daño y caja |
|---:|---:|---:|---:|---:|
| 100 | 0 | 500 | 14 | 0 |
| 101 | 1 | 520 | 18 | 0 |
| 102 | 3 | 540 | 22 | 2 |
| 103 | 2 | 560 | 16 | 3 |
| 104 | 0 | 505 | 14 | 0 |
| 105 | 1 | 525 | 16 | 0 |
| 106 | 3 | 545 | 30 | 0 |
| 107 | 2 | 565 | 34 | 4 |
| 108 | 0 | 510 | 14 | 0 |
| 109 | 1 | 530 | 15 | 0 |
| 110 | 3 | 550 | 17 | 0 |
| 111 | 2 | 570 | 25 | 0 |

El deck inicial incluye dos copias de cada carta 100–103. El PAT confirma secuencias/poses para las doce acciones; solo cuatro acciones tienen alguna pose con daño positivo y caja ofensiva declarada en el inventario. Ese conteo describe los datos PAT, no demuestra por sí solo el efecto completo: pueden existir objetos, colisiones u otros efectos externos.

## Rutas adicionales y límites

El contexto de ambos switches ya quedó resuelto por su estructura en el C de Ghidra y el wrapper de SokuLib: `FUN_00463530` es `Player::isGrounded()`. El switch completo de la línea 415 está en la rama terrestre; el switch de línea 89 está en la rama aérea. Por eso no son una ruta base y una mejora. El aéreo contiene ocho cartas y selecciona estas acciones:

| Carta | Acción PAT aérea | Observación frente a tierra |
|---:|---:|---|
| 100 | 502 | Distinta de 500 |
| 101 | 522 | Distinta de 520 |
| 102 | 540 | Igual |
| 104 | 507 | Distinta de 505 |
| 105 | 527 | Distinta de 525 |
| 106 | 545 | Igual |
| 108 | 512 | Distinta de 510 |
| 111 | 572 | Distinta de 570 |

Las cartas 103, 107, 109 y 110 no aparecen en el switch aéreo de este handler. Los gates de estado/frame que envuelven los switches aún no se han reducido a contratos dinámicos; tampoco se ha demostrado si la acción se selecciona en juego para todas las configuraciones/decks.

El reporte local reproducible es `artifacts/reimu-skill-card-routes.json`, ligado a hashes de las entradas. Se genera con `python tools/analyze_skill_card_routes.py`. El análisis es estático: todavía no prueba consumo de carta, transición por frame, cancelaciones, efectos/objetos ni funcionamiento en el runtime Vita. Tampoco cubre otros personajes.

## Verificación

- `tests/test_skill_card_routes.py` prueba que los switches se clasifican como aéreo/terrestre desde la rama de `isGrounded()` y que la relación real de 12 cartas coincide con el handler, el deck y la presencia PAT.
- Esta iteración agrega análisis y tests; no modifica la lógica del juego ni genera otro VPK.

## Próximo paso

El helper `onSkillUpgrade` ya se ejecutó por separado contra x86 en [ITERATION45.md](ITERATION45.md). Ahora recuperar los guards de cancelación que rodean ambas rutas; escoger una skill con hitbox directa (por ejemplo, acción terrestre 560 o 565) y construir una entrada x86 controlada para observar acción, frame, flags y vida del rival. Después portar esa ruta y comparar la traza por frame en host/Vita3K. Repetir el inventario de acciones aéreas/terrestres para las otras 19 clases de personaje.
