# Iteración 2.46: cadena de transformación BG33

Fecha: 2026-10-17.

Se amplió el oracle del PE para verificar, además de la tabla de 30 slots, las llamadas de `0x473620` al update de sprite `0x406ea0`, a la traducción local `0x406ee0` y a la cámara/viewport `0x429440`. También comprueba que el callback filtra por duración (`clock < end-start`), carga los offsets del escenario `+0x44/+0x48` y obtiene la escala de cada sprite. El helper `0x429440` consume la escala de viewport `+0x14`, los centros de cámara `+0x18/+0x1c` y los offsets de pantalla `+0x30/+0x34`, y compone la matriz del sprite.

Se añadieron `0x473620` y los helpers de transformación a la lista de funciones de `tools/ghidra/ExportStages.java` para que una corrida futura de Ghidra los exporte desde el PE. No hay Ghidra instalado en este entorno y la exportación no se ejecutó. No se integró una animación aproximada en el juego: faltan validar límites de tiempo y estado de cada uno de los sprites, además de implementar la matriz afín/rotación y la cámara en el renderer Vita. La build distribuida sigue siendo la de Iteración 2.45.

Verificación: `python -m unittest tests.test_bg33_pe_vtable_oracle -v` pasó 3/3. Evidencia base: `artifacts/kernel/bg33-render-full.tsv`, `artifacts/stage-render-helper-disasm.tsv`, PE local SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.
