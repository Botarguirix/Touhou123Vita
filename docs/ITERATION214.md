# Iteración 2.114: el archivo Sanae coincide con la plantilla del catálogo Story

Se extendió `tools/x86_replay_manager_selection_probe.py` fijando el ejecutable original de 2009 por SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`.

RTTI y vtable identifican `CReplayList` (`0x82133c`), con slot virtual 1 en `0x43c140`. Su constructor `0x42bbd0` fija el filtro `*.rep` (`0x821350`) y la raíz `replay` (`0x821330`); el slot virtual enumera los resultados del directorio. La rutina que prepara los nombres (`0x42c0a0`, referencia a la plantilla desde `0x42c34d`) forma `replay\story\%02d%02d%02d_%02d%02d_%s_story`. El archivo local `090815_2219_sanae_story.rep` coincide exactamente con el basename esperado: fecha `090815`, hora `2219`, identificador `sanae` y sufijo `_story`. El handler de selección toma los componentes de la fila, forma el path, llama a `0x42e030` y, tras una carga aceptada, cambia al estado título 6.

Junto con las iteraciones 2.112–2.113, la evidencia estática conecta la clase de lista, su filtro y raíz, la plantilla de nombres, la fila seleccionada y el loader; además separa la entrada al modo Story (estado 12 → manager modo 6/estado 2) de la posterior carga del replay. El basename Sanae encaja con el patrón Story. Aún no se ha observado el evento de confirmación en ejecución ni playback end-to-end. Tampoco se asume que una invocación del decoder equivale a un frame.

Verificación: `python -m unittest tests.test_replay_manager_selection_probe` pasa (1/1); se regeneró `artifacts/kernel/replay-manager-selection-original-2009.json`. No hubo cambios en código del juego, VPK ni corrida Vita3K.

Siguiente: obtener una captura/traza frame-stepped del PE que confirme el evento de confirmación de la fila y correlacione el avance del cursor con los ticks; después llevar el mismo contrato a la integración del runtime Vita.
