# Iteración 1.18: la cola conserva una ventana precargada

**Corrección:** la iteración 1.19 localizó la ruta de siembra. La interpretación de que aún faltaba encontrar quién precarga el ring quedó superada; ver [ITERATION23.md](ITERATION23.md).

Esta iteración no cambia el runtime Vita. Reexaminé el supuesto caller `0046d939` y la aritmética de inserción/eliminación del deque en el PE 1.10a fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.

## Corrección de referencias

`0046d939` no es una llamada externa al helper `0046d050`: está dentro de la función más amplia de edición de rango que termina en `0046d944`. El código anterior ya había mostrado el epílogo `ret 8`; el desensamblado desde `0046d8b0` confirma que, antes de ese epílogo, el mismo método crea iteradores/rangos y llama a `0042bc40` para manipular el deque. La tabla `player-input-callers.tsv` es un barrido lineal y este resultado muestra por qué sus candidatos no deben tratarse como xrefs de Ghidra confirmados.

## Invariante del ring por frame

El productor `0042cf90` añade una muestra de 16 bits e incrementa `deque+0x10`. Inmediatamente después, `0046d5d0` avanza `deque+0x0c` y decrementa `deque+0x10` cuando es distinto de cero. Si el deque parte vacío, append y decremento lo dejan vacío. Si contiene N muestras, al final de cada update conserva N muestras y avanza una posición: esto es consistente con una ventana de longitud fija inicializada con muestras neutrales, no con un historial que crece por sí solo.

El constructor de Player `0046c330` pone a cero `this+0x7b4`, `+0x7b8`, `+0x7bc` y `+0x7c0` en `0046c43d–0046c455`, pero esta observación no demuestra cómo se vuelve a cargar la ventana durante inicialización de ronda/entrada a combate. El productor real del ring se llama desde ambos caminos de actualización de jugadores que aparecen en `0047ff82/8a` y `00482245/4d`; no se debe implementar la retención hasta localizar la precarga o un estado alternativo que la active.

## Siguiente trabajo

1. Seguir el flujo desde carga de personaje y comienzo/reset de ronda hasta los dos dispatches de `0046d5d0`, y localizar quién escribe o copia `Player+0x7b4..0x7c0` después del constructor.
2. Decompilar los wrappers de deque `0042ca80`, `0042b930`, `0042b9b0` y `0042bc40` con xrefs de Ghidra que pertenezcan a funciones reconocidas; el candidato `0046d939` debe mantenerse clasificado como call interno de edición de rango.
3. Capturar una traza de estados iniciales y por frame (head, cantidad, muestras) en el juego original o en una instrumentación x86 antes de implementar el matcher en Vita.

La instancia local de Ghidra pudo abrir una copia aislada del proyecto, pero el exportador `ExportKernel.java` falló al cargar como script en Ghidra 12.1.4; no se generaron xrefs nuevos con ese intento y el proyecto compartido/original no se alteró. No hubo cambios de código de runtime ni VPK nuevo.
