# Iteración 2.176: la ruta Story obtiene `PlayerInfo.character` de datos CSV

Se siguió el productor usado por `0x45f176`, que entrega el `PlayerInfo` del slot 3 al helper de creación común `0x46ead0`. La rutina `0x43f440` no elige un personaje mediante una rama de gameplay: busca una clave/cadena en la estructura global de datos CSV `0x899cfc` y devuelve el valor de la fila localizada. El caller `0x45ef50` copia ese retorno en `[esi+0x858]`, campo `PlayerInfo.character`, y después solicita la creación del slot 3.

La misma búsqueda se usa al leer `data/csv/story.csv` (referencia de cadena en `0x85870c`) y ficheros bajo `data/csv/` (`0x858718`); los otros callers incluyen un loader de filas/configuración (`0x4330b6`) y código que lee texto de escenario `data/scenario/%s/ed.txt` (`0x462adf`). Esto acota el origen de un posible ID 21 a los datos/camino Story o a otra entrada que comparta el helper. El código inspeccionado no demuestra por sí solo que un CSV concreto contenga 21 ni que el caller `0x45ef50` corresponda a un modo determinado. Namazu sigue sin estar probado como selección normal.

La evidencia se contrastó en el PE local: llamadas directas a `0x43f440` en `0x4330b6`, `0x45f141`, `0x462adf` y `0x462f2b`; referencias de ruta y escritura del retorno a `PlayerInfo+0`. No se modificó runtime ni VPK.

Actualización en Iteración 2.177: `data/csv/meirin/story.csv` asigna a Namazu como rival de la etapa 4. Falta enlazar dinámicamente esa fila con el caller y la instancia de combate.
