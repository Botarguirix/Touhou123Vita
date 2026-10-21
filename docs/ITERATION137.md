# Iteración 2.37: contrato de render BG12

Fecha: 2026-10-17.

El PE local fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` asocia el vtable de BG12 (`0x85ac9c`) con update `0x4723b0` y render `0x4723f0`. El update incrementa `this+0x64` en uno para BG12 (ID 12), con excepciones para otros IDs. El render itera `ebp=0,45`, calcula los argumentos temporales `2*(counter+ebp)` y llama `0x407180`.

El constructor `0x472640` carga `tori1.bmp`/`tori2.bmp` y llama al cargador genérico `0x46fe40(12,0x56,0)`. Su export local de Ghidra indica anchors de tiles `(700-256*col, 946-256*row)`. Añadí el contrato portátil a `include/t123/stage.h`/`src/stage.c`, pruebas de código C y una prueba Python que valida instrucciones y export hash-pinned. La capa 2 del visor muestra esos anchors y los dos recursos torii; se aclara en pantalla que son transforms previos a cámara y que falta recuperar las posiciones finales de los torii y la composición.

VitaSDK compiló el VPK automático. Vita3K SDL aislado ejecutó 600 frames; `stage_bg12_contract=1`, `stage_bg12_updates=4`, counter 4 y argumentos 8/98 concordaron. Los gates previos de BG36, BG34, roster, práctica y combate dieron valores positivos esperados. El runner no consigue entrar de forma determinista a la capa 2 de BG12 (`stage_bg12_layout=0`). Retiré temporalmente la captura del gate: el reporte final schema35 sí pasó los 600 frames y gates existentes, pero este pase acredita el contrato lógico de BG12 y no la composición visual del esquema.

Suite Python completa: 59/59. El VPK de esta iteración pasó Vita3K y está en `artifacts/Touhou123Vita-bg12-layout.vpk`; SHA-256 actual `5416879a3241e15ba4a574195d35aec6c0411456687414f416a48de818a8b517`. Usa DAT externos de TH123 en `ux0:data`; no es el juego completo ni acredita paridad visual o de combate.

Siguiente: resolver la navegación determinista/captura de BG12, recuperar el transform y timing exactos de `tori1/2`, luego continuar los callbacks de BG33/BG36–38 y las capas/cámara que faltan.

