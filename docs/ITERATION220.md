# Iteración 2.120: VPK del árbol actual reconstruido y validado

Se reconstruyeron desde el árbol de trabajo los paquetes interactivo y de autotest con VitaSDK 2026.08:

- Interactivo: [Touhou123Vita-current.vpk](../artifacts/Touhou123Vita-current.vpk), 97,535 bytes, SHA-256 `ef67efae74cd517292bd3adb26875c85565735e7fa03b752d0b87a2ab5f18d1c`.
- Autotest: [Touhou123Vita-current-auto.vpk](../artifacts/Touhou123Vita-current-auto.vpk), 97,701 bytes, SHA-256 `cfd346a8d9dafe6531d7bc66309b10343851b04685efa71dee5648b620d18008`.
- Ambos contienen el mismo `eboot.bin`, SHA-256 `d1d730c7849097d8b78a09e75ccc708b2668a9b39cf1e716c9a39abd2879fdf5`; solo el autotest incluye `auto-test.txt`.

La suite Python completa pasó: `python -m unittest discover -s tests -v` ejecutó 114 pruebas, todas aprobadas. El autotest recién construido pasó en la instancia local aislada de Vita3K SDL: schema 46, 600 cuadros y `status=passed`. Pasaron las regresiones de combate/objetos, recorte PAT, cámara/viewport y contratos de BG33, BG36, BG37 y BG38. El reporte fresco está en [vita3k-result.json](../artifacts/vita3k-result.json); las capturas de la corrida están en [screenshots](../artifacts/screenshots/).

Esto valida que el VPK actual arranca y recorre sus gates instrumentados; no demuestra paridad completa de personajes, escenarios, campaña ni replay. La búsqueda estática de caller para el slot 5 Story sigue abierta: el barrido de llamadas virtuales por offset `+0x14` devuelve objetos y clases mezclados, por lo que no se etiqueta ninguno como llamador del manager sin una referencia de objeto concluyente. La Iteración 2.119 conserva ese trabajo de análisis.

## Siguiente paso

Continuar la cobertura funcional por diferencias verificables del PE: cerrar un caller atribuible para el slot 5 Story o tomar una traza frame-stepped del original, y avanzar las mecánicas/escenarios que aún están solo catalogados o parcialmente integrados. Mantener este autotest de 600 cuadros como gate de integración, no como criterio de paridad total.
