# Iteración 2.159: action97 contiene otra salida condicional por `Player+0x884`

La actualización de gameplay del Player (`0x6086a0`) despacha action97 a `0x48b85f`. Ese handler compara el word `Player+0x884` en `0x48b8cf`; si es positivo, solicita action96 con el setter virtual en `0x48b8e4`. Esto es una posible salida local del estado 97 distinta del avance PAT, pero aún no hay evidencia de que action96 signifique levantamiento.

En la fixture actual `Player+0x884` vale cero durante los 300 ticks post-hit. También queda en cero después de las diez entradas individuales de un tick, de modo que no se toma la rama a action96. No conocemos todavía el productor ni el significado del campo. La conclusión previa de que la salida necesariamente depende de un manager externo queda acotada: falta rastrear quién escribe `+0x884`, conectar su actualización natural y observar si la acción 96 es realmente recuperación.

La búsqueda exploratoria de operandos `+0x884` arroja múltiples candidatos por personaje y bloques; no se atribuye un productor hasta validar límites de función y una escritura dinámica. La prueba ahora fija el consumer ejecutado y el valor cero de la fixture.

Verificación: sonda regenerada con el PE fijado; suite focal de siete pruebas, `py_compile` y `git diff --check`. Sin cambios de runtime Vita/VPK.

Evidencia: [reporte x86](../artifacts/x86-suika-constructed-handler.json), [sonda](../tools/x86_suika_constructed_handler_probe.py), [prueba](../tests/test_x86_suika_constructed_handler_probe.py), [caída 74→97](ITERATION258.md).
