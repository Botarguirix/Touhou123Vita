# Cobertura inicial de PAT

Catálogo generado al decodificar los PAT instalados localmente. `bloques` incluye acciones y secuencias según el formato; `poses con daño` cuenta cuadros que traen daño y caja/flag de ataque. Esta tabla mide contenido cargable, no acciones ya reproducidas por el motor.

Se decodificaron **22 PAT**.

| Personaje/carpeta | Imágenes | Bloques | Aliases | Poses | Poses con daño |
|---|---:|---:|---:|---:|---:|
| `alice` | 536 | 1,048 | 30 | 3,462 | 707 |
| `aya` | 548 | 721 | 25 | 3,664 | 820 |
| `chirno` | 375 | 972 | 27 | 3,429 | 346 |
| `common` | 86 | 64 | 0 | 153 | 4 |
| `iku` | 546 | 627 | 29 | 3,473 | 634 |
| `komachi` | 631 | 631 | 23 | 3,264 | 368 |
| `marisa` | 824 | 1,008 | 25 | 4,461 | 1,353 |
| `meirin` | 744 | 785 | 21 | 3,543 | 792 |
| `namazu` | 179 | 731 | 86 | 3,276 | 858 |
| `patchouli` | 892 | 730 | 29 | 3,450 | 567 |
| `reimu` | 812 | 1,001 | 20 | 4,436 | 1,036 |
| `remilia` | 789 | 703 | 20 | 3,505 | 446 |
| `sakuya` | 581 | 785 | 22 | 3,314 | 287 |
| `sanae` | 535 | 764 | 43 | 2,963 | 631 |
| `suika` | 596 | 809 | 24 | 3,833 | 463 |
| `suwako` | 853 | 1,026 | 30 | 4,746 | 1,093 |
| `tenshi` | 645 | 721 | 33 | 2,880 | 240 |
| `udonge` | 529 | 804 | 21 | 3,297 | 190 |
| `utsuho` | 649 | 1,041 | 29 | 5,130 | 1,143 |
| `youmu` | 782 | 655 | 21 | 3,252 | 375 |
| `yukari` | 555 | 651 | 31 | 3,738 | 275 |
| `yuyuko` | 523 | 746 | 35 | 3,088 | 255 |

Las carpetas `common` y `namazu` se reportan por separado; el inventario general contiene 20 carpetas de personajes jugables candidatas, además de contenido común y Namazu. La clasificación final debe confirmarse con selección de personaje, guion y ejecutable original.

Para consultar disponibilidad de acciones dañinas por botón y por índice PAT en las 22 carpetas, ver [ATTACK_COVERAGE.md](ATTACK_COVERAGE.md). Se regenera a partir de `artifacts/pat-attacks.tsv` con `python3 tools/summarize_pat_attacks.py artifacts/pat-attacks.tsv docs/ATTACK_COVERAGE.md`.

La disponibilidad de imágenes de todas las poses con daño se cruzó además con los DAT 12.3 y 10.5: ver [PAT_RESOURCE_COVERAGE.md](PAT_RESOURCE_COVERAGE.md) y el regenerador `tools/summarize_pat_resource_coverage.ps1`. Las 20 carpetas candidatas no presentan imágenes dañinas fuera de los cinco índices; esto no valida su renderizado ni el dispatcher de input.

El exportador `resource_probe --pat-detail` conserva cada pose y sus cajas ofensivas en `artifacts/pat-detail.tsv`; [DASH_ATTACK_REFERENCE.md](DASH_ATTACK_REFERENCE.md) resume las variantes 66B/j4B/66C de todas las carpetas.
