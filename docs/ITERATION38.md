# Iteración 1.34: metadatos PAT de Suwako 418

El recorrido x86 del setter y su adaptador muestra que las dos componentes de origen del registro del frame (`+0x0c/+0x0e`) alimentan `stage+0x9c/+0x98`. El stride de 28 bytes seleccionado por el índice de frame concuerda con el descriptor de frame que el loader construye a partir del PAT; en el formato PAT local esas dos componentes son `ox/oy` y el parser existente las conserva en `T123Pose`.

Añadí `tools/extract_pat_pose_metadata.py` para leer el PAT directamente de los DAT locales del usuario, descifrando solo su tabla y entrada solicitada. Para `data/character/suwako/suwako.pat`, acción 808, secuencia 0:

| DAT | Prioridad | Frames | Offsets (ox, oy) |
|---|---:|---:|---|
| `th123a.dat` | 2 | 10 | (64, 58) en los diez frames |
| `th123b.dat` | 3 | No contiene el PAT | — |
| `th123c.dat` | 1, gana en el loader | 10 | (64, 58) en los diez frames |

Los hashes del PAT son `82ed61db09bcfa2da1abdcd8f7e4e5c84e3101a60eaf137df8a981832743fb70` (A) y `1e7e06920e9a7a0e8b0ee0fc160a5b2dd3a19f2cdba2ba8144ab969d0a9dc906` (C). Esto confirma los datos del recurso prioritario que usa el loader y proporciona los valores de origen del sprite. Todavía no demuestra que el frame 808 sea el descriptor activo que lee el setter durante la creación, ni el sistema de coordenadas del campo `object+0x37c`. Por eso el movimiento Vita conserva sus valores provisionales hasta verificar esa conexión en la ruta `0076f3b4` y su llamada `createObject` `0046eb30`.

La herramienta se ejecutó sobre los DAT locales; la suite Python del proyecto pasó 8/8 y `git diff --check` no encontró errores. No se recompiló VPK en esta iteración porque solo se añadieron herramientas y evidencia de recursos.

Siguiente paso: relacionar la rutina de actualización de frame, el puntero de descriptor usado por `0076f3b4` y los valores enviados a `0046eb30`; después incorporar coordenadas ya probadas y medir trayectoria/impacto frente a una traza x86.
