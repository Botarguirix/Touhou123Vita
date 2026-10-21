# Iteración 2.122: Suika 623C conecta ambas ventanas PAT

El análisis del update original de Suika confirma que la acción 521 avanza por secuencias PAT 0, 1, 2 y 3. En la secuencia 1 conserva una ventana de ataque de 400 durante dos ticks; en la secuencia 3 abre otra de 600. El PE 2009 está fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`; el probe de setter/update registra los daños en ticks 12–13 y 30 respectivamente.

La primera integración trasladó ambos frames PAT pero la colisión del port guardaba `hit_done` para toda la acción, por lo que solo aplicaba 400 una vez. Ahora las skills se rearman tras salir de una pose dañina: se evita repetir el mismo contacto mientras la hitbox sigue activa y se habilita la siguiente ventana authored. El gate del invitado exige que el comando 623C active una vez PAT 521 y reduzca 1000 HP combinando ambos impactos (400+600).

Validación: VitaSDK 2026.08 recompiló VPK interactivo y autotest; Vita3K SDL pasó schema46/600 frames y reportó `suika_623c_probe=1`, `action_seen=1`, `skill_uses=1`, `hit_delta=1000`. La suite Python completa pasó 114/114. El fixture de combate usa el PAT real de Suika para ambos lados como defensor controlado; no es una prueba de matchup completo ni coteja el hitstop/stun por cuadro del juego original.

Artefactos:

- VPK interactivo: [Touhou123Vita-suika623c.vpk](../artifacts/Touhou123Vita-suika623c.vpk), SHA-256 `8a11917aa35432d91f6898dcae8fa99b41e26034a936244466d1d35c18c5d7a7`.
- VPK autotest: [Touhou123Vita-suika623c-auto.vpk](../artifacts/Touhou123Vita-suika623c-auto.vpk), SHA-256 `7e1d4c0da27d7c4f5ab10a0e4a14b0c66901912296367f9dc3d9d762ff1478e9`.
- Reporte de Vita3K: [vita3k-result.json](../artifacts/vita3k-result.json).
- Probe del update x86: [x86-suika-action-setter.json](../artifacts/x86-suika-action-setter.json); probe de selección 623C: [x86-suika-623c-dispatch.json](../artifacts/x86-suika-623c-dispatch.json).

Sigue pendiente modelar niveles de las skills: el dispatcher x86 selecciona 531 cuando nivel9=1, 526 cuando nivel5=1 y 521 cuando ambos están en cero; con ambos niveles en uno no activa esta ruta. Los análisis de PAT identifican 526 con daño 500 en su pose ofensiva, mientras 531 tiene un recorrido visual/buff sin frame ofensivo directo en el update muestreado. Antes de portarlas se debe recuperar su semántica completa, posibles objetos y transiciones. La reconstrucción completa del juego sigue abierta.


**Actualización posterior:** la Iteración 2.123 implementó y probó las ramas por nivel 5/9. La activación de 531 pasó; su semántica de efectos y la progresión que establece los niveles permanecen pendientes. Los VPK con nombre compartido se reemplazaron por la build de 2.123.
