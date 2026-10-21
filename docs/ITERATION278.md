# Iteración 2.178: el PE carga las tablas Story de los 20 personajes

El flujo `0x432bb0–0x43332f` construye el path `data/csv/` + nombre del personaje + `/story.csv`. El nombre sale de `0x43f3f0` usando el índice actual. El loader `0x40f370` abre el recurso; el código procesa sus filas y consulta `0x43f440` sobre un campo de cadena para resolverlo mediante el mapa global. El bucle incrementa el índice y compara con `0x14`, volviendo a `0x432bb0`; así recorre los 20 IDs principales y carga, entre otros, `data/csv/meirin/story.csv`.

Esto establece el puente **CSV de campaña → loader/parser de Story** para la tabla que contiene `4,"Namazu",5,3`. El enum SokuLib y el factory siguen corroborando el ID 21. No establece todavía qué fila/stage queda activa durante una sesión ni cómo ese resultado llega a los argumentos del constructor genérico `0x45ef50` y al slot 3 del factory. Sus tres callers conocidos siguen en contexto de parsing `<br>` o claves `win`/`lose`; falta seguir la estructura compartida y sus writers/readers.

`tests/test_story_namazu_source.py` ahora fija el path, el loader, la consulta de cadena, el límite de 20 iteraciones, el registro Meiling y el flujo PE de creación. Prueba focalizada y `py_compile` pasan. La extracción usa el CSV local decodificado CP932 y la tabla del índice; no se pudo repetir la extracción `shady-cli` desde cero, ni se ejecutó una partida original. Sin cambios en runtime/VPK.

El seguimiento posterior identificó registros clave/valor de 24 bytes y los consumidores de progreso `0x42f5e0`/`0x42f680`; los detalles y límites están en [ITERATION280.md](ITERATION280.md). Eso aún no enlaza stage activo con el rival ni con `0x45ef50`.
