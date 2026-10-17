# Iteración 1.73: factory y dispatcher originales de Suwako 808

Se amplió `tools/x86_suwako_808_factory_probe.py` para recorrer en el PE fijado por hash el constructor de lista (`0x783d70`), asignación del manager/handle, constructor de Suwako (`0x783a70`), factory (`0x784020`) y dispatcher de actualización (`0x7876d0`). Allocator, locks, PAT mínimo, trigonometría, RNG, piso, colisión y callback gráfico siguen controlados o sustituidos. No se ejecuta el loop del juego ni un renderer real.

La factory retorna normalmente en `STOP` con vtable `0x85f22c`, action 808, secuencia 1, posición `(300,400)` y color `ffffffff` (alpha 255). El reporte separa ese estado inicial de los updates posteriores. La primera prueba todavía usaba un flag loop en el offset incorrecto; su lectura de secuencia 4 y alpha 175 fue supersedida por la corrección documentada en Iteración 1.74.

El reporte reproducible se regenera en `artifacts/x86-suwako-808-factory-probe.json`. `tests/test_suwako_808_factory_probe.py` verifica el retorno del factory. La continuidad de secuencia y los valores post-update deben leerse en la Iteración 1.74, que usa flags/duraciones extraídos del PAT genuino. Esta evidencia no prueba impactos, colisiones ni terminación natural, integración Vita o un VPK nuevo. No se cambió el runtime Vita.

## Transferencia desde Touhou75Vita

El hilo `Configurar Touhou75Vita` solo valida en Linux el smoke test sintético del prototipo x86→C; reporta el bootstrap VitaSDK detenido por HTTP 403. El checkout local TH075 aporta, como método, contratos ABI explícitos, límites/watchdog, separación de logs y mediciones por corrida. Esas prácticas ya aparecen en herramientas de TH123 y se fortalecen aquí con estado de factory y estado post-update explícitos. No trasladar su runtime, imports Win32, renderer D3D8/raster CPU, direcciones ni fixtures: son específicos de TH075 y no tienen prueba diferencial con `th123.exe`. Ver `TOUHOU75_REUSE_REVIEW.md`.

## Siguiente gate

1. Continuar decodificando los campos de pose completos que necesita el renderer y validar layout/enlaces contra el loader PAT del PE.
2. Capturar cada transición del dispatcher y establecer la terminación/colisión del objeto con los frames reales.
3. Resolver colisión, vida y borrado en la lista/manager con servicios x86 contrastados, y comparar contra replay/traza del juego original.
4. Solo tras ese gate, portar el contrato validado a C y generar un VPK de regresión para Vita3K.
