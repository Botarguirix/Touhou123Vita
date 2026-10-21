# Iteración 2.127: reacción de Remilia tras el impacto de PAT 821

La captura guest posterior al impacto mostró una diferencia frente al PE: el resolver Vita dejaba 10 ticks de stun por el valor de la pose PAT, mientras el hit-response x86 registra temporizador 20 (`Player+0x194`). La ruta player-vs-player x86 selecciona además reacción Remilia 50; el resolver Vita ya hacía esa selección. El golpe de PAT 821 ahora aplica 20 ticks al defensor. La compuerta captura el primer cuadro tras el impacto y exige 800 de daño, acción 50, secuencia/pose 0 y stun 20.

La corrida Vita3K SDL pasó schema46/600, route mask 31, dos objetos, 800 HP de daño, ambos ciclos de 27 actualizaciones y `impact_contract=1`. La suite Python pasó 114/114. El reporte es `artifacts/vita3k-result.json`; captura guest y trayectorias: `artifacts/vitafs/ux0/data/touhou123vita-suika821-debug.json` y TSV vecinos.

VPK generados con VitaSDK:

- Interactivo: [Touhou123Vita-suika623c.vpk](../artifacts/Touhou123Vita-suika623c.vpk), SHA-256 `c96f5374b782db2f247311a1de2f1521155fbb2a621e72bd3af23ad628f5e7be`.
- Autotest: [Touhou123Vita-suika623c-auto.vpk](../artifacts/Touhou123Vita-suika623c-auto.vpk), SHA-256 `36c3599ef0a577d835dd409b09832535e72114858058f1d31782c029da864b97`.

La reacción se verifica en la fixture controlada al primer cuadro; aún no se compara toda la animación/stun con una corrida natural o replay del PC. Hitstop observado para el impacto x86 es cero. Guardia, Spell 531, progresión de cartas, cobertura del roster/escenarios y hardware físico siguen pendientes.
