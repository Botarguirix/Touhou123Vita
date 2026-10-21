# Iteración 2.103: el selector de modo tiene dos rutas Story

La sonda [`x86_replay_manager_selection_probe.py`](../tools/x86_replay_manager_selection_probe.py) verifica el selector `0x43cca0` y las inicializaciones en el PE 2009 fijado por SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`.

El selector consulta `[0x85ec10]`. El caso `0` salta a `0x43b440` y el caso `6` a `0x4378d0`; ambos inicializadores construyen el objeto con vtable `CBattleManagerStory` (`0x82192c`) y lo publican en el global `[0x85eb64]`. Los otros modos toman rutas distintas. Esto acota qué inicializador sería usado una vez conocido el valor runtime, pero el nombre del directorio `replay/story` no revela por sí solo si el selector vale `0` o `6`.

También se trazó el escritor de flags `0x42d6b0`: en la ruta observada desde `0x4281a2`, el receptor viene del getter `0x43cec0`, que devuelve el global separado `0x85ec98`. El escritor calcula su byte `+0xf0` según la presencia de fuentes en los offsets `+0x24` y `+0x44`, y reconstruye sus estructuras mediante `0x42d420`. Esto confirma que ese byte expresa fuentes disponibles en ese objeto de input; no prueba que el receptor sea el objeto cuyo `+0xf0` consulta el decoder `0x42a410` durante replay. La sonda de decoder mantiene explícitamente `f0=3` como una condición del harness.

El resultado separa el selector del manager (modos 0/6), el puntero global al manager Story y el estado global de input. Aún faltan el modo efectivo durante la reproducción Sanae, la identidad/flags del objeto entregado al decoder y la relación entre consumo de words y tick. No se conectó playback al combate ni se cambió el runtime Vita.

La regresión `tests/test_replay_manager_selection_probe.py` fija las ramas estáticas y sus límites. El siguiente paso es resolver quién establece `[0x85ec10]` al entrar al replay y seguir la ruta del callback Story hasta el objeto usado por `0x42a410`; luego medir cadence con frame-step del PE.
