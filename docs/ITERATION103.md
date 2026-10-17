# Iteración 2.03: initializer, update y daño PAT del objeto 801

Se resolvió el ID 801 (`0x321`) en los dos mapas de acción de objeto del PE fijado. El índice es `801 - 0x320 = 1`: el mapa de initializer `0x79ecd8` selecciona grupo 1 y handler `0x7991a5`; el mapa de update `0x798b70` también selecciona grupo 1 y handler `0x7879da`. El update dedicado procesa secuencias 0–3 y crea objetos desde el callback del dueño bajo condiciones de fase/posición, así que hay una posible ruta de ataques múltiples que debe validarse con estado persistente.

El PAT efectivo de Remilia (`data/character/remilia/remilia.pat` de `th123c.dat`) sí define action 801. Su seq.0 contiene 20 poses, daño 120 y caja ofensiva en las 20; seq.1 contiene dos poses sin daño ni cajas; seq.2 contiene 20 poses, daño 100 y caja ofensiva en las 20. No hay cajas de colisión ni hurt en estas secuencias. Esta evidencia confirma que 801 es un ataque capaz de dañar, y lo convierte en candidato real para el 2C; no equipara sus daños 120/100 con los 750 de la pose PAT del dueño ni prueba cuántos impactos ocurren.

La primera ejecución dinámica de factory/update quedó en [ITERATION104.md](ITERATION104.md): el factory crea action 801 y tres ticks originales corren, pero un servicio de host no inicializado detiene el cuarto antes de demostrar la vida completa o el daño.

Siguiente: resolver ese servicio y continuar el update con la secuencia/setup que entrega la rama 412; capturar hijos y primer contacto para determinar si el daño total observado corresponde a la acción 412. No se modifica el runtime Vita ni se genera VPK.

Evidencia: `artifacts/kernel/remilia-object801-initializer-dispatch.tsv` y `artifacts/kernel/remilia-object801-handlers.tsv` (ignorados; PE SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`); PAT leído de `original/th123c.dat` con `tools/extract_pat_pose_metadata.py`.
