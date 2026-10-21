# Iteración 2.69: origen de los flags del decoder de replay

La revisión del PE original 2009 localizó el escritor del byte `this+0xf0`: `0x42d6b0`. La única llamada directa hallada es `0x4281a2`. El segundo argumento apunta al estado global de input en `0x860288` (obtenido por `0x43cce0`); el primer argumento es cero en esta llamada. El escritor lee las fuentes en `0x8602ac` y `0x8602cc` y calcula:

```text
f0 = 2 * (input_state[0x44] != 0) + (input_state[0x24] != 0)
```

La estructura global se prepara en las rutas de configuración `0x43d8e0`/`0x43e126`; sus campos de fuente cambian según el backend y configuración de input. El dispatcher `0x43dee0` toma el valor de `[0x85ec10]` y selecciona una rama por una tabla en `0x43e248`. Las ramas observadas escriben tanto solo `0x8602ac=0x85ef20, 0x8602cc=0` (un slot) como dos punteros no nulos (`[0x85ec20]+0x1f0/+0x1f8` o `0x85ef20/0x85f70c`). Luego `0x42d6b0` delega la construcción de estado a `0x42d420`. Esto confirma que `f0` depende del backend/configuración activa; no es un parámetro fijo del formato replay. Aún falta obtener el valor seleccionado en la sesión real de replay.

Las funciones `0x47ee10` y `0x481040` llaman ambas a `0x42a410` cuando el modo global es 2. Sus punteros aparecen en tablas/vtables del PE (`0x82196c`, `0x821924` y `0x8219d4`). Esto confirma dos rutas de actualización que pueden ejecutar el decoder; todavía falta demostrar si son clases/modos mutuamente excluyentes o si alguna secuencia alcanza ambas dentro de un mismo tick. No contar cada llamada como un frame.

En consecuencia, el oráculo de [ITERATION168.md](ITERATION168.md) es válido para demostrar el comportamiento de `0x42a410` con `f0=3`, y el replay real pasa todos sus pares bajo esa condición. No demuestra que el constructor de cada ronda configure ambos slots ni que una llamada equivalga a un frame. El punto `0x4600fe` sigue siendo otra ruta: consulta el word actual, lo compara con `[0x85eb58]` y solo avanza al coincidir.

Siguiente: determinar qué valor de `[0x85ec10]` se usa durante playback y trazar los dispatchers de vtable de ambos métodos para establecer si se llaman en rutas excluyentes o dentro del mismo tick; luego integrar el cursor al motor Vita.
