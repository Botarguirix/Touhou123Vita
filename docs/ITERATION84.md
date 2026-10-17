# Iteración 1.84: impacto A tras aproximación normal

Fecha: 2026-10-17 (America/Mexico_City).

## Cambio y evidencia

La autoprueba desactiva la IA de la CPU al inicio del combate, hace que el jugador se acerque con `IN_RIGHT` y pulsa A con `IN_MELEE` sin modificar las posiciones directamente. El contador de combate registró `a_hits=1`; la prueba Vita3K SDL aislada pasó schema 29 y 600 frames. El gate y `tools/vita3k-test.ps1` ahora exigen que el impacto A natural ocurra. La máscara controlada de rutas PAT continúa en `0xFFFFF` para los 20 personajes.

La captura nueva [fight-natural-a.bmp](../artifacts/screenshots/fight-natural-a.bmp) muestra el golpe durante la reacción de la CPU. El paquete es `artifacts/Touhou123Vita-natural-a-auto.vpk`, 96,273 bytes, SHA-256 `ef4ca60440f5ab7d5607e182884517dac4299578b15a0349bd93ec1e87ac27f8`.

## Alcance

Esto confirma una secuencia natural de movimiento y ataque mediante el runtime, para Marisa contra Cirno con el rival quieto. No verifica que el personaje CPU se mueva o defienda, que el daño/ventana coincida por frame con el juego original, ni que el mismo guion funcione en cada matchup. El reporte no sustituye los replays de referencia ni el análisis del estado de guardia, hitstop, cancelaciones y reacciones. Sigue pendiente integrar skills y objetos para todo el elenco, y reconstruir los demás escenarios y sus mecánicas.
