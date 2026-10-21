# Iteración 2.116: el ciclo llama al update Story; cadence de replay sin cerrar

Se amplió la sonda fijada al PE original 2009 (`24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`) para seguir el dispatcher `0x43d480`.

El dispatcher selecciona una tabla por `[0x85ec0c]`; el caso 3 salta a `0x43d4ca`, prepara el objeto de input y llama a `0x437790`. Ese wrapper lee el manager global `[0x85eb64]` y despacha su slot virtual 1. El vtable Story `0x82192c` asigna ese slot a `0x47eaa0`. La Iteración 2.118 precisa que esta cadena de estado no demuestra el tick de combate: el slot 1 es distinto del slot 5 (`0x47f810`), que sí invoca el callback de replay.

El callback Story de replay `0x47ee10` es un método virtual distinto, slot 16 del mismo vtable; con el estado consultado en `0x43ced0` igual a 2 obtiene el objeto global de input y llama al decoder por pares `0x42a410`. Así, el update del manager Story sí está en la ruta del dispatcher de ciclo, y el callback del decoder se identifica en la misma clase. El análisis estático actual no establece cuántas veces se invoca el slot 16 por update, tick simulado o frame renderizado; tampoco confirma la cadence del juego mediante una sesión activa.

En el momento de la comprobación no había proceso `th123` activo. Había procesos Vita3K; se dejaron intactos. Verificación entonces: `python -m unittest tests.test_replay_manager_selection_probe` pasa (1/1); 49 condiciones del reporte pasan. Se regeneró `artifacts/kernel/replay-manager-selection-original-2009.json`. Runtime y VPK sin cambios.

Siguiente: localizar el call virtual del slot 16 desde el update Story/dispatcher y distinguirlo de callbacks de escena; después medir una ventana frame-stepped del PE 2009 para correlacionar word cursor, updates de simulación y frames renderizados. La muestra Sanae tiene tres peleas; no asumir correspondencia 1:1 entre pares y ticks.
