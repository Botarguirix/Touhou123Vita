# Inventario local de recursos

Generado a partir del índice de `th123a.dat`, `th123b.dat` y `th123c.dat` instalados en el VitaFS local. Los DAT comerciales permanecen fuera del repositorio y del VPK.

El índice reúne **11,283 archivos** y **1,088,266,746 bytes** sin comprimir.

Se encontraron 22 PAT de personaje: 20 carpetas candidatas al roster, `namazu` y `common`. Ver [PAT_COVERAGE.md](PAT_COVERAGE.md) para el conteo de poses/acciones. El manifiesto lista presencia y tamaño, no demuestra todavía que cada recurso esté conectado a una escena o sea alcanzable desde el juego.

## Categorías principales

| Ruta bajo `data/` | Archivos |
|---|---:|
| `background` | 441 |
| `battle` | 104 |
| `bgm` | 73 |
| `card` | 483 |
| `character` | 7,999 |
| `csv` | 65 |
| `effect` | 320 |
| `guide` | 24 |
| `infoeffect` | 176 |
| `menu` | 150 |
| `number` | 1 |
| `profile` | 87 |
| `scenario` | 123 |
| `scene` | 636 |
| `se` | 473 |
| `stand` | 41 |
| `weather` | 87 |

## Carpetas de personaje

| Carpeta | PAT | CV2 | Otros archivos |
|---|---:|---:|---:|
| `alice` | 2 | 562 | 9 |
| `aya` | 2 | 23 | 8 |
| `chirno` | 2 | 393 | 9 |
| `common` | 1 | 84 | 1 |
| `iku` | 2 | 154 | 9 |
| `komachi` | 2 | 91 | 9 |
| `marisa` | 2 | 885 | 9 |
| `meirin` | 2 | 758 | 10 |
| `namazu` | 1 | 185 | 2 |
| `patchouli` | 2 | 986 | 8 |
| `reimu` | 2 | 906 | 12 |
| `remilia` | 2 | 106 | 9 |
| `sakuya` | 2 | 88 | 8 |
| `sanae` | 2 | 551 | 12 |
| `suika` | 2 | 134 | 8 |
| `suwako` | 2 | 863 | 9 |
| `tenshi` | 2 | 118 | 9 |
| `udonge` | 2 | 36 | 8 |
| `utsuho` | 2 | 659 | 8 |
| `youmu` | 2 | 25 | 8 |
| `yukari` | 2 | 56 | 8 |
| `yuyuko` | 2 | 112 | 9 |

## Carpetas de escenario

| Carpeta | Archivos |
|---|---:|
| `bg10` | 29 |
| `bg11` | 30 |
| `bg12` | 27 |
| `bg13` | 24 |
| `bg14` | 30 |
| `bg17` | 21 |
| `bg30` | 30 |
| `bg31` | 30 |
| `bg32` | 30 |
| `bg33` | 26 |
| `bg34` | 94 |
| `bg36` | 29 |
| `bg37` | 28 |
| `bg38` | 13 |

## Tipos de archivo

| Extensión | Archivos |
|---|---:|
| `.cv0` | 62 |
| `.cv1` | 65 |
| `.cv2` | 10,330 |
| `.cv3` | 473 |
| `.dat` | 33 |
| `.ogg` | 25 |
| `.pal` | 181 |
| `.pat` | 65 |
| `.psd` | 1 |
| `.sfl` | 48 |

## Límite de esta primera pasada

El manifiesto prueba qué recursos están presentes; todavía no indica cuáles se usan en cada estado, escena, clima o efecto. `common` y `namazu` aparecen como carpetas de personaje en los DAT y requieren clasificarse como recursos compartidos o contenido especial antes de fijar el número de personajes jugables. La siguiente fase resolverá referencias desde PAT, CSV, scripts de escena y despachadores del ejecutable de referencia exportados con Ghidra.
