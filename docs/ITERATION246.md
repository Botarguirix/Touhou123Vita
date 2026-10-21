# Iteración 2.146: rama interna Suika 418 y limpieza

La sonda `x86_suika_418_handler_branch_probe.py` ejecuta el bloque interno `0x60be34→0x60be83`, observa setter virtual 418 y ejecuta el limpiador original `0x46cac0`, que vacía los ocho words buffered. Esta iteración usó action=300; la auditoría posterior del prólogo mostró que el bloque real compara `BX=0xc8` (action=200). Por tanto, los seis casos originales no acreditan correctamente la rama 418 y se consideran sustituidos por la ejecución corregida de [ITERATION248.md](ITERATION248.md).

La observación estructural de que este bloque no llama `getMoveLock(418)` sigue siendo válida, pero la precondición positiva es action=200, suelo aceptado, movimiento horizontal al facing y eje vertical actual neutral. La sonda corregida usa action=200.
