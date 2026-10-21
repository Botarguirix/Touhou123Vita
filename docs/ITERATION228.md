# Iteración 2.128: Suika 623B por niveles, con PAT 520/525/530

El dispatcher x86 de Suika contiene una ruta 623B independiente (`0x60a5b0`, comando `Player+0x7c8 & 0x200`). Se añadieron cuatro casos al probe original: nivel 9 selecciona 530, nivel 5 selecciona 525, nivel base selecciona 520 y ambos niveles activos bloquean el comando. El probe verifica además move-lock, evento de uso, setter virtual, `useSkill` y reseed de input. Los datos PAT locales confirman para 520 ventanas de 400 y 600; para 525, un impacto de 500; 530 no muestra daño directo en las poses examinadas.

El port ahora reconoce el movimiento `623B` y aplica el selector por niveles. Vita3K SDL validó con PAT real `route_mask=15`: 520 causa 1000 acumulado, 525 causa 500, 530 se activa y la combinación bloqueada no consume la habilidad. Las rutas existentes 623C/PAT 821 y los contratos de escenarios también pasaron; el reporte es `artifacts/vita3k-result.json`. La suite Python completa pasó 114/114.

VPK VitaSDK:

- Interactivo: [Touhou123Vita-suika623b.vpk](../artifacts/Touhou123Vita-suika623b.vpk), SHA-256 `8f24c1d3835b13c56ed5cb4550b090c7e6994f01fcb4ec86ffab7738908972e5`.
- Autotest: [Touhou123Vita-suika623b-auto.vpk](../artifacts/Touhou123Vita-suika623b-auto.vpk), SHA-256 `293808e8d22ebfee64943c680d39e386e973fae94c66a8ee626eee4c12a600cb`.

La entrada del comando usa actualmente los campos efectivos de nivel que fija el fixture; la progresión/cambio de cartas durante un combate no está conectada. La semántica visual y de efectos de 530 requiere más traza x86. Esta mejora cubre solo a Suika: el resto de skills, personajes, escenarios y la paridad completa continúan pendientes.
