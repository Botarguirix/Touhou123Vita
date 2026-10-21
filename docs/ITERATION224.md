# Iteración 2.124: impacto de Suika 623C/531 mediante objeto PAT 821

Se conectó la activación x86 623C→531 con los objetos originales PAT 821. Suika llega a la pose 7 de 531 y crea el proyectil secuencia 0 y su objeto visual secuencia 1. La secuencia 0 usa el daño 800 y la caja PAT `[-50,-50,50,50]`; el resolver Vita ancla esa caja a la posición de mundo del objeto, según el sincronizador x86 `0x465e10`. Los demás objetos conservan su transformación previa. El renderer ahora modula el alpha de 821 con la caída de 10 por tick observada en x86; el contrato framebuffer verifica mezcla alfa al 50% además del recorte PAT.

La sonda usa Suika en `(320,0)` y Remilia en `(420,0)`, la ubicación del spawn `+100`. Mantiene a Remilia en 602/seq.0/frame0 —tres hurtboxes reales— durante el startup de 20 ticks, igual que la fixture x86. El reporte huésped confirmó dos objetos, daño exacto 800, `route_mask=31` para las cuatro ramas 623C y regresión completa schema46/600 cuadros. La build con alpha pasó el gate estricto de Vita3K SDL; tres ejecuciones anteriores de la misma mecánica también pasaron antes del cambio aislado de render. La traza focalizada está en `artifacts/vitafs/ux0/data/touhou123vita-suika821-debug.json`; el reporte integral en `artifacts/vita3k-result.json`.

Las 114 pruebas Python pasan. Los VPK se generaron con VitaSDK 2026.08:

- Interactivo: [Touhou123Vita-suika623c.vpk](../artifacts/Touhou123Vita-suika623c.vpk), SHA-256 `e2f44aa0056919d6d7d3db838b608a36dac7e500a61adc672633228bb4315b33`.
- Autotest: [Touhou123Vita-suika623c-auto.vpk](../artifacts/Touhou123Vita-suika623c-auto.vpk), SHA-256 `10405e18b5e64355a29622b2d502cc4ae68c9bf0da2aea61b9087b79ca6f71eb`.

El resultado valida el spawn y el primer impacto en una fixture controlada. Quedan por contrastar el recorrido visual completo del proyectil, alpha/fade en render, reacción/hitstop, guardia y los efectos de Spell 531 frente al PE/replay. Los niveles efectivos siguen configurados por la sonda, sin progresión de cartas; otras skills, personajes, escenarios y hardware físico siguen fuera de esta cobertura.
