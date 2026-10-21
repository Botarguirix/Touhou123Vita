# Iteración 2.94: campos de variante en poses PAT con recortes extremos

La auditoría por personaje de `th123c.dat` encontró ocho frames con `tx/ty` no cero entre 17,586 secuencias. Corrijo la clasificación anterior: siete referencian `alpha000.bmp`, pero Sakuya action 40/seq.0/frame0 usa `attackAa000.bmp`. Los flags también varían (0, 1 y 2), así que no forman una única ruta identificada por imagen o byte de variante.

Ejemplos extraídos:

- Marisa 47/0/frame0: `alpha000.bmp`, `ty=-19704`, `tw=10876`, `th=19704`, flags 1. El frame siguiente usa `alpha000.bmp` con 64×64.
- Alice 304/0/frame0: `alpha000.bmp`, `ty=-25016`, `tw=10876`, `th=25016`, flags 0. Los frames siguientes son 256×256.
- Sakuya 40/0/frame0: `attackAa000.bmp`, `ty=-720`, `tw=16044`, `th=720`, flags 1. El frame siguiente usa el mismo nombre con 64×128.

El extractor [`extract_pat_pose_metadata.py`](../tools/extract_pat_pose_metadata.py) ahora incluye `flags` y los 16 bytes extra en hexadecimal cuando el flag vale 2. La lectura confirma el bloque especial estructuralmente, pero aún no sabemos si estos cuadros representan una fase invisible, un sentinel, un efecto de textura o una forma especial de UV. No se altera el runtime ni se atribuye comportamiento sin seguir el camino en el PE.

Siguiente paso: construir una sonda x86 pequeña que seleccione esos descriptores mediante el setter/selector original, observe las llamadas al initializer de sprite `0x466720` y capture el componente generado por `0x406c60`. Luego determinar si el renderer PC emite el draw y con qué límites/sampler; usar ese resultado para decidir si se debe omitir el cuadro o soportar una convención especial en Vita.
