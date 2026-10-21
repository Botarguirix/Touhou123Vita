# Iteración 2.115: la fila seleccionada toma la rama del loader replay

Se extendió el probe SHA-pinned del PE 2009 original (`24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`) y se inspeccionó el update del menú en `0x449fe0`.

El método comprueba el estado activo de selección (`[edi+8] == 1`), obtiene el índice de fila y consulta `0x43ba50`. Ese getter valida el índice contra el tamaño del contenedor y lee el byte de tipo asociado a la fila. Si el flag no es cero, el handler actualiza/navega la lista; si es cero, lee las dos cadenas del elemento seleccionado con `0x43b9f0` y `0x43b620`, las formatea y llama a `0x42e030`. Si el loader acepta el archivo, el flujo solicita la transición y escribe estado título 6.

Esto confirma estáticamente qué rama carga un elemento normal seleccionado dentro del catálogo `CReplayList`, cuyo filtro/raíz y convención Story están fijados en Iteración 2.114. No determina qué botón físico produjo el estado activo ni sustituye una traza dinámica; tampoco prueba aún cursor/cadencia de playback por tick.

Verificación: `python -m unittest tests.test_replay_manager_selection_probe` pasa (1/1); 46 condiciones estáticas del PE pasan y se regeneró `artifacts/kernel/replay-manager-selection-original-2009.json`. No hubo cambios al runtime/VPK ni corrida Vita3K.

Siguiente: observar una sesión frame-stepped del PE 2009 al seleccionar `090815_2219_sanae_story.rep`; registrar estado de menú, ruta pasada a `0x42e030`, estado/cursor al iniciar combate y avance por tick. Después integrar el consumo temporal medido en el runtime Vita y validarlo en Vita3K.
