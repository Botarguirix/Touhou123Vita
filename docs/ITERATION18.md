# Iteración 1.14: matcher de movimientos y dash desde ambos lados

## Recuperación de `0046cc90`

Se aisló el helper completo en el PE 1.10a cuya SHA-256 es `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. El dump Capstone de 960 bytes está en `artifacts/kernel/<sha>/input-state/0046cc90.capstone.txt`; la función termina en `0046d04d` y la siguiente comienza en `0046d050`. El dump registra instrucciones, no es pseudocódigo Ghidra.

La rutina usa un patrón, la longitud y un límite de historial. Para cada símbolo escoge una de las tablas de traducción en `0x883b08`/`0x883adc` según el byte `this+0x104`. Ambas tablas representan `N/R/L/D`, las direcciones numpad, A/B/C y X como valores de estado. Después busca la secuencia en muestras empaquetadas del historial circular asociado al bloque `this+0x7b0`; el cursor actual está en `this+0x7bc`. Así queda confirmado que el helper coteja secuencias completas de estado dentro de un rango, no solo dos flancos con un contador.

La demo aún no replica el formato de esas muestras ni la comparación de botones comodín. Su modelo de dos pulsaciones con ventana 15 sigue siendo aproximado. El trabajo siguiente es decodificar el ring (cadencia, wrap, neutral y flags de botones), implementar el matcher como componente portable y contrastarlo con el juego/replays. Referencias y tabla de símbolos: [INPUT_STATE.md](INPUT_STATE.md).

## Cambio y verificación

Se amplió el `dash_gate_probe` de Vita para cubrir también el lado invertido: el jugador se coloca a la derecha del rival, ejecuta `N-L-N-L`, entra en dash frontal `200` y selecciona `408:index 1` con izquierda+B. Los contratos host ahora incluyen el mismo caso. El gate ya había cubierto neutral+B/C, dash y ataques especiales, y la ventana 15/16.

Se compilaron los VPK interactivo y automático con VitaSDK. Vita3K SDL aprobó 600 frames con `dash_gate_probe=1`, roster y tarjetas 20/20, 146 texturas, cero errores de textura, 30+30 tiles de BG34, 4 recursos estáticos y 30 sprites de objetos.

- Interactivo: `artifacts/Touhou123Vita-input-ring-probe.vpk`, 82,993 bytes, SHA-256 `0af9a368d44670693179d49a8df70dba6f72a6f63de7f43c5f3e470f2ae26983`.
- Automático probado: `artifacts/Touhou123Vita-input-ring-probe-auto.vpk`, 83,159 bytes, SHA-256 `66f6f0e4e559251b5367fab19fdd3d885a2dcf60966c037ad0ef5ecffa899d6d`.
- Reporte fresco: `artifacts/vita3k-result.json` (schema 13, status `passed`, hash automático correspondiente).

La prueba host todavía no corre en este equipo porque WSL reportó `E_ACCESSDENIED` en la iteración anterior y no se encontró CMake/compilador host en PATH. La compilación ARM y la prueba guest sí cubren el caso espejo recién agregado.
