# Iteración 1.69: cadence persistente de Suwako 808

## Corrección y resultado

Al inspeccionar el handler real seq.1 en `0x788d60–0x788da2`, encontré que cada callback aplica gravedad `vy -= 0.2` y actualiza `+0x11c/+0x120 += 0.005`, pero solo integra posición cuando el subframe `+0x113` llega a 8; entonces resta 8. El engine externo avanza ese subframe entre callbacks. La corrida previa forzaba un desplazamiento en cada invocación y sobrestimaba la distancia; queda supersedida.

El harness ahora conserva `+0x11c`, la velocidad y posición, toma el subframe devuelto por el handler y modela un incremento de un paso del reloj externo entre callbacks. Con secuencia 1 derivada de `customData[2]` (contrato confirmado en `ITERATION34.md`) y servicios de suelo/colisión/RNG/seno controlados, tras 24 callbacks (tres integraciones espaciales) los estados son:

- Custom data `[-20,12,1]`: `(x,y)≈(287.6873,428.4290)`, `vy≈6.4763`, escalar `≈0.8700`.
- Custom data `[-30,14,1]`: `(x,y)=(279,430.9731)`, `vy≈7.3244`, escalar `≈0.8700`.

JSON actualizado: `artifacts/x86-suwako-808-child-trajectories.json`. El handler/initializer x86 y sus operaciones de punto flotante corren en Unicorn; factory y servicios de engine siguen controlados, el retorno sintético usa shim y el valor de secuencia se deriva de `customData[2]`; el incremento externo de subframe sigue modelado y pendiente de capturarse desde el engine. Es una traza de cadence corregida, no una trayectoria end-to-end.

## Validación

- `tests/test_suwako_808_object_oracle.py`: 7/7 pasan. La nueva regresión comprueba el umbral de subframe, el avance de gravedad/escalar y los desplazamientos espaciados.
- No se modifica el runtime Vita ni se crea VPK; falta capturar la cadena virtual real de factory, la secuencia inicial, colisión/cajas, vida y terminación.
