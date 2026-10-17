# Iteración 1.64: valores de spawn PAT de Suwako 418

## Resultado

La auditoría del constructor y del loader de poses del PE fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` resuelve los campos que lee `0076f3b4`:

- `00466e20` inicializa el objeto de pose de `0xa8` bytes con `memset(0)` y construye sus contenedores.
- `004679e0` llena los campos PAT del registro hasta `+0x80`; no hay stores de carga para `+0x98/+0x9c`. Los datos PAT `ox/oy` se leen como enteros con signo y se convierten a float en los campos de transformación `+0x3c/+0x40`; no son los offsets de spawn.
- `00466a50` copia explícitamente `+0x98` y `+0x9c` al clonar un descriptor. Como el loader no sobrescribe esos campos, conservan el cero del constructor en las poses PAT cargadas.
- `00464ae0` coloca la pose elegida en `Player+0x158`; `0076f3b4` calcula el objeto 808 con `x=Player.x + facing*descriptor[+0x98]` y `y=Player.y-descriptor[+0x9c]`. Para la ruta PAT cargada, ambos offsets del spawn son cero.

Corregí `spawn_dash_object` y el fixture Vita3K para que el objeto 808 aparezca en la posición del jugador (offsets `0,0`), en vez del offset horizontal provisional `24`. Añadí una aserción de combate que comprueba la posición del primer objeto al disparar la pose 10. La velocidad y la vida siguen siendo aproximaciones independientes sin traza end-to-end.

El extractor de recursos confirma que Suwako acción 418/secuencia 0 tiene 23 poses y que sus `ox/oy` sí varían (por ejemplo, pose 10: `38,178`). Esos valores pertenecen al anclaje de imagen/transformación y no deben sustituirse en la fórmula del objeto.

## Verificación

- `python -m unittest tests.test_suwako_418_spawn_oracle`: 2/2 pasan contra el PE original local. Prueba la aritmética de spawn con registros controlados; no ejecuta el loader completo ni una partida.
- `tools/extract_pat_pose_metadata.py original --character suwako --action 418 --sequence 0`: extrae las 23 poses efectivas de `th123c.dat`.
- Build VitaSDK correcto; VPK auto-test: [suwako-418-zero-origin-v2.vpk](../artifacts/suwako-418-zero-origin-v2.vpk), SHA-256 `2b16ce9e6b340015ce2a556ab79c4cd54caf3e4381a9a05cfbb9f914894ee732`.
- Vita3K SDL, corrida fresca schema 28/600 frames: `status=passed`, roster PAT/recursos/cartas 20/20, stage BG34 y 148 texturas; ruta de objetos 5/5, rutas con ataques 4/4, diez spawns Suwako 418, anclas 2/2. El probe confirma origen del objeto en el jugador después del cambio.
- La primera corrida detectó el fixture obsoleto que aún esperaba `offset_x=24` (error codificado 364); actualicé esa expectativa y la segunda corrida pasó. No se toma el error del fixture como fallo del runtime.

## Auditoría posterior del objeto 808

Una revisión posterior detectó que la tabla de actualización es de dos niveles: `007876d0` mapea el índice de acción a un grupo y luego consulta la tabla de funciones. Para acción `0x328`/808 resulta grupo 5 y handler `0x00788d3e`; para `0x3dd`/989, grupo 46 y `0x00797884`. La lectura previa como handlers `0x00789f9d` y `0x0078e794` era incorrecta; se retiraron de las conclusiones atribuciones de secuencia y geometría apoyadas en esas direcciones.

El initializer base `0x00799000` pone velocidad horizontal y vertical en cero, y el constructor específico de 808 (`0x007997ae`) no las sustituye. En ambas secuencias el update resta `0.2` a `vy`; además, seq0 suma `0.075` y seq1 suma `0.005` al escalar auxiliar `object+0x11c/+0x120`, no a la velocidad vertical. Al completar sus guards de colisión/suelo puede emitir dos objetos hijos `0x328` y fijar el latch `object+0x36c=1`. El helper `0x4397f0` consulta el suelo por `object.x`. El helper `0x4099f0` es un generador acotado: los hijos reciben `customData+0=-10-draw(160)` y `customData+4=10+draw(6)`, campos usados por su initializer de animación/transformación; su posición de mundo hereda `x/y` del padre. Por lo tanto, el `vx=4` configurado en el prototipo no representa la inicialización original y no tiene soporte en esta ruta estática. La ejecución dinámica controlada se documenta en [ITERATION66.md](ITERATION66.md); faltan las actualizaciones de hijos y traza PC nativa.

El verificador ahora fija por bytes las ramas de secuencia 0/1, el guard de colisión, las dos llamadas creadoras y el latch. La regresión `tests/test_object_motion_analysis.py` lee el reporte y comprueba despacho e invariantes del objeto 808.

## Alcance pendiente

La conclusión de cero procede del flujo estático del constructor/parser/copia, mientras que el oracle de handler sigue inyectando el descriptor. Falta una captura dinámica end-to-end que cargue el PAT en el juego original y registre `Player+0x158` al emitir los diez objetos; esa comparación cerrará la paridad de los valores observados en ejecución. También siguen pendientes trayectoria, ciclo de vida y daño de Suwako 418.
