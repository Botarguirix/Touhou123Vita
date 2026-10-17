# Iteración 1.12: 66B/66C requieren dash frontal

## Evidencia de la referencia

En el EXE 1.10a fijado por SHA `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`, los handlers de Reimu (`004ae670`) y Cirno (`006fb8b0`) despachan `408` (66B) y `418` (66C) únicamente desde la acción `200`, con dirección positiva hacia el rival y `param+0x1d6 == 0`. Antes de cambiar a esas acciones consultan el move lock de 408/418. `0048a220` comprueba el move lock de 200 y selecciona el dash frontal a partir de los flags de dirección o del buffer de input. Los pseudocódigos exportados previamente están en `artifacts/kernel/<sha>/004ae670.c`, `006fb8b0.c` y `0048a220.c`. Intenté repetir la exportación en un proyecto aislado porque el proyecto Ghidra original estaba bloqueado por otro propietario; Ghidra importó el PE, pero su compilador de scripts falló al leer bibliotecas externas, así que no cuento esa exportación como nueva evidencia.

## Cambio del prototipo

`src/fight.c` ya no puede seleccionar 408/418 al pulsar adelante+B/C desde neutral. Añade un estado de dash frontal 200 tras dos pulsaciones de la dirección hacia el rival y solo permite esas rutas especiales mientras continúa el dash y se mantiene la dirección. La prueba incluye controles negativos (adelante+B/C desde neutral no produce 408/418) y positivos (doble toque, dash 200, después B/C). El siguiente análisis recuperó los patrones `NRNR`/`NLNL` y un rango de historial de 15 ticks para ambos; la implementación anterior de 10 ticks queda superada por la iteración 1.13. La duración simplificada de la animación y el significado completo del umbral `sVar1 <= getMoveLock(action)` siguen pendientes. `fight_reset` limpia el historial para que el primer toque tras reiniciar se detecte.

## Validación

Compilación VitaSDK completada para VPK interactivo y automático. Vita3K SDL pasó 600 frames y el sondeo guest `dash_gate_probe=1` verificó los bloqueos negativos desde neutral, estado `200` tras doble toque y activación de `408:index 1`/`418:index 0`. La pelea registra 3 dashes, A=1, B=1 y C=1; roster/tarjetas 20/20; sin errores de textura; los dos planos BG34 30/30, bitmaps 4/4 y animación de objetos 30/30. La suite host no se pudo ejecutar: WSL devolvió `E_ACCESSDENIED` al crear la instancia.

- Interactivo: `artifacts/Touhou123Vita-dash-gated.vpk`, 82,741 bytes, SHA-256 `ab76e8a7a8915a80469755ba80494da24deadbebdf5681091c36a5c5133f3e2c`.
- Automático: `artifacts/Touhou123Vita-dash-gated-auto.vpk`, 82,907 bytes, SHA-256 `c4761950decf3aeb7149215b920eb7372ee56cd1ad157aee4c35f89575233279`.
- Reporte fresco: `artifacts/vita3k-result.json`.

## Continuación

Exportar y decodificar `00487020` y los campos del input buffer con una sesión Ghidra que compile los scripts locales; luego medir el umbral/ventana de inputs y locks por personaje. Extender la condición de estado 200 y la prueba a todos los PAT que implementan esa ruta, y continuar con movimiento, sistema de cartas, habilidades, objetos, escenarios, colisiones y rondas.
