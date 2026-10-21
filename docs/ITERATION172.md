# Iteración 2.72: ejecución dinámica de todas las palabras del replay

Se añadió `tools/x86_replay_update_method_probe.py`, que carga el PE original 2009 en Unicorn y ejecuta instrucciones originales de `0x481040` hasta inmediatamente después del avance del índice. Las palabras del replay real se exponen como vector de `uint16`; los getters de modo, el decoder `0x42a410`, el lector de vector `0x42ea50` y el setter global se sustituyen por hooks controlados. Así se aísla el método sin afirmar que el harness simula una partida.

La pasada completa ejecutó **33.820 invocaciones**: 8.720, 6.932 y 18.168 palabras en los tres registros. En cada invocación se comprobó que el método leyera el word indicado, escribiera la misma máscara en el estado de input, emitiera los callbacks correspondientes a flags `0x4000/0x2000` y avanzara el índice una vez. También se comprobó el guard de fin de vector, que vuelve al índice cero y luego avanza a uno. Se encontraron respectivamente 34, 175 y 320 words con alguno de esos dos flags.

Reporte: [`artifacts/x86-replay-update-method-full-original-2009.json`](../artifacts/x86-replay-update-method-full-original-2009.json). El test integral [test_replay_update_method_probe.py](../tests/test_replay_update_method_probe.py) vuelve a ejecutar los tres registros si los archivos locales de referencia están presentes. El test focalizado pasó 12/12; la suite Python completa pasó 95/95.

## Límite de evidencia

Esto demuestra el comportamiento del método original al invocarlo una vez por word con las guardas preparadas. Los punteros, modo, estado de ronda y momento de llamada son fixtures controladas. No prueba que una palabra sea un frame, que el juego llame `0x481040` una vez por frame o que el wait-sync y este callback recorran el mismo cursor durante una partida viva. El parser/cursor C, el runtime Vita y el VPK no cambiaron.

Siguiente gate: capturar estado real de `[0x85d748]`, del contador `+0x14`, del tick de ronda y del punto de llamada mientras se reproduce el archivo en el PE 2009. Después comparar muestras con el core C antes de integrar carga y playback al runtime Vita.
