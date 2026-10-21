# Iteración 2.180: campos y consumidores de los registros Story

Seguí la estructura del parser y el actualizador de progreso, sin atribuirles una selección de stage que el PE no demuestra:

- El parser `0x432bb0–0x43332f` procesa cuatro campos por fila. En `0x4330b6` resuelve una clave mediante `0x43f440`; busca pares en registros de 24 bytes (`0x18`) comparando el campo `[+0]` con la clave y `[+8]` con el valor numérico. Si no encuentra el registro, `0x4331c2` llama a `0x430e20` para insertarlo.
- `0x42f5e0` selecciona un vector en `this + 0x1a4 + index*0x10`, busca el mismo par de claves y aumenta `[registro+0x0c]`. `0x468de0` es su único caller directo localizado: bajo el flag `this+0x5e6`, obtiene valores de campos y pasa el singleton `0x899f60` (retornado por `0x43df50`) al updater.
- `0x42f680` actualiza otro contador, `[registro+0x10]`; sus callers directos son `0x468fa6` y `0x51dd45`.

Esto prueba que el CSV alimenta registros clave/valor y que el manager Story actualiza contadores asociados a pares de claves. No identifica cuál de esos campos representa el stage activo ni prueba que una fila del CSV seleccione el personaje del combate. `0x45ef50` sigue siendo un constructor genérico usado por rutas de diálogo (incluidas claves `win`/`lose`); no se ha establecido un enlace desde el progreso hasta el factory del rival. Namazu está confirmado como contenido de la etapa 4 de Meiling y como destino del factory ID 21, pero su spawn en una sesión real aún no está observado.

Se amplió `tests/test_story_namazu_source.py` para fijar el tamaño/offset de los registros, el par de claves del updater, los callers directos y el retorno singleton del resolver. La prueba es estática sobre el PE local identificado por su hash en el test; no sustituye instrumentación dinámica del juego original. Sin cambios de runtime ni VPK.

Siguiente: determinar qué selector entrega el índice de campaña/stage al manager Story y observar la llamada al factory al cargar Meiling stage 4. Si el PE no expone ese flujo sin iniciar el juego, ejecutar la versión original con breakpoints/log de argumentos en `0x46ead0` y `0x46da40`; luego contrastar la construcción de Namazu, carga PAT y combate contra su rival real.
