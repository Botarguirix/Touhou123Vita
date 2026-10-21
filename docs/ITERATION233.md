# Iteración 2.133: ampliar la cobertura natural B/C del roster

La sonda por personaje ahora repite cada ruta PAT candidata contra tres posiciones iniciales del rival (x=340/380/420) desde el spawn normal. El TSV registra la separación entre los luchadores al conectar, además de acción, frame, daño y origen del hit. Esto corrige el supuesto anterior de una sola distancia fija y conserva el carácter diagnóstico del barrido: rival inmóvil, sin defensa/IA.

El nuevo reporte encuentra ataques B normales con daño PAT en 15/20 personajes y ataques C normales en 17/20. Alice conecta ahora 66B y 66C a través de PAT 849 (450 de daño cada uno en esta separación); las rutas C normales de Remilia siguen conectando vía objeto 801. Los faltantes B son Reimu, Remilia, Udonge, Tenshi y Cirno; los faltantes C normales son Suika, Udonge y Utsuho. Para no marcar Suika como sin C, el inventario guarda aparte su 623C por movimiento: base 521/1000, nivel5 526/500 y nivel9 531/800. El runner ahora exige esos seis valores además del contrato Remilia 2C/objeto801.

VitaSDK compiló los paquetes y Vita3K SDL pasó schema46/600 frames; route mask Suika 623B se mantiene en 127, 623C en 31, con gates de objetos, sprites y escenarios. El runner generó un TSV fresco en [roster-bc-natural.tsv](../artifacts/roster-bc-natural.tsv) y un reporte integral en [vita3k-result.json](../artifacts/vita3k-result.json).

- Autotest: [Touhou123Vita-roster-spacing-auto.vpk](../artifacts/Touhou123Vita-roster-spacing-auto.vpk), SHA-256 `17932B8D556679B306A1B3DC3B595B0E482645148F1462D1B7B295257A6ECD7E`.
- Interactivo: [Touhou123Vita-roster-spacing-interactive.vpk](../artifacts/Touhou123Vita-roster-spacing-interactive.vpk), SHA-256 `E2CFC1240B8D624A0FA75BC8970B0C73ABCF5D5EB05E822AFBCB2332E7CC80CD`.
- Ambos comparten `eboot.bin` SHA-256 `D5B58AC1C39996BF64CCB3A9DCF4B502C8B13F3ED9E94A34D3149764631EAB61`; Vita3K ejecutó el autotest.

Este avance amplía la cobertura de detección, no la paridad del selector de variantes original ni todos los matchups. Continúan sin conexión observada 5 rutas B y 3 rutas C normales bajo este escenario de prueba; las entradas especiales además de Suika y la defensa/movimiento de los rivales aún requieren reconstrucción y comparación con PE/replay. El juego completo, los escenarios completos y el hardware físico siguen pendientes.
