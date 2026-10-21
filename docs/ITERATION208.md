# Iteración 2.108: el backend del selector 6 no prueba dos fuentes activas

Se extendió `tools/x86_replay_manager_selection_probe.py` para decodificar la tabla de `0x43dee0` en el PE original 2009 (SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`). El dispatcher indexa la tabla `0x43e248` con `[0x85ec10] - 1`. Para el selector 6, índice 5, el destino es `0x43e122`, una ruta común que no escribe directamente los slots de fuente `0x8602ac` y `0x8602cc`. En cambio, selector 3, índice 2, llega a `0x43e0a0`, donde sí se asignan explícitamente `0x85ef20` y `0x85f70c` a esos dos slots.

Esto precisa la evidencia anterior sobre modo 6: `0x43d310` inicializa dos slots internos del manager Story (`+0x1f0/+0x1f8`) y el setter enlaza el objeto global `0x85ec98`, pero eso no demuestra que las dos fuentes de backend estén activas. El byte `+0xf0` del objeto entregado al decoder depende del estado de configuración apuntado por `0x860288`; el dispatcher del modo 6 no fija por sí solo las dos fuentes. Se mantiene injustificado asumir `f0=3` como valor natural del playback.

La prueba focalizada `tests/test_replay_manager_selection_probe.py` ahora verifica el índice y destino de cada rama, la ausencia de escrituras de slots en la ruta común 6 y las asignaciones explícitas en la rama 3. El runtime Vita y los VPK no cambian.

Siguiente: seguir quién prepara `0x8602ac/0x8602cc` y cuándo ejecuta el escritor `0x42d6b0` respecto al selector/callback Story; luego obtener una traza de frame-step que relacione el cursor con ticks antes de conectar playback al combate.
