# Iteración 2.167: action96 ejecuta 181 ticks PE sin salir; fixture alcanza un límite de contexto

Se amplió `tools/x86_suika_constructed_handler_probe.py` para usar el Player Suika construido por el PE, restaurar el snapshot post-hit, aplicar el setter original con action96 y correr el timer común, `handleInputs` neutral y updater virtual con el PAT action96 original. La entrada a 96 es explícitamente forzada en esta subprueba; no representa el disparador natural.

El setter termina sin error. En 181 actualizaciones válidas el action permanece en 96 y el frame pointer se mantiene dentro de los diez frames PAT originales. El handler compartido hace la solicitud a `setSequence(3)` desde `0x4851e7` cuando el contador estaba en 1. El estado de secuencia avanza más allá de 3 mientras la estructura singleton resuelve todos los índices al nodo PAT seq0 (`prev=self` confirmado en el loader), por lo que el payload de diez frames se repite. No hay escrituras a `+0x884` ni setters de acción para salir de 96 durante este tramo.

En la iteración siguiente del loop el harness detiene la emulación al detectar fetch de código en dirección baja (esta corrida: `0x0`) después del epílogo que retorna desde la ruta común. Como el probe no tiene el manager/round caller completo y su stack/servicios están parcialmente controlados, esto solo identifica un límite del contexto emulado; no se afirma que el juego real termine action96 ni que se bloquee igual. Resultado seguro: no se observó transición de salida de 96 en las 181 actualizaciones completadas.

Se agregó una regresión al test de la sonda: exige action96 durante el tramo válido, PAT frame pointers válidos, llamada `setSequence(3)`, cero escrituras `+0x884` y registro explícito del fetch de baja dirección. Suite del probe y compilación Python pasan; no hay cambios al runtime Vita ni VPK.

Siguiente: reconstruir el manager/caller de combate o hacer un harness frame-step que conserve el stack/callback real para observar la salida natural de action96 y el avance del round. No portar la transición hasta verificarla.
