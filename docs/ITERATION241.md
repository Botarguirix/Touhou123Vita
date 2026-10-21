# Iteración 2.141: PE de Suika 418 avanza desde windup hasta la hitbox

La fixture del setter Suika en `x86_suwako_808_factory_probe.py` ahora construye cada acción a partir de su tabla PAT efectiva (el decoder reemplaza una definición de acción anterior). Conserva el conteo crudo de definiciones para el diagnóstico Alice 849; el probe ya no falla con las dos definiciones de Suika 418.

Agregué `tools/x86_suika_dash_sequence_probe.py`, que fija el PE por SHA-256 y ejecuta el setter original más 40 updates de su vtable con el PAT local fijado por hash. El setter establece acción 418 en secuencia 0. El update avanza a secuencia 1 en tick 8 y llega a secuencia 2/pose 0 en tick 16, con daño PAT 900 y una hitbox; la ventana registrada dura ticks 16–26. En tick 27 el estado salta a secuencia 5, lo que demuestra que no se debe modelar como reproducción lineal sin recuperar la condición de esa rama. A partir de tick 35 el campo de secuencia vuelve a 6; su significado necesita trazarse antes de mapearlo a un índice PAT.

Reporte: [x86-suika-418-sequence.json](../artifacts/x86-suika-418-sequence.json). Regresión: `tests.test_x86_suika_dash_sequence_probe`. Pruebas focalizadas 11/11 y suite Python completa 119/119. No hay cambio de runtime/VPK: el setter recibe 418 directamente, sin input natural de dash, rival, colisión ni replay.

Siguiente: trazar las escrituras de `Player+0x13e` y las llamadas condicionales en el update de Suika alrededor de tick 27; determinar si la selección de secuencia 5 depende del contacto, estado de cancelación, input o un timer. Repetir después con Udonge/Utsuho y comparar transición y posición relativa con los probes de cajas x86 antes de portar el timeline a `fight.c`.
