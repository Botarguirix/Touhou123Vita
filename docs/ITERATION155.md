# Iteración 2.55: Remilia 801 conserva el proyectil tras el impacto

El probe x86 captura los registros y ambos objetos dentro de `0x47b660`: `ESI` apunta al objeto 801; `EBX`, al defensor. La respuesta escribe 3 en `801+0x194` (`801+0x1bc=4`, menos uno), copia el hitstop PAT del cuadro (0) a `801+0x196`, marca `801+0x190=9` y reduce el HP defensor 120. El defensor ya estaba en `+0x194=20`; este handler no lo modifica. Al enlazar un `EffectManager_Effect::CreateEffect` sintético con firma correcta, el dispatch de parejas retorna sin error y deja el objeto con `+0x34c=1`.

El runtime ya conserva el objeto Remilia 801 al conectar: registra `hit_done`, lo mantiene activo mientras avanza por PAT y evita que vuelva a causar daño. La prueba real de roster comprueba que el rival pierde 120 HP una sola vez, que el proyectil sigue activo en el siguiente cuadro y que su pose avanza. Este caso se incorporó al gate de `probe_roster_object_routes`.

La compilación `-O3` terminó con excepción en `vita-elf-create`; el build script ahora ofrece `-Optimization s|2|3` y usa `-Os` por defecto, que empaqueta correctamente este build. La configuración aún requiere medición comparativa de FPS; no se presenta `-Os` como ajuste final de rendimiento.

Verificación de esta etapa: el probe Remilia pasó 5/5; el VPK validado en Vita3K SDL ejecutó 600 frames, schema46, gate de regresión y contratos BG33. La Iteración 2.56 confirma después el ciclo de vida x86 bajo manager/listas controlados. Los efectos visuales reales, la integración natural en combate y la paridad de una ronda siguen pendientes. Ver [ITERATION156.md](ITERATION156.md).
