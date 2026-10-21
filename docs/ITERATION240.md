# Iteración 2.140: sondas de combate distinguen PAT crudo y efectivo

Al preparar la geometría x86 para las rutas C sin impacto, detecté que `action_sequence_metadata()` enumeraba registros PAT repetidos aunque `t123_pattern_decode()` elimina las definiciones anteriores al encontrar nuevamente la misma acción. Cambié la API del extractor para preservar por defecto la vista cruda de inventario y admitir `effective=True`; el probe x86 de pareja ahora usa esa vista efectiva para ataque, defensor y reacción. Una redefinición no cambia los índices de otras acciones.

El test sintético cubre ambas vistas y confirma la regla de reemplazo: `tests.test_extract_pat_pose_metadata`. En los PAT locales de `th123c.dat`, Suika 418 pasa de 12 registros crudos a 6 efectivos; solo el índice 2 tiene cajas ofensivas (frames 0–7, daño PAT 900). Udonge tiene 6/6 y su índice 1 está activo en frames 0–2 (850); Utsuho 4/4, índice 1 activo en frames 0, 1, 6, 7 y 8 (daño 700/1150). Hashes y detalle: [pat-action-418-effective-summary.json](../artifacts/pat-action-418-effective-summary.json).

La suite focalizada de probes consumidores pasó 17/17 y la suite completa pasó 118/118. Al principio probé reemplazar las entradas siempre; cuatro pruebas demostraron que inventarios existentes necesitan conservar los registros crudos. La API explícita separa ambos objetivos. No cambia el motor Vita ni el VPK.

Este hallazgo fija la tabla PAT efectiva, pero no recupera el selector dinámico del PE ni explica por sí solo los no impactos C. Próximo: ejecutar el setter/update original de Suika/Utsuho 418 con la entrada de dash, observar qué secuencia efectiva selecciona y comparar su hitbox transformada/tick con el runtime Vita. No inferir que índice de PAT equivale a variante elegida solo por su daño.
