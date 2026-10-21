# Iteración 2.54: el campo 194 no es cuenta regresiva de animación

La prueba de Suika 531 → 821 → Remilia 602 observa que el campo de Remilia `+0x194` vale 20 antes y después de 50 llamadas directas a su update derivado. Esa observación se mantiene como comportamiento del fixture, pero no demostraba un temporizador decreciente ni que el impacto fijara ese valor. Iteración 2.55 añade captura en `0x47b688` y establece que la respuesta de 801 modifica el campo del proyectil; ver [ITERATION153.md](ITERATION153.md).

El update derivado sigue sin consumir el campo durante ese tramo; el manager/base de una partida natural aún no está modelado. Sin cambio Vita en esta iteración.
