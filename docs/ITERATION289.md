# Iteración 2.189: quitar el fondo ajeno bajo un escenario cargado

El render de combate pintaba siempre `data/background/bg10/0000_10.cv2` antes de cualquier escenario. El renderer BG36 ya dibuja su campo base y sus cuatro auxiliares; por ello, las zonas transparentes podían mostrar BG10 como una capa de otra escena. BG10 ahora se usa solo como fondo de reserva cuando no están listos los renderers BG33 o BG36.

Se recompilaron los VPK autotest e interactivo. El autotest exacto pasó Vita3K SDL con 600 frames, `status=passed`, `regression_gate=1`; BG36 cargó/dibujó sus 25 tiles disponibles y cuatro auxiliares, y produjo captura. SHA-256 del auto VPK: `7815f2f78fd5d3183f15f581633accd957cd6d9962ca2c27fbe6b7d791045ebe`; coincide con `vpk_sha256` del reporte fresco `artifacts/vita3k-result.json`. El VPK interactivo mide 108,370 bytes y SHA-256 `072d8294b65b414b5391c43dbb0eb436db8f12693be14cf0c066ab0d2fa9298d`.

Los contratos de unittest BG36 (3/3) y BG37/BG38 (4/4) pasan; `git diff --check` pasa. La captura confirma que hay imagen y capas de BG36, pero todavía se ve una región azul rectangular asociada a la nube y no hay comparación sincronizada con PC; no se declara resuelta la transparencia ni la composición completa. La suite global de pytest no se ejecutó porque el Python local no tiene pytest y WSL respondió `E_ACCESSDENIED`. El avance global permanece en 27%.

Siguiente: identificar la mezcla/fase de color de las dos pasadas de nubes BG36 en el renderer original, comparar la captura con PC y llevar el selector de escenario al combate interactivo. Después continuar con los demás renderers de stage.
