# Iteración 0.5: experimento de secuencia PAT

Se probó concatenar automáticamente los índices PAT de una misma acción, suponiendo que eran bloques de animación consecutivos. La suite host sintética pasó, pero la prueba nueva en Vita3K registró cero impactos (`a_hits=0`, `b_hits=0`, `c_hits=0`), aunque abrió menú, práctica y combate, cargó los 7 DAT internos y decodificó 22 texturas. La hipótesis no reprodujo el juego y se retiró.

El XML original extraído muestra que índices como 400/401 son variantes con distinto `loop`, `movelock` y `actionlock`; no deben encadenarse sin observar el estado que elige cada índice en el juego. El VPK automático de este experimento fue `artifacts/Touhou123Vita-iter05-auto.vpk` (SHA256 `3a185abbab321073a68eccd69cc05e4cb5d53e2a0a8892cf3e75ee30f41d6af7`). No se considera una build de combate válida.
