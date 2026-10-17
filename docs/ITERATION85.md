# Iteración 1.85: ruta A natural por personaje

Fecha: 2026-10-17 (America/Mexico_City).

## Corrida y gate

La sonda recorre los 20 PAT del roster. Por cada uno crea un combate en las posiciones de spawn normales `(190,450)`, deja a Cirno como objetivo inmóvil, avanza al atacante durante 130 updates con `IN_RIGHT` y prueba las entradas A terrestres que ese PAT admite. Después del botón no corrige posiciones ni estados: deja correr `fight_step` hasta 600 updates y cuenta el resultado solo si la acción A seleccionada causa un hit y el daño aplicado coincide con la pose activa.

VitaSDK generó `artifacts/Touhou123Vita-roster-natural-a-auto.vpk` (96,291 bytes; SHA-256 `1a1461e7197ac65694ce45f01f45f3460288301bd7029c27a1b072300372fd08`). Vita3K SDL aislado pasó schema 30 y 600 frames. La máscara de ataques controlados y la de ataques naturales son ambas `1048575` (`0xFFFFF`), con 20/20 personajes. La pelea principal de la secuencia registra A=1, B=1 y C=2; el test runner exige estos gates además del resto de regresiones.

## Alcance

La medición ejecuta lógica real del prototipo con movimientos de `fight_step` y cajas PAT auténticas, pero el rival es Cirno inmóvil. No cubre todos los 400 pares posibles, defensa/IA del rival, rutas de dash B/C, cancelaciones, skills u objetos para todos, ni compara timing por frame contra el juego original. Los 20/20 indican una ruta básica A que conecta tras aproximación en este escenario repetible; no representan roster completo jugable ni paridad funcional.

El siguiente gate debe instrumentar rutas B y C por personaje, incluyendo el dash previo donde lo requiera la acción PAT, y después correr parejas con movimiento/guardia. La referencia de timing sigue siendo el EXE/replay de PC y debe quedar documentada para cada subsistema antes de afirmar paridad.
