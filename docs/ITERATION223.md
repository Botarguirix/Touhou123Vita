# Iteración 2.123: dispatcher Suika 623C según niveles 5/9

Se añadieron `skill_level_5` y `skill_level_9` al estado del luchador y se conectó el selector x86 de Suika para el comando 623C: ambos niveles en cero seleccionan 521, nivel 5 selecciona 526, nivel 9 selecciona 531 y ambos activos no consumen el comando. Los campos entran al digest de combate para conservar visibilidad determinista del nuevo estado.

La regresión invitada ejecuta las cuatro combinaciones sobre el PAT original local. Vita3K SDL pasó 600 frames/schema46 y reportó `suika_623c_route_mask=15`: acción 521 y dos impactos por 1000; acción 526 e impacto de 500; acción 531 activada una vez; bloqueo correcto con ambos niveles activos. El test no atribuye daño a 531: el análisis de PAT/update disponible muestra la animación SpellHa y no localiza una ventana de ataque directa en el tramo observado. Suite Python: 114/114.

Artefactos compilados con VitaSDK 2026.08:

- Interactivo: [Touhou123Vita-suika623c.vpk](../artifacts/Touhou123Vita-suika623c.vpk), SHA-256 `3c8bec53bca95413549029b6387ab6f22c8fb4aafda8ad6ca2aa34c116c2f5a6`.
- Autotest: [Touhou123Vita-suika623c-auto.vpk](../artifacts/Touhou123Vita-suika623c-auto.vpk), SHA-256 `b30466a7b3d6d9e92188732ede9f8e207f2ab26343a8c8c39c1f5ba07227e1dd`.
- Reporte de huésped: [vita3k-result.json](../artifacts/vita3k-result.json).
- Dispatcher x86: [x86-suika-623c-dispatch.json](../artifacts/x86-suika-623c-dispatch.json); update/PAT action 521: [x86-suika-action-setter.json](../artifacts/x86-suika-action-setter.json).

Queda sin modelar cómo la selección de cartas/progresión cambia esos niveles durante una pelea real. La animación y las mecánicas completas de 531 aún necesitan traza del manager de objetos/efectos y validación contra replay o juego frame-steppeado. Las otras skills de Suika y las de los restantes personajes siguen pendientes; esta integración no completa el motor ni los escenarios.
