# Iteración 2.152: geometría PE confirma contacto tras Suika 200→418

Se extendió Iteración 2.151 después de alcanzar action 418/seq.2/pose.0 en tick 16. El Player atacante conserva su estado construido y timeline original; se cargan las cajas del frame PAT auténtico (daño 900, una attack box) y se prepara un defensor Suika neutral con su hurt box PAT. Con posiciones coincidentes, el helper PE de hit-vs-hurt `0x47a5b0` devuelve contacto: una hitbox contra una hurtbox.

La conversión local→mundo aplica la transformación `x + facing*x_local`, ordenando extremos, y `y_local - y`, ya contrastada en las sondas de cajas. El test verifica que el helper geométrico original confirma el solapamiento, pero no ejecuta aún `0x47c770`; HP, reacción y daño efectivo en esta cadena quedan pendientes. Tampoco es input físico/replay ni una pelea completa, y los callbacks de escenario siguen controlados.

Las pruebas Suika focalizadas pasan 3/3; no hubo accesos inválidos ni cambios en runtime Vita/VPK.

Evidencia: [reporte](../artifacts/x86-suika-constructed-handler.json), [sonda](../tools/x86_suika_constructed_handler_probe.py), [test](../tests/test_x86_suika_constructed_handler_probe.py). Siguiente: inicializar stats/equipos/servicio de efectos y ejecutar resolver `0x47c770` sobre estos mismos objetos para medir HP y acción de reacción.
