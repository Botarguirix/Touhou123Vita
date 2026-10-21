# Iteración 2.29: ejecución del dispatch Suika 623C

Fecha: 2026-10-17.

Se agregó `tools/x86_suika_623c_dispatch_probe.py`, que ejecuta desde `0x60a45c` código original del PE fijado (`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`). Se inyecta `Player+0x7c8=0x400` para entrar al branch 623C; el código original consulta niveles y move-locks y el probe observa los argumentos de las llamadas a `useSkill`.

Resultados reproducibles:

- `Player+0x6ad=1`: consulta moveLock(531), selecciona acción 531.
- `Player+0x6ad=0`, `Player+0x6a9=1`: consulta moveLock(526), selecciona acción 526.
- ambos niveles en 0: consulta moveLock(521), selecciona acción 521.
- ambos niveles en 1 con el fixture de moveLock rechazando (`0xffff`): consulta 531, 526 y 521 y no activa acción.

El test coteja la presencia de las tres acciones en el PAT de Suika. El parser informa respectivamente que 531 tiene dos variantes sin cajas/daño directos, 526 una variante con una pose dañina, y 521 siete variantes con dos poses dañinas. Esto solo delimita qué datos seguir después del dispatch; todavía no explica las secuencias, objetos ni el primer impacto.

El dispatch probe ahora ejecuta también el cuerpo original de `useSkill` y captura su solicitud al límite virtual `setAction`; solo esa función virtual y el reseed quedan controlados en esa corrida. La regresión `x86_skill_use_oracle.py` pasó 5/5 y confirma que el primer argumento llega al setter. No hay cambios de runtime ni VPK. Sigue pendiente producir el bit con matcher/ring buffer, y la inicialización PAT corre en una sonda separada. Reporte local: `artifacts/x86-suika-623c-dispatch.json`.

La prueba siguiente enlazó esas acciones con el setter, initializer y update originales de Suika, usando el vtable real y los nodos/frame data del DAT. El lookup de acción y secuencia PAT (`0x43f2f0`) también se ejecutó sin stub. Tras el setter, las tres acciones quedaron en seq.0/pose0 con 6, 12 y 16 poses respectivamente. Para 521, el update x86 recorrió 31 ticks hasta que la secuencia 4 llevó EIP a cero; antes de eso observó seq.1/pose0 con daño 400 y una caja en el tick 12, y seq.3/pose0 con daño 600 y una caja en el tick 30. Las rutas 526 y 531 retornaron a EIP 0 después de 29 y 20 ticks, antes de alcanzar un impacto directo. Esto prueba dos estados ofensivos del código/datos originales para 521, pero la falta de constructor, manager y estado de pelea en la fixture limita las transiciones posteriores.

El test `tests/test_x86_suika_action_setter_probe.py` compara los conteos iniciales con PAT y comprueba ambos frames ofensivos. Las pruebas focalizadas de selección, setter y rutas de skills pasaron 7/7; el probe `useSkill` separado pasó 5/5. La suite completa de 48 pruebas del estado anterior pasó antes de estos últimos cambios y se volverá a correr. Entrada/matcher original, constructor completo, objetos y combate de pareja siguen pendientes. Próximo: reconstruir el fixture de Player/manager requerido por las rutas que terminan en EIP 0, y después sustituir el bit 623C inyectado con el matcher/ring buffer original.
