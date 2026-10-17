# Cobertura de decodificación de imágenes PAT

Resultado de `resource_probe --pat-image-decode` ejecutado dentro de Vita3K con el decodificador ARM real y prioridad de DAT del runtime. Se examina cada entrada de imagen de los PAT seleccionados; `unreferenced` significa que ninguna pose decodificada usa esa entrada (incluye nombres de paleta presentes en PAT).

- PAT examinados: **22** (20 candidatos jugables, `common` y `namazu`).
- Entradas de imagen PAT: **13,210**; decodificadas: **12,444**; sin uso por poses: **765**.
- Fallos: recurso ausente **1**, paleta ausente **0**, CV2 inválida/no soportada **0**.

## Personajes candidatos del roster

| Personaje | Imágenes referenciadas | Decodificadas | Fallos referenciados | Imágenes ofensivas referenciadas | Fallos ofensivos |
|---|---:|---:|---:|---:|---:|
| alice | 504 | 504 | 0 | 148 | 0 |
| aya | 538 | 538 | 0 | 250 | 0 |
| chirno | 358 | 358 | 0 | 66 | 0 |
| iku | 511 | 511 | 0 | 156 | 0 |
| komachi | 615 | 615 | 0 | 86 | 0 |
| marisa | 785 | 785 | 0 | 271 | 0 |
| meirin | 673 | 673 | 0 | 249 | 0 |
| patchouli | 773 | 773 | 0 | 271 | 0 |
| reimu | 782 | 782 | 0 | 340 | 0 |
| remilia | 749 | 749 | 0 | 176 | 0 |
| sakuya | 550 | 550 | 0 | 45 | 0 |
| sanae | 516 | 516 | 0 | 162 | 0 |
| suika | 580 | 580 | 0 | 152 | 0 |
| suwako | 810 | 810 | 0 | 265 | 0 |
| tenshi | 576 | 576 | 0 | 95 | 0 |
| udonge | 470 | 470 | 0 | 65 | 0 |
| utsuho | 634 | 634 | 0 | 233 | 0 |
| youmu | 731 | 731 | 0 | 133 | 0 |
| yukari | 530 | 530 | 0 | 103 | 0 |
| yuyuko | 504 | 504 | 0 | 58 | 0 |

## Referencias utilizadas con fallo

| Personaje/PAT | Índice | Imagen | Poses | Poses ofensivas | Estado |
|---|---:|---|---:|---:|---|
| common / `data/character/common/common.pat` | 0 | `000 hikakuyou.bmp` | 31 | 0 | `missing_resource` |

Las 20 carpetas candidatas no presentan imágenes de poses ofensivas ausentes o no decodificables en esta pasada. El PAT compartido `common` conserva una referencia no ofensiva que no resolvió el loader (`000 hikakuyou.bmp`); requiere rastrear su consumidor/recurso de otra versión. `namazu` se audita aparte y no se cuenta como personaje jugable.

Esta prueba confirma decodificación de las imágenes referenciadas por las secuencias PAT cargadas, no que todos los movimientos sean alcanzables ni que la composición visual sea idéntica a PC. Las imágenes sin referencias desde poses no se contaron como fallos de sprite.

Fuente local ignorada por Git: `artifacts/pat-image-decode.tsv`.
