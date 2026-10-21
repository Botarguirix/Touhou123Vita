# Iteración 2.195: cámara de la captura BG36 registrada

El reporte automatizado ahora conserva `camera.x`, `camera.y` y `camera.zoom` en el instante de la captura de combate BG36. Antes se guardaba el scroll y la cobertura de tiles/auxiliares, pero no el estado de cámara necesario para reconstruir la transformación de pantalla y alinear una captura equivalente del juego original. El runner exige los tres números finitos y un zoom en el rango observado por el port.

Evidencia fresca: VPK auto SHA-256 `ac19b63c4c2b0bec10f024210b83b8b1ede2197a4b00d08a8adfd250a43bc7f8`; `check_vpk.py` 8 entradas, cero errores/advertencias. Vita3K SDL schema46/600, gate 1: captura con cámara `(392, 0, 1)`, nubes `(-401.5, -301.0)`, 25 tiles (máscara `0x3ffff79c`), 4 auxiliares y selector interactivo. Pruebas de contrato BG36/BG37/BG38: 7/7. El reporte está en `artifacts/vita3k-result.json` y la imagen en `artifacts/screenshots/fight-bg36.bmp`.

La copia local de `th123.exe` y el replay `090815_2219_sanae_story.rep` fueron leídos sin modificar. El replay es compatible con el ejecutable (hash del EXE `24e6149f…`, replay `6905658c…`), pero su compatibilidad de formato no demuestra que contenga BG36 ni que sea un frame comparable. Próximo paso: reproducirlo en PC, identificar la etapa y capturar un frame sincronizado; todavía no se afirma paridad visual de BG36. Avance global: 27%.
