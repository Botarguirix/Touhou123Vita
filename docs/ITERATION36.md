# Iteración 1.32: transforma objetos con datos del PE

## Análisis reproducible

Se añadió `tools/analyze_object_motion.py`, que exige SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`, verifica entradas de las tablas de dispatch y lee constantes del ejecutable original. Los callbacks comprobados son Alice objeto 849 (`0053c68c`), Suwako 808 (`00789f9d`, subruta secuencia 0 en `00789fb8`) y Suwako 989 (`0078e794`).

El handler x86 de Alice 408 crea 849 en `x + facing*60`, `y + 100`; Alice 418 crea 849 en `x`, `y + 50`, con secuencias 21/23 para subestados 2–5. El callback de 849 luego fija su posición al jugador para estados internos 150–158: offsets verticales 110 para 150–153, 60 para 154–157 y 100 para 158. El port refleja las coordenadas de creación y hace seguimiento mientras continúa la acción; el puente entre esos estados internos y el FSM Vita todavía no está completo.

Suwako 408 crea 989 en la posición del jugador con secuencia 5. Su callback vuelve a copiar `x` y `y - stage.ground_y` mientras el dueño está en estado 600 y el subestado no pasa de 3; la coordenada del suelo se reduce a cero en la arena Vita actual. El probe del motor verifica el seguimiento básico en el entorno de combate.

Suwako 418 crea 808 en `x + facing * stage.scale_x`, `y - stage.ground_y`; el callback de secuencia 0 consulta el suelo y transiciona al aterrizar. `stage.scale_x` y `stage.ground_y` aún deben mapearse desde la estructura de escenario, así que el offset y velocidad usados por el port para este objeto siguen provisionales.

## Cambios y pruebas

- Alice 408/418 y Suwako 408 ya usan offsets de creación y anclaje sustentados por el PE; se retiraron las velocidades inventadas de 3/7 unidades para esas rutas. Suwako 418 conserva temporalmente la simulación provisional.
- El autotest valida cinco casos de spawn, cuatro variantes con cajas ofensivas y dos casos de seguimiento por movimiento del dueño. El render del objeto se captura en [object-probe.bmp](../artifacts/screenshots/object-probe.bmp).
- `tools/analyze_object_motion.py` reproduce dispatches y constantes del PE fijado; las 8 pruebas Python pasan.
- VitaSDK + Vita3K SDL pasan el autotest schema 18 en 600 frames: PAT/roster 20/20, 145 texturas, BG34, sin fallos de textura, `object_route_probe=5`, `object_attack_routes=4`, `object_anchor_probe=2`.
- VPK: [Touhou123Vita-object-motion-auto.vpk](../artifacts/Touhou123Vita-object-motion-auto.vpk), SHA-256 `73dd3c237d56e372ad96d6bea26cc414dea66973d7e94b55915ebcf7eece0f28`.

## Siguiente análisis

Resolver el constructor del área de escenario que escribe `stage+0x98`/`stage+0x9c`, transferir esos valores al runtime de pelea y sustituir la velocidad/vida provisional de 808 por su física y transición de suelo observadas. Después comparar las cuatro rutas por frame, incluyendo impacto efectivo y eliminación, con traces PC del mismo PE y recursos locales.
