# Iteración 2.168: fetch inválido identificado en el callback del timer

Se identificó que el fetch `0x0` tras 181 updates válidos no lo genera el retorno de `0x606aae`/`0x606abe` ni la secuencia PAT de action96. El epílogo del updater devuelve al sentinel correcto del harness (`ESP=0x200e600`, `[ESP]=0x03000000`). En el tick 182, el fetch ocurre durante la llamada al timer `0x46a330`, antes del input/updater.

La traza termina en `0x463b69: call eax`: tras acumular `Player+0x4a4 >= 0x12c0`, el PE consulta el singleton global `0x8985e8`, toma su objeto y llama el callback virtual `object+0x18`. El harness no ha construido ese manager/callback, por eso `EAX=0` lleva a fetch nulo. Así se resuelve el diagnóstico previo: no era stack corrupto ni prueba de final/bloqueo de action96. Action96 continúa activa, y no hay escritura a `Player+0x884` en las 181 actualizaciones; hace falta reconstruir el singleton dependiente del timer para avanzar con una corrida auténtica.

Se añadió al artefacto la fase exacta del fetch y la pila del epílogo; el test exige ambos hechos. El probe PE pasa. Sin cambios en runtime Vita ni VPK.

## Siguiente

Localizar por xrefs quién inicializa `0x8985e8` y su objeto/callback `+0x18`, reproducir esa inicialización en el harness, y repetir el avance de action96 más allá del umbral `0x12c0`. Después continuar el call graph de quien escribe positivamente `Player+0x884` y validar recuperación con el ciclo de combate real.
