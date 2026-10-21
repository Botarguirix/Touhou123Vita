# Iteración 2.158: el aterrizaje del handler 74 solicita action97

Se añadieron checkpoints al tick 10 de la sonda posterior al impacto. Tras consumir hitstop, la entrada neutral conserva action74; durante el update del personaje, el dispatcher `0x483f40` elige el handler 74 (`0x4849f6`). La rama pasa por `0x487ea0`, cuyo retorno de aterrizaje es verdadero en el escenario controlado, entra por `0x4847d4` y acaba pidiendo action97 en el setter virtual (`0x4846a5`, retorno `0x4846a7`). En ese mismo tick el update de Suika (`0x6086a0`) ya procesa action97.

Así queda diferenciada la transición de caída de la futura recuperación: action74→97 está explicada por el handler PE y el gate de suelo, no por el input neutral ni por un manager de round. La salida de action97 sigue abierta: su grafo PAT forma un anillo y no completa localmente, por lo que falta capturar la condición/caller de gameplay que abandona el loop.

La prueba fija el action en ambos lados del input/update y el orden de los PCs observados. El piso sigue controlado por el harness (Y=500 al aterrizar); esto confirma el caller y el gate PE, pero no una pelea natural ni paridad completa. Sin cambios al runtime Vita ni al VPK.

Verificación: `python tools/x86_suika_constructed_handler_probe.py` regeneró el reporte; suite focal de siete pruebas, `py_compile` y `git diff --check`.

Evidencia: [reporte x86](../artifacts/x86-suika-constructed-handler.json), [sonda](../tools/x86_suika_constructed_handler_probe.py), [prueba](../tests/test_x86_suika_constructed_handler_probe.py), [grafo action97](ITERATION257.md).
