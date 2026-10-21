# Iteración 2.126: ciclo x86 del efecto visual PAT 821/seq.1

Se extendió la sonda Unicorn del PE para avanzar por separado el objeto 821/seq.1 creado junto al proyectil seq.0. El updater original confirma 27 ticks: el primero queda en el spawn; después cae verticalmente con aceleración de `-0.5` unidades por tick, pierde 10 de alpha por actualización, conserva una pose PAT y se desactiva en el tick 27 antes de otro movimiento. La traza termina en `(420,17.5)` del espacio x86 con alpha 5; en coordenadas locales Vita corresponde a `(420,-162.5)`. `tests/test_x86_suika_action_setter_probe.py` comprueba los estados inicial, intermedio y final.

Se portó gravedad, movimiento fraccionario, fade y ciclo de vida a la secuencia visual. El contrato Vita registra 27 ticks para seq.0 y 27 para seq.1 (`motion_contract=1`, `visual_motion_contract=1`). Vita3K SDL pasó schema 46, 600 frames, `route_mask=31`, daño de 800, dos objetos y regresiones de escenarios. La suite completa Python pasó 114/114.

Artefactos: `artifacts/vita3k-result.json`, `artifacts/vitafs/ux0/data/touhou123vita-suika821-debug.json`, `touhou123vita-suika821-motion.tsv` y `touhou123vita-suika821-seq1-motion.tsv`; oráculo original: `artifacts/x86-suika-action-setter-current.json`.

VPK generados con VitaSDK:

- Interactivo: [Touhou123Vita-suika623c.vpk](../artifacts/Touhou123Vita-suika623c.vpk), SHA-256 `f80ec19ed0cb6a82e55dc01ff58d2a0ca56ff80f18c603550d87b46b0056d368`.
- Autotest: [Touhou123Vita-suika623c-auto.vpk](../artifacts/Touhou123Vita-suika623c-auto.vpk), SHA-256 `5abae17c05d91634e62bb71f0250d61f073a05e5d284ed452266784ceab389dc`.

Esto verifica los dos ciclos de objeto en una fixture controlada, no la representación visual cotejada por captura con el juego original. Reacción/hitstop, guardia, Spell 531, progresión de cartas, resto de personajes/mecánicas y prueba en Vita física siguen pendientes.
