# Iteración 2.09: fábrica real y actualización del objeto 801

La prueba `tools/x86_remilia_412_spawn_probe.py --real-factory` ejecuta el camino original de Remilia 412 hasta la solicitud de objeto 801, arranca el CRT del PE fijado, construye el manager y llama la factory original `0x784020`. Para hacer ejecutable el manager en esta imagen parcial, el harness adapta su interfaz de slot +4 a esa factory: no usa el vtable externo situado fuera del PE disponible.

La factory produce un hijo en `0x1100040` con action 801, seq.0, pose0, 20 poses y posición `(403,360)`. El sincronizador original publica una hitbox ofensiva desde el frame PAT (1 hitbox, 0 hurtboxes). El dispatcher original `0x7876d0` corre 60 ticks sin excepción; poses 1–19 se observan en el ciclo. El objeto sigue activo en el tick 60 y continúa moviéndose, por lo que esta muestra no prueba terminación/limpieza.

Alcance pendiente: el callback indexado de Remilia, la tabla/servicio externo `0x487ca0`, las llamadas `0x464980` y el manager completo siguen controlados por fixtures/adaptadores; el preámbulo y gates de la actualización del jugador no se ejecutan. No hay pareja defensora, resolución de colisión, daño medido, match completo ni cambio del runtime Vita/VPK. El siguiente objetivo es reconstruir el callback real y el servicio de manager/pareja para ejecutar hit-vs-hurt y comparar la vida contra los datos PAT.

Validación: prueba real de factory/update sin error; suite Python en regresión. Reporte generado bajo `artifacts/` e ignorado por Git.
