# Iteración 2.38: pivote local de los torii BG12

Fecha: 2026-10-17.

El constructor BG12 `0x472640` carga ambos bitmaps y llama a `0x406c60` con `x=0`, `y=0`, ancho/alto nativos y pivote `(w/2,h)`. El helper `0x406d30` construye las esquinas locales `x=[-w/2,+w/2]`, `y=[-h,0]`. Esta evidencia permite saber cómo se orientan localmente los dos sprites, sin confundir el origen del constructor con sus transforms finales en mundo/cámara. Extendí `tests/test_bg12_stage_contract.py` para fijar ambas llamadas y las asignaciones de vértices del helper. El visor interactivo ahora dibuja el marcador del pivote inferior centrado sobre `tori1/2` y mantiene pendiente la composición final.

La secuencia de auto-test aún no llega de forma estable a la capa esquemática BG12 (`stage_bg12_layout=0`); por eso la captura de esa vista no es un gate. Sí se valida la lógica exportada: contador BG12 4 y parámetros de render 8/98. El VPK automático compiló con VitaSDK y Vita3K SDL pasó schema35/600 frames, incluidos BG36, BG34, roster, práctica y combate. La suite Python completa pasa 60/60.

Artefacto: `artifacts/Touhou123Vita-bg12-pivot.vpk`; SHA-256 `497a891c9a264dc0ec60ac551919a00e7922476ee0d7f7f7c34af441a3ec59f5`. Usa los DAT locales instalados bajo `ux0:data`; no es una reconstrucción completa ni demuestra paridad visual.

Siguiente: hacer determinista la entrada manual/automática a la capa BG12, recuperar del render las transforms de ambos torii y el encuadre/cámara efectivos, y aplicar el mismo análisis a los callbacks y capas restantes.
