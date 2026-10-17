# Iteración 0.7: referencia detallada de variantes PAT

Se amplió `resource_probe` con `--pat-detail`, que exporta cada pose, duración, daño, stun, flags y cajas ofensivas de los PAT. La corrida sobre los tres DAT locales produjo 76,357 filas (5,970,466 bytes) para las 22 carpetas PAT. La nueva [DASH_ATTACK_REFERENCE.md](DASH_ATTACK_REFERENCE.md) resume 117 variantes de las acciones 408 (`66B`), 409 (`j4B`) y 418 (`66C`).

La matriz confirma diferencias por personaje. Reimu tiene 66B dañino en índice 1 (dos poses en bucle, 800 de daño en los datos PAT) y 66C en índice 0 (dos poses con cajas ofensivas, 900). Cirno tiene 66B en índice 1 (ocho poses, 180 por pose), j4B en índice 1 (tres poses, 400) y 66C en índice 0 (tres poses dañinas, 750). Los índices 400/410 neutros sin hitboxes no explican estos ataques; no se debe convertir cada botón en la misma acción para todos los personajes.

La API pública confirma que `00487ba0` es `useSkill`; los helpers comunes relacionados con input son `handleGroundBE` (`00487990`) y `handleAirBE` (`00487ab0`). Se actualizó `tools/ghidra/ExportKernel.java` para exportar estos helpers y las rutas de dash/flight. Los ocho contratos host pasan después de añadir el modo detallado al probe. No se generó una nueva VPK porque esta iteración cambia herramientas y evidencia de análisis, no el juego.

## Pendiente para convertir datos en comportamiento

Seguir el buffer de movimientos y las llamadas a `setActionSequence`/`setSequence` para cada personaje, identificar cuándo se seleccionan los índices activos de 408/409/418 y añadir objetos para los B/C que producen proyectiles. El reporte no valida todavía input, daño real ni paridad con Vita3K. Después debe ampliarse la cobertura a las demás acciones y escenarios.
