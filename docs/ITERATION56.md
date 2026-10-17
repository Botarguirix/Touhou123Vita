# Iteración 1.52: ramas de bloqueo y límites del integrador x86

Fecha: 2026-10-16.

Al desensamblar `00463550` completo, confirmé que el límite horizontal de la arena depende de `Player+0x571`; no se puede copiar como un clamp global en el runtime.

- Con `+0x571 == 0`, la rama `00463634` integra `(opponent+0x74C + Player+0xF4) * direction * speedPower` y termina sin limitar `x`. Unicorn verifica 37.5 desde x=42 con vx=-4.5, y 1242.5 desde x=1238 con vx=4.5.
- Con `+0x571 != 0`, la rama `00463585` también incluye `Player+0x744`, consulta `004393B0` y `004393F0`, y aplica límites almacenados en `0x8596B8` (40.0) y `0x85A25C` (1240.0). Esas consultas dependen de estado de escenario y aún no están modeladas en el oracle.
- Ambas ramas exigen estado cero en `Player+0x196` y `opponent+0x4A8`; de lo contrario, la función retorna sin integrar. Las condiciones no deben desaparecer al generalizar la rutina.

Extendí el oracle y las pruebas para distinguir el caso sin bloqueo y los dos early-return por lock; la suite Python completa pasa 22/22. Esto refina el alcance de Iteración 1.51: el integrador portado reproduce el término horizontal base en los vuelos, pero los límites locales 35..605 siguen siendo una aproximación visual del prototipo y no representan todavía la colisión de escenario x86. Mantengo esa escala por ahora porque el renderizador local opera en coordenadas diferentes; trasladar 40..1240 directamente sacaría personajes del viewport. El siguiente paso de paridad es identificar qué configura `+0x571`, `+0x744` y los helpers de colisión en una escena real, y definir el mapeo de coordenadas de combate antes de reemplazar los límites.

Referencias: PE `th123.exe`, SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`; ramas en `00463550`; globals x86 `0x8596B8` y `0x85A25C`; oracle `tools/x86_physics_oracle.py`.
