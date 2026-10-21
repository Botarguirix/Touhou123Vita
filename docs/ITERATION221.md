# Iteración 2.121: primer comando especial de Suika conectado al combate

Se conectó el comando direccional **623C** al combate para Suika (personaje 9), usando `t123_input_match` sobre las 15 muestras recientes. La sonda del PE 2009 fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` identifica el bit `0x400` y selecciona la acción PAT 521 cuando los chequeos de nivel consultados valen cero. El prototipo aún no modela la progresión/niveles de carta; por eso esta integración cubre explícitamente esa ruta base.

La nueva sonda invitada usa el DAT local real de Suika y comprueba el comando, la acción, una única activación y daño contra el PAT del defensor. El VPK automático pasó Vita3K SDL en 600 cuadros, schema46 y `status=passed`; el reporte registra `suika_623c_probe=1`, `action_seen=1`, `skill_uses=1`, `hit_delta=400`. El gate ya falla si no se alcanza cualquiera de esas condiciones. La suite Python pasó 114/114.

El daño observado es un impacto de 400. El resumen x86 previo proponía también una transición de acción/pose más adelante (mencionada alrededor del tick 30, 600 de daño), pero esta corrida no la reprodujo; por tanto no declaramos la secuencia completa ni paridad temporal. Además, el probe x86 del dispatcher inyecta el comando y sustituye algunos helpers, así que no demuestra por sí solo la producción natural de entrada, los niveles efectivos ni todo el update. Próximo trabajo: trazar action 521 desde su handler/update x86, determinar su selector por nivel y replicar cada transición PAT/hit antes de ampliar el mapeo a otras skills/personajes.

Artefactos:

- VPK interactivo: [Touhou123Vita-suika623c.vpk](../artifacts/Touhou123Vita-suika623c.vpk), SHA-256 `07ab6b2debf567eae245c9681e78ff9f2e1e80aece6a6b5a8b12844677260935`.
- VPK de prueba: [Touhou123Vita-suika623c-auto.vpk](../artifacts/Touhou123Vita-suika623c-auto.vpk), SHA-256 `a7e712ead8b6180bd298a9c058dbc0ced53ef30c8828868d26f0335e1680facf`.
- Evidencia Vita3K: [vita3k-result.json](../artifacts/vita3k-result.json), con métricas específicas de Suika además de los gates previos de pelea, PAT y escenarios.

Esto valida una primera ruta especial jugable/probada en el motor de Vita; no completa las skills de Suika ni las de los otros 19 personajes, y tampoco equivale al juego completo.


**Actualización posterior:** esta corrida inicial comprobó solo el impacto de 400. La Iteración 2.122 corrigió el latch y verificó 400+600=1000 en Vita3K. Los hashes de los VPK del mismo nombre corresponden ahora a la build posterior documentada allí.
