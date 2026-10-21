# Iteración 2.153: resolver PE aplica daño de Suika 418 tras input

**Resultado corregido por [Iteración 2.154](ITERATION254.md):** esta corrida omitía el bloque PAT crudo `combat_traits`; el daño 900/reacción ausente no era fiel para el trait 100 de la acción 418.

Se completó el camino en una sola instancia x86: PlayerSuika construido, acción 200, input C+NRNR con update/matcher originales, handler que selecciona 418, cleanup, 16 updates PAT hasta seq.2/pose.0, sincronización de cajas `0x465e10`, overlap PE `0x47a5b0` y resolver `0x47c770` contra una hurtbox PAT neutral.

El helper original de daño `0x464a80` retorna 900, coincidente con el campo PAT. El resolver observa HP 1000 en `0x47b11c` y escribe 100 en `0x47b123`: pérdida efectiva de 900. Las cajas conectan una hitbox con una hurtbox. Para completar contexto se preparan bloques de stats/equipos/HP controlados y un EffectManager stub que registra las llamadas y devuelve un objeto sintético; por ello la presentación de efectos no se ejecuta. La reacción del defensor queda en action 0, así que todavía falta reproducir la inicialización de combate necesaria para su action/hitstun de reacción.

El test de esta cadena y las dos regresiones Suika relacionadas pasan 3/3; no hay accesos inválidos. No se modificó runtime Vita/VPK. Esta evidencia verifica daño x86 en estado de combate controlado, no replay físico ni combate completo.

Evidencia: [reporte](../artifacts/x86-suika-constructed-handler.json), [sonda](../tools/x86_suika_constructed_handler_probe.py), [test](../tests/test_x86_suika_constructed_handler_probe.py). Próximo: inicializar el defensor con el constructor completo y el contexto de round/player-data para resolver reacción, stun y continuidad de frames sin fixtures de estado del target.
