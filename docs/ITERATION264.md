# Iteración 2.164: action96 y action97 comparten el handler x86 de caída

Se resolvieron por separado las dos tablas indirectas del PE fijado (`f0db9366…`):

- El updater común `0x483f40` indexa `byte[0x486e3c + action - 0x32]` y salta por `dword[0x486d80 + index*4]`. Tanto action96 como action97 llegan al handler `0x485115`; action98 llega a `0x4852a0`.
- El callback de cambio de acción que parte de `0x48b210` tiene su propio mapa/tabla. Action96 cae en el handler vacío/default `0x48be20`; action97 va a `0x48b85f` (el consumer de `+0x884`); action98 a `0x48b8f6`.

Esto explica una parte importante del probe: action96 no tiene un update independiente. Comparte el handler de caída/aterrizaje de action97. En la ejecución PE de 60 ticks, al seguir action96, en tick30 el estado llega a sequence1 y en tick31 el mismo handler alcanza el setter de secuencia (`0x4851e7`) con argumento 3. Por ello los índices de secuencia 1/3 observados no se originan en un dispatcher equivocado del harness: son la ruta común de actualización. El PAT efectivo de action96 solo define seq0 con diez frames, así que el contenido gráfico de esos estados posteriores sigue sin resolverse con el fixture.

La convergencia de handlers es evidencia de que action96 pertenece a la misma familia de estados de caída/recuperación que action97; no prueba por sí sola qué representa en gameplay ni completa su secuencia visual. El callback de action96 es default/no-op y el natural productor positivo de `+0x884` todavía falta. Añadí `tests/test_suika_recovery_dispatch.py` para fijar los targets de ambas tablas contra el PE de hash conocido.

Siguiente: rastrear qué manager/condición de combate solicita action96 o escribe `+0x884>0`, y resolver cómo se obtienen las secuencias de action96 al cambiar de estado. Sin cambios al runtime Vita ni VPK.
