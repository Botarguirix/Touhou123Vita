# Iteración 1.76: alcance CFG del update 808 y campo `+0x34c`

Se agregó a `tools/analyze_object_motion.py` un recorrido de flujo de control desde el handler 808 que la tabla real selecciona (`0x788d3e`). El recorrido parte del PE fijado por SHA-256, sigue ramas condicionales/directas, continúa tras llamadas y corta los saltos indirectos. Encuentra 219 instrucciones alcanzables; calls directas relevantes incluyen `0x438c60`, `0x48ce90`, `0x48ce30`, `0x4397f0` y `0x4099f0`. `0x438fc0` no es alcanzable desde esta entrada. La llamada `0x48ce90` era descrita como helper de colisión en esta iteración; la Iteración 1.79 corrige esa interpretación: consulta el action del owner y puede generar efectos `0xc8/0xc9`, mientras `0x4397f0` es la consulta del piso. Por ello se corrige también el texto de Iteración 1.75 que especulaba que `0x438fc0` entregaba las cajas del hijo; sus referencias en `0x789ed2/0x789f0e` están en otra ruta.

El probe de 40 ticks además conserva el entero raw `object+0x34c`. La factory/constructor lo retorna en 1. El tick 31 baja alpha de 15 a 7 y deja el campo en 1; el tick 32 toma la salida `alpha<8`, retorna EAX=7 y reduce el campo a 0. El constructor base `0x4adcc0` inicializa `+0x34c=1`. Al llamar manualmente el dispatcher una vez más, el harness observa `0xffffffff`; esas llamadas no incluyen el manager que normalmente decide si un objeto sigue actualizándose, así que el subdesbordamiento no representa la partida real. `+0x34c` era candidato a señal de fin/refcount al cerrar la iteración; la Iteración 1.78 encontró el consumidor exacto: el iterador `0x633c10` elimina la entrada cuando el callback la deja en cero. La pasada dinámica integrada con constructor, pool y handles reales sigue pendiente.

La prueba `tests/test_object_motion_analysis.py` verifica el CFG: el helper de estado `0x48ce90` y la consulta de suelo `0x4397f0` sí son alcanzables; el adaptador geométrico `0x438fc0` no. Suite completa y artifacts deben regenerarse antes de aceptar un cambio posterior.

## Próximo gate

1. Identificar el consumidor de `object+0x34c` en la iteración del manager y comprobar el comportamiento del objeto tras llegar a cero en una ejecución que incluya esa capa.
2. Seguir la colisión/impacto de GameObject desde el loop de combate hasta las cajas PAT o bounds dinámicos, incluidos los hijos seq.1 que no tienen cajas PAT explícitas.
3. Solo con spawn, hit y borrado demostrados, reemplazar la aproximación provisional del motor Vita y generar una regresión VPK para Vita3K.
