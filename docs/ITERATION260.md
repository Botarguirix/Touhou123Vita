# Iteración 2.160: `+0x884` selecciona una rama al entrar en action97

La sonda instala el hook de memoria antes del resolver de impacto y lo mantiene durante la reacción 74, la caída y los 300 ticks. El PE no escribe `Player+0x884` en esa trayectoria; el campo permanece en cero. Ocho pruebas adicionales mantienen A/B/C/D y abajo+A/B/C/D por 24 ticks, cada una desde el mismo estado action97: ninguna escribe el campo, cambia acción ni secuencia.

Una corrida diagnóstica separada repite los primeros diez ticks desde el estado post-hit y fuerza `+0x884=1` justo antes del update de aterrizaje. El PE solicita action97 desde `0x4846a7`; durante el callback de cambio de acción, `0x6086a0→0x48b85f` ve el campo positivo y pide action96 desde `0x48b8ef`. Action96 es alcanzable bajo esa precondición artificial, pero su significado y el productor real del campo siguen sin resolverse. El resultado no prueba levantamiento natural.

Conclusión acotada: en la fixture actual, `+0x884` se consume al entrar en action97 y no actúa como timer que se actualice durante el loop. El origen debe buscarse en otra ruta del juego (por ejemplo, un servicio/manager o una condición de reacción distinta), y todavía hay que reproducirla con combate normal antes de asignar semántica a action96.

Una búsqueda lineal independiente con Capstone sobre secciones ejecutables del PE no encontró referencias decodificadas al desplazamiento `0x884`; por el entrelazado de datos/código y los dispatch indirectos no es evidencia de que no existan escritores. El vtable de Suika en `0x85da84` confirma `update=0x5ee620`, callback de acción `0x6086a0` y `handleInputs=0x609dc0`, lo que mantiene identificada la ruta consumidora, pero no clasifica el productor. No se atribuyen a Suika las referencias estáticas crudas a `0x884` sin límites de función/xrefs verificados.

Verificación: se regeneró el reporte; la regresión fija cero escrituras en la trayectoria observada, ocho casos mantenidos de 24 ticks y la rama forzada `74→97→96`. Suite focal de siete pruebas, `py_compile` y `git diff --check`. Sin cambios al runtime Vita ni VPK.

Evidencia: [reporte x86](../artifacts/x86-suika-constructed-handler.json), [sonda](../tools/x86_suika_constructed_handler_probe.py), [prueba](../tests/test_x86_suika_constructed_handler_probe.py), [caída 74→97](ITERATION258.md), [consumer `+0x884`](ITERATION259.md).
