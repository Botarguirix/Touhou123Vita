# Iteración 2.112: CTitle state 12 solicita el manager Story

Se extendió la sonda con la RTTI y la tabla de estados de la pantalla título del PE original 2009, SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`.

La vtable `0x820f9c` se identifica por Complete Object Locator/TypeDescriptor como `CTitle`, con bases `CSceneBase` e `IScene`; su slot 1 apunta al handler `0x426d50`. Ese handler lee `[0x848a94]`, usa la tabla de saltos `0x427218/0x427200` y para estado 12 entra en `0x426de2`. Ese bloque empuja estado 2 y modo 6 al setter `0x43d8e0`. Los estados adyacentes 8 y 9 seleccionan modos 4 y 5, ambos con estado 1.

Al combinarse con la RTTI de managers de [ITERATION201.md](ITERATION201.md), esto demuestra una ruta estática desde `CTitle` hacia la selección del manager Story (modo 6) y el estado 2 que habilita el callback Story. Es una conexión más fuerte que el callsite aislado: el selector sí pertenece al dispatch de estados de la pantalla título. Aún no demuestra que el estado 12 corresponda específicamente a elegir un replay, que el archivo Sanae lo tome, qué backend deja activos sus slots, ni la cadence por frame.

La prueba `tests.test_replay_manager_selection_probe` pasó 1/1, los 36 contratos de la sonda pasan y `git diff --check` no reporta errores. Reporte actualizado: `artifacts/kernel/replay-manager-selection-original-2009.json`. Runtime y VPK sin cambio.

Siguiente: seguir qué acción/elemento de `CTitle` asigna estado 12 y cómo se carga el registro `.rep` desde `replay/story`; después obtener la traza de cursor por tick antes de conectar playback al combate Vita.
