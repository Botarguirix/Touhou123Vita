# Iteración 2.162: métodos Suika sin writer directo y acción 96 confirmada en PAT

## Búsqueda estática ampliada

Se recorrieron los 48 punteros consecutivos desde el vtable Suika `0x85da84` del PE fijado, usando un CFG básico por entrada: sigue fallthrough y saltos condicionales/directos dentro del método, registra llamadas directas sin entrar a sus callees y busca operandos de memoria con displacement `0x884`. Ninguno de los slots escaneados produjo una referencia. El mismo recorrido aislado para los slots 10 (`0x5ee620`), 15 (`0x6086a0`) y 20 (`0x609dc0`) también dio cero referencias.

Este resultado es más específico que el barrido lineal anterior, pero no excluye accesos por código alcanzado mediante `jmp/call` indirectos, helpers directos compartidos que no se recorrieron, managers, ni alias/acceso calculado al campo. No se atribuye el writer a un componente concreto. El writer estático `0x490795` sigue clasificado aparte como Reimu.

## Acción 96

El PAT efectivo de Suika contiene para action96 una secuencia 0 de diez frames, sin daño. Se ejecutó el constructor `PlayerSuika`, el setter PE `0x464930(96)`, el timer común `0x46a330` y el update virtual `0x5ee620` durante 60 ticks. El setter acepta action96 y la ejecución no falla. El primer ciclo recorre frames 0–9; desde aproximadamente el tick 30 aparecen índices de secuencia 1 y luego 3 mientras action sigue en 96. Esos índices no forman parte de las definiciones efectivas que leyó el extractor para action96; por ello no se trata esta fixture como prueba de la secuencia completa ni del resultado natural del movimiento.

La acción 96 es una acción PAT real y ejecutable, pero aún no está probado que sea levantamiento: la activación previa depende de forzar `+0x884`, el manager/estado de ronda no está integrado, y la animación posterior sale de las secuencias PAT efectivas esperadas. Hace falta el contexto original de manager y el grafo runtime de secuencias antes de implementarla en Vita.

## Siguiente paso

Seguir las escrituras del campo en helpers compartidos y manager de combate mediante call/xrefs y dispatch indirecto; ampliar el fixture con ese contexto, no inventar las secuencias 1/3 de action96. Mantener sin cambios el runtime Vita y VPK hasta tener la transición natural y la salida de recuperación verificadas.
