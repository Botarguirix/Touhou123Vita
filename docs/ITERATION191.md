# Iteración 2.91: campos del quad PAT aplicados al renderer

La sonda [`x86_sprite_quad_probe.py`](../tools/x86_sprite_quad_probe.py) queda fijada al SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` del PE. Recorre las lecturas en `0x468100`, el setup de sprite en `0x466720` y el cálculo UV de `0x406d30`. Confirma los campos PAT en disco (`image`, `tx/ty/tw/th`, `ox/oy`, duración y flags), su reorganización en el registro runtime y el uso de offsets firmados. Una discrepancia inicial entre el formato de operandos de Capstone y la expectativa del test fue corregida; la sonda focalizada vuelve a pasar.

El renderer Vita dibuja ahora el rectángulo recortado de la textura PAT, admite espejo horizontal por facing y usa `ox/oy` firmados como origen local después de proyectar el mundo/cámara. El recorte UV y la copia de campos están demostrados por la lectura x86. La escala y alineación exactas entre coordenadas reducidas del prototipo y unidades del juego todavía no están calibradas; tampoco hay comparación sincronizada con una pose del juego original. La captura de autotest muestra los dos sprites completos, pero el overlay tapa parte del piso.

Validación ejecutada:

- `python tools/x86_sprite_quad_probe.py`: pasa contra el PE fijado.
- `python -m unittest tests.test_stage_camera_oracle -v`: 10/10.
- `python -m unittest discover -s tests -p 'test_*.py'`: 110/110.
- VitaSDK: VPK interactivo y auto-test compilados; comparten `eboot.bin` SHA-256 `35cdbd4005b5a41293210fb320a65a88e55ace9f89dd45f27639a2e48c39ebbf`.
- Vita3K SDL aislado: schema46, 600 frames, `status=passed`, regresión y contratos acumulados de cámara, BG33, BG36, BG37 y BG38 aprobados.

Artefactos:

- Interactivo: [`Touhou123Vita-pat-quad.vpk`](../artifacts/Touhou123Vita-pat-quad.vpk), SHA-256 `11cf2ba5d80774dae7ea42d641ebea5bb4d5b14d37a62cc515162f9a44959f4e`.
- Auto-test usado por Vita3K: [`Touhou123Vita-pat-quad-auto.vpk`](../artifacts/Touhou123Vita-pat-quad-auto.vpk), SHA-256 `d6a2992612afafa139b7c234ddf9a0fd25c7d32b5e96f1688dfb7eaa1101ea74`.
- Reporte de guest: [`vita3k-result.json`](../artifacts/vita3k-result.json).
- Captura: [`fight.bmp`](../artifacts/screenshots/fight.bmp).

Siguiente paso técnico: usar replay/capturas comparables de PC para ajustar origen y escala con poses quieta, aérea y de ataque; después aplicar el mismo camino de quad a sprites de objetos. El VPK es un prototipo funcional, no una reconstrucción completa ni evidencia de paridad por frame.
