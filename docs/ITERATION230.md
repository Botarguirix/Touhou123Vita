# Iteración 2.130: alcance geométrico controlado para Suika 623B nivel 9

La prueba nueva deja el PAT 821 en la posición de spawn obtenida con el RNG xorshift original del PE: `(344.6202,261.1317)`. Barre una cuadrícula de 11×11 posiciones del defensor sin desplazar al atacante. El centro `(0,0)` da contacto; el resolver de colisión del PE alcanza la respuesta de impacto y reduce HP de 1000 a 200 (800 de daño), consistente con los datos PAT.

El fixture no inicializa la cámara/escenario que requiere el transformador original de cajas. Para esta cuadrícula se usa la transformación afín de coordenadas locales reconstruida de dos observaciones del PE: `x' = x + facing·localX`, `y' = localY - y`, ordenando los extremos. La fórmula reproduce exactamente las cajas world-space observadas del PE en la prueba pinned. El barrido encuentra contacto en 56/121 posiciones; esto mide la geometría relativa al spawn, no una trayectoria del juego ni una probabilidad de impacto. El replay disponible `090815_2219_sanae_story.rep` no contiene el índice de Suika, así que no provee una traza real para esta acción.

La regresión focalizada pasa 2/2 y la suite Python completa pasa 115/115. Se reconstruyeron los VPK desde el árbol actual. Vita3K SDL pasó el autotest con schema 46 y 600 cuadros, junto con regresiones, probes de Suika 623B/623C, objetos y contratos/capturas de escenarios. Resultado fresco: `artifacts/vita3k-result.json`.

Artefactos:

- Interactivo: `artifacts/Touhou123Vita-suika623b.vpk`, SHA-256 `A5A5B8CA6998640E8D74B269094595C56DCC722AFC01C93E1A5D102DBA6D38FD`.
- Autotest: `artifacts/Touhou123Vita-suika623b-auto.vpk`, SHA-256 `B602C1228ABD1347DEB288A53B2348DAECF6CD6E3D95A2C2666E7CC17A19F69D`.
- Reporte Vita3K: `artifacts/vita3k-result.json` (status `passed`, schema 46, 600 frames).

No se integró el efecto 530 a `src/fight.c`; por tanto esta build conserva las funciones ya implementadas y verificadas, pero la técnica 623B nivel 9 sigue mostrando solo la activación. Próximo: conseguir una grabación/replay de Suika con 623B o instrumentar input y estado de combate en el PE para fijar el origen, el RNG, la vida del objeto y la trayectoria en una escena real antes de portar el efecto.
