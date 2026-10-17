# Iteración 1.67: encadenamiento experimental del split 808

## Avance

Se extendió `tools/x86_suwako_808_object_oracle.py` para encadenar la emisión real del padre 808 con el initializer base/acción del hijo y ocho llamadas al update original por hijo. El PE de referencia conserva SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. El handler padre ejecuta el split con RNG controlado `[10,2,20,4]`; el initializer hijo ejecuta su aritmética x86, con servicios seno sustituidos por los resultados Python de `math.sin` y callback de recursos neutralizado.

Para las llamadas capturadas `[-20,12,1]` y `[-30,14,1]`, suponiendo explícitamente secuencia 1, los componentes iniciales son aproximadamente `(-4.10424,11.27631)` y `(-7,12.12436)`. El update resta 0.2 a `vy` por tick. En el tick 1, partiendo de `(300,400)`, se observan `(295.89575,411.07632)` y `(293,411.92435)`. A ocho llamadas emuladas, las posiciones son `(267.16602,483.01050)` y `(244,489.79486)` (captura completa en `artifacts/x86-suwako-808-child-trajectories.json`).

Cada secuencia de inicialización/update usa una instancia Unicorn limpia para evitar que el estado de una corrida contamine a otra. La prueba de regresión comprueba los dos datos de fábrica, dos inicializaciones y los primeros cuatro ticks. Los servicios de fábrica/recursos/escenario siguen controlados y no se ejecuta la creación real end-to-end.

## Límite de interpretación

El cuarto argumento de factory vale 1 para ambos hijos y la instrucción de llamada pasa por `0046eb30` a un virtual constructor. La vista estática muestra que la rutina intermedia conserva ese argumento como configuración, pero no se ejecutó la cadena virtual completa hasta demostrar que selecciona `object+0x13e=1`. Por eso la secuencia 1 de los updates es todavía una hipótesis explícita; estas coordenadas no son aún una trayectoria confirmada de partida natural. No se cambió el comportamiento de combate ni se generó un VPK.

## Validación

- `tests/test_suwako_808_object_oracle.py`: 7 pruebas pasan, incluyendo split, initializer y trayectoria controlada.
- Artefacto reproducible: `artifacts/x86-suwako-808-child-trajectories.json`.
- Pendiente: emular el virtual de factory, observar el valor real de secuencia y el estado persistente entre frames; después incluir colisión, daño, vida y terminación antes de sustituir el placeholder Vita `vx=4/life=90`.

## Corrección de Iteración 1.67 (Iteración 1.69)

La primera traza de ocho pasos forzaba un subframe creciente sin conservar la operación real del handler. El análisis del branch `seq1` (`00788d60–00788da2`) muestra que cada callback resta 0.2 a `vy`, suma 0.005 a `+0x11c/+0x120`, compara `+0x113` con 8 y, al alcanzar el umbral, resta 8. El reloj del engine debe avanzar ese byte entre callbacks. Por ello, la trayectoria de ocho posiciones publicada arriba no representa el cadence del juego y queda supersedida por `ITERATION69.md` y el JSON regenerado. La secuencia 1 todavía se suministra explícitamente y no está atribuida al arg4.

## Corrección de secuencia (Iteración 1.70)

La secuencia del objeto no se toma del argumento 4 de la fábrica. El contrato de la ruta documentado en [ITERATION34.md](ITERATION34.md) establece que Suwako `initializeAction` (`00799000`) lee `customData[2]` y lo usa en `setSequence`. En el split 808 ambos custom data terminan en `1`; el harness ahora deriva el selector de ese float y confirma que el initializer x86 procesa secuencia 1. `arg4` continúa siendo un argumento independiente de la fábrica. La traza anterior que llamaba “hipótesis” a la secuencia queda supersedida en ese punto; la incertidumbre restante es la configuración real del reloj/subframe desde el engine, además de colisión y ciclo de vida.

## Correcciones posteriores

La secuencia se resolvió desde customData[2] en ITERATION70. La interpretación de +0x113 como subframe/reloj en ITERATION69 era incorrecta: es el byte alpha de RenderInfo; véase [ITERATION71.md](ITERATION71.md). Las coordenadas previas quedan supersedidas por el artefacto actual, que modela alpha controlado.
