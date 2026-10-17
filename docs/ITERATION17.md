# Iteración 1.13: ventana de input del dash recuperada

## Evidencia x86

Se desensambló con Capstone el PE 1.10a fijado por SHA, aislando exactamente `00487020` (497 bytes, hasta `ret` en `00487210`). La función llama a `0046cc90` para reconocer patrones y construye bitmasks en `this+0x7c4` y `this+0x7c8`. Para `NRNR` y `NLNL` pasa límite 15 y longitud 4; marca bits `0x01`/`0x02`. `handleGroundDash` (`0048a220.c`) interpreta esos bits según la orientación. El patrón `DD` usa límite 15/longitud 2. Otros movimientos direccionales tienen límites 15 o 20 ticks y escriben las máscaras documentadas en [INPUT_STATE.md](INPUT_STATE.md).

El dump de instrucciones tiene hash de referencia y puede regenerarse desde el PE con `tools/find_pe_callers.py --window 00487020:1F1`; está guardado en `artifacts/kernel/<sha>/input-state/00487020.capstone.txt`. Esta salida es desensamblado x86 verificable, no pseudocódigo decompilado de Ghidra. La exportación Ghidra sigue impedida por permisos de lectura de bibliotecas externas.

## Cambio y prueba

El prototipo usa ahora 15 ticks para el doble toque y detecta el toque de borde antes de reducir la ventana. El sondeo guest verifica neutral+B/C bloqueados, las rutas positivas `dash 200 → 408:index 1` y `dash 200 → 418:index 0`, y el límite temporal: segundo toque a 15 ticks aceptado, a 16 rechazado. `fight_reset` reinicia el búfer de input.

VitaSDK compiló los VPK interactivo y automático. Vita3K SDL pasó 600 frames con `dash_gate_probe=1`, 3 dashes, A/B/C=1/1/1, roster 20/20, 0 fallos de textura y los recursos BG34 de la prueba anterior completos. El control temporal corrige la ventana de historial; siguen provisionales la duración del dash, el significado completo de `sVar1` y los move locks/cancelaciones.

- Interactivo: `artifacts/Touhou123Vita-dash-15tick.vpk`, 82,757 bytes, SHA-256 `749cefed223c7ae23b466b5a2c2c087cc78da41c2fcea9996a4b6a14ef3c4e87`.
- Automático: `artifacts/Touhou123Vita-dash-15tick-auto.vpk`, 82,923 bytes, SHA-256 `ee00c123e89e26a7c5068c887cdf48d4bbf63093c89069dfbcfd97d83fde0d60`.
- Reporte Vita3K: `artifacts/vita3k-result.json`.

La suite host sigue pendiente porque WSL respondió `E_ACCESSDENIED` al crear su instancia. La compilación ARM y el gate integrado de Vita3K sí se ejecutaron en esta iteración.
