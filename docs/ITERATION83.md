# Iteración 1.83: ataque A por personaje

Fecha: 2026-10-17 (America/Mexico_City).

## Evidencia

El auto-test de Vita ahora recorre todos los PAT cargados y prueba las acciones A terrestres 300, 302, 303, 304 y 330 con sus entradas correspondientes. Para cada personaje toma una acción con hitboxes y daño, coloca al rival según la geometría PAT, ejecuta `fight_step` hasta el impacto y cuenta el caso solo si el contador `a_hits` sube y el daño aplicado coincide con la pose activa.

El gate pasó en Vita3K SDL aislado: schema 29, 600 frames, `roster_a_attack_mask=1048575` (`0xFFFFF`), 20/20. El VPK de esta corrida es `artifacts/Touhou123Vita-roster-a-auto.vpk`, 96,162 bytes, SHA-256 `c4fb9924259113e14ba0cdb9f39691c2fa03dc6398b16c335f7cee1523936605`. El runner ahora rechaza una máscara incompleta. El mismo reporte mantiene 20/20 PAT/sprites/tarjetas, cero fallos de textura, 148 texturas, BG34 y las regresiones de dash, objetos y skills ya existentes.

## Qué prueba y qué falta

Esta prueba controlada confirma que cada PAT tiene al menos un ataque A terrestre que el selector actual puede iniciar y que el resolvedor de cajas aplica el daño PAT correcto. La colocación se calcula desde hitboxes/hurtboxes originales; no equivale a conectar mediante movimiento natural del jugador. En el combate principal del auto-test `a_hits` continúa en 0, frente a B/C con 1 cada uno. El avance no demuestra paridad de timing, defensa, cancelaciones, ataques aéreos, skills para todo el roster ni una pelea completa.

El siguiente gate debe registrar un combate natural con entrada fija, posiciones y transiciones por frame, primero para Reimu/Cirno y después para cada arquetipo que el análisis de handlers permita distinguir. La corrección debe conservar daños y ventanas PAT, sin ajustar posiciones a mano durante el combate.
