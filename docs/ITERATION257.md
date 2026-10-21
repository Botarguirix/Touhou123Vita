# Iteración 2.157: grafo efectivo de action97 es un anillo sin terminal

La sonda ahora exporta los enlaces del grafo PAT de action97 en memoria, antes de cualquier mutación diagnóstica. Los nodos efectivos son `0→1→2→3→0`; sus enlaces previos son `0←3`, `1←0`, `2←1`, `3←2`. Los modos de frame son `[0, 0, 1, 0]`: solo seq.2 repite su frame, mientras que la lista de secuencias sigue siendo circular.

Esto conecta la topología con el gate del PE: `0x464bf0` solo devuelve terminal si el nodo actual no tiene enlace previo (`node+0x18 == 0`). Ninguno de los cuatro nodos cumple esa condición. Por eso el handler local de action97 no llega a solicitar action98 simplemente avanzando el grafo, incluso si se apaga artificialmente el loop de frames de seq.2. La transición observada en juego debe depender de estado/callback de combate externo o de otra variante efectiva del PAT; todavía falta capturar cuál en un flujo natural.

Como búsqueda estática complementaria, se recorrieron los bytes de todas las secciones ejecutables del PE buscando el literal `push 0x62` seguido de llamada. Solo apareció el callsite `0x4851fe`, dentro del handler de action97. Esto no excluye setters con argumento calculado, cargado de tabla o un callback virtual, pero no hay otra solicitud literal inmediata de action98 en ese barrido.

Se conservan los límites: el grafo está construido con el PAT de Suika fijado por el harness; el piso, el manager de ronda, efectos y condiciones del combate siguen controlados o ausentes. No se afirma paridad de recuperación ni cambio al runtime Vita.

Verificación: el reporte incluye nodos, punteros, links y loop bits; la prueba focal fija el anillo y los cuatro modos. `python -m unittest tests.test_x86_suika_constructed_handler_probe -v`, `py_compile` y `git diff --check` pasan.

Evidencia: [reporte x86](../artifacts/x86-suika-constructed-handler.json), [sonda](../tools/x86_suika_constructed_handler_probe.py), [prueba](../tests/test_x86_suika_constructed_handler_probe.py), [análisis del gate](ITERATION256.md).
