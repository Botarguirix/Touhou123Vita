# Iteración 2.118: slot 5 Story llama al decoder; cadence todavía abierta

Se amplió `tools/x86_replay_manager_selection_probe.py` contra el ejecutable original de 2009 fijado por SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`. El reporte actualizado está en [replay-manager-selection-original-2009.json](../artifacts/kernel/replay-manager-selection-original-2009.json). `python -m unittest tests.test_replay_manager_selection_probe` pasa (1/1); ahora comprueba 52 condiciones.

La inspección separa tres rutas que antes estaban demasiado juntas:

- El caso 3 de `0x43d480` llega a `0x437790`, wrapper que llama el slot 1 del manager global `[0x85eb64]`; en la clase Story apunta a `0x47eaa0`. Esto establece una transición de lifecycle y no identifica el tick que procesa cada entrada.
- El slot 5 del vtable Story (`0x82192c`) apunta a `0x47f810`. Esa rutina carga el slot 16 desde `[this+0x40]` y lo llama en `0x47f82e`; el slot 16 apunta a `0x47ee10`, callback que consulta estado y alcanza el decoder `0x42a410`. Queda probado el enlace slot5→slot16 y una llamada por ejecución de `0x47f810`.
- La ruta `0x4787f0` toma un método del offset `+0x14` del objeto global `[0x85eb70]`, lo llama en `0x478844` e incrementa `[0x85eb58]` en `0x478851`. El objeto no es el manager Story `[0x85eb64]`; aún falta demostrar qué representa esa llamada dentro del playback y si su contador coincide con ticks de combate.

La Iteración 2.119 cerró la ruta interna posterior al decoder: slot 5 → slot 16 → helper de slot 15 → incremento de `[0x85eb58]`. Esta iteración anterior todavía no tenía esa cadena. La etiqueta anterior que trataba `0x47eaa0` como el update por cuadro queda corregida: el slot es distinto del slot 5 que llama al decoder. Runtime y VPK no cambiaron.

## Próximo paso

Seguir la ruta externa que invoca `0x47f810` y obtener una sesión frame-stepped del replay Sanae para comparar cursor, contador, tick de simulación y render. La cadena estática por invocación no determina la frecuencia por cuadro. Mantener el cursor/per-pair harness como prueba de semántica por invocación, no como prueba de tiempo por cuadro.

