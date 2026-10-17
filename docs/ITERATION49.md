# Iteración 1.45: secuencia inicial de la skill 560

## Cambio

El reinicio x86 de la acción 560 de Reimu pone el índice PAT en cero. El inicializador por nivel no salta a la variante ofensiva. Se conectó la lista ordenada de secuencias a la animación, y el probe de Vita3K usa un `Fight` aislado para no modificar la corrida general de regresión.

La prueba automática carga el PAT real, coloca al rival mediante cajas de ataque/daño de la secuencia 1 y comprueba que los primeros 11 updates siguen en secuencia 0 sin impacto; el update 12 cambia a secuencia 1 y conecta. El esquema de reporte pasó a 21 y el runner exige explícitamente la transición `0 → 1`, cero daño de preparación y un impacto en la secuencia ofensiva.

El oracle ejecutó el `resetSequence` y `initializeAction` del PE x86 local en cinco niveles de skill (0–4): todos preservaron secuencia 0; sólo el nivel 4 escribió el marcador `2`. Este test no modela la animación PAT posterior; confirma que el juego no elige la variante ofensiva según nivel. Reporte: `artifacts/x86-skill-sequence-oracle.json`.

## Resultado

- Suite Python: 16/16 pruebas.
- Build VitaSDK: correcto.
- Vita3K SDL, instalación aislada y 600 frames: `passed`, schema 21.
- Skill: acción 560, imagen inicial 71, secuencia inicial 0, cero daño durante los primeros 11 updates, transición a secuencia 1 e impacto delta 1 en el update 12.
- Regresión: roster/PAT/tarjetas/arte 20/20, BG34 30+30 tiles, 4 recursos estáticos y 30 objetos, 35 rutas de impacto directo de dash, tres sin cajas directas, tres dashes y métricas B/C positivas.
- VPK de probe: `artifacts/Touhou123Vita-skill-sequence-probe.vpk`, SHA-256 `54e4c58c34dd8a5be8416afcedba6187f6d8c94605bb76638ef2d5997905ffc2`.
- VPK interactivo reconstruido desde el mismo código: `artifacts/Touhou123Vita-skill-demo.vpk`, SHA-256 `35162bf1dbc601887d7245e36c37ea27f87cb368a9d08c33fcc5891831ccf54d`. La build pasó; esta build interactiva no se lanzó separadamente en Vita3K.
- VPK interactivo reconstruido desde el mismo código: `artifacts/Touhou123Vita-skill-demo.vpk`, SHA-256 `35162bf1dbc601887d7245e36c37ea27f87cb368a9d08c33fcc5891831ccf54d`. La build pasó; esta build interactiva no se lanzó separadamente en Vita3K.

La comprobación demuestra sólo la entrada, startup y primer impacto de una ruta experimental. La secuencia en bucle, su salida/cancelación, activación desde mano con costo, mejora, aéreo y objetos de otras skills todavía no están terminados. Vita3K no sustituye una prueba física. CTest C host no pudo ejecutarse porque no hay CMake ni compilador host disponible; la compilación VitaSDK sí pasó.

## Referencia Touhou 7.5

Se revisó el checkout local `Vita_Touhou75\Touhou75Vita`, iteración 96. Su ejecución PE32/x86 por WinVita y su telemetría física pueden informar una ruta experimental y el proceso de diagnóstico. No hay evidencia de combate en TH075 todavía y la rama x86 no reemplaza la reconstrucción C de TH123. Ver [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md) y la comparación de arquitectura en [PORT_REFERENCES.md](PORT_REFERENCES.md).
