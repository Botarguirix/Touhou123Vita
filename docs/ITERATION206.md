# Iteración 2.106: el callback Story despacha al input global en estado 2

Se añadió `tools/x86_replay_story_callback_probe.py`, que carga el PE original 2009 fijado por SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3` en Unicorn y ejecuta las instrucciones reales de `0x47ee10` hasta el callsite del decoder.

Con `[0x85ec08]=2`, el callback llama una vez a `0x42a410` y el `ECX` observado es el global original `[0x85ec98]`. Con estado de control `1`, llega al mismo punto posterior a la guarda sin llamar al decoder. El getter `0x43ced0` se ejecuta sin hook y lee el estado del PE; únicamente se intercepta `0x42a410`, por lo que esta prueba confirma el gating y el objeto entregado al decoder.

Esto valida la ruta del callback aislada, pero no consume words del replay ni prueba que el menú elija este estado para `090815_2219_sanae_story.rep`. Tampoco cuenta llamadas por frame. La prueba de actualización arcade/base `0x481040` ya recorre los words reales, pero el callback Story sigue sin playback conectado al loop Vita. La ruta `(modo 6, estado 2)` sigue siendo compatible con la reproducción, no un hecho dinámico medido.

La regresión `tests/test_replay_story_callback_probe.py` comprueba el estado 2, el estado de control y el puntero recibido. Reporte: `artifacts/kernel/replay-story-callback-original-2009.json`. Siguiente: vincular la transición del menú de replay a `[0x85ec08]=2`, después ejecutar `0x47ee10` con el decoder real y medir cadence por frame.
