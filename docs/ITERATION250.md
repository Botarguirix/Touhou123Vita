# Iteración 2.150: input C original habilita el dispatch Suika 418

La sonda ahora encadena el constructor `PlayerSuika` (`0x609d40`), el setter original a action 200, el seeder del deque `0x46d950`, cuatro updates originales `0x46d5d0`, el matcher virtual original `0x487020` y `handleInputs` (`0x609dc0`) sobre el mismo objeto y ring.

El fallo del intento previo se explicó en el productor: `0x46d73e` escribe `Player+0x784` con `1` cuando `Player+0x764 == 1`; `+0x764` es el control C, según el empaque de muestras `0x46d5d0`. La prueba anterior dejaba C en cero, por lo que el handler cortaba antes del dispatch. Con C mantenido en la fixture mientras se ingresa NRNR, el update produce `+0x784=1`, el matcher conserva el bit NRNR, el handler alcanza `0x60be83` desde action 200, el setter original selecciona action 418 y se llega a la entrada del cleanup `0x46cac0`.

La prueba focalizada pasa 1/1. La captura física de KeyManager, servicios de escenario/suelo y el caller completo siguen controlados; por tanto, esto verifica la cadena PE y el origen del guard, no un combate jugable ni playback real. No se modificó el runtime Vita ni se generó otro VPK.

Evidencia: [reporte de sonda](../artifacts/x86-suika-constructed-handler.json), [prueba](../tests/test_x86_suika_constructed_handler_probe.py), [layout/input](INPUT_STATE.md). Siguiente: enlazar captura real de controles/replay y seguir update PAT, rival y colisión.
