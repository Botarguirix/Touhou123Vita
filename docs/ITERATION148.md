# Iteración 2.48: traslación de cámara/viewport de escenarios

Fecha: 2026-10-17.

Se portó `t123_stage_viewport_translation`, el término de traslación de matriz calculado por `FUN_00429440` del PE fijado. La fórmula usa resolución base `(320,420)`, centro horizontal `640`, zoom del gestor y offsets separados de cámara/viewport, con factores por eje provistos por el callback. No produce por sí sola coordenadas finales ni aplica rotación/escala completa de vértices.

La autoprueba Vita ahora ejecuta dos vectores numéricos (incluidos offsets/cámara no nulos) y rechazos para zoom cero y puntero nulo. El gate exige ese contrato y reporta `stage_viewport_contract`; la fórmula y las constantes se contrastan también con PE. Se conserva explícitamente la limitación: aún falta el renderer afín que aplica las 12 entradas de matriz, el estado real del gestor, los límites de animación de los auxiliares BG33 y su composición durante combate.

Verificación: VitaSDK compiló el VPK; Vita3K SDL aislado pasó 600 frames con `schema=43`, `regression_gate=1`, `stage_viewport_contract=1`, BG33 layout/captura presentes, 24 tiles y cuatro updates. Suite Python completa: 79/79. VPK: `artifacts/Touhou123Vita-latest.vpk`, 104,325 bytes, SHA-256 `cf904f199fa85fca8db8a2a49ebf3dbaa24e24a482159126e3b6abf59af26763`.
