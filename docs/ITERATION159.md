# Iteración 2.59: ciclo visual secundario de Remilia 801 en Vita

Porté al runtime la emisión de objetos 801/seq.1 desde Remilia 412: el padre emite al primer update y después cada tres updates. Los secundarios muestran pose PAT inicial, duran 18 updates efectivos y el padre se retira al tick 73 del manager. En la regresión del runtime hay 26 objetos creados en total (el raíz y 25 emisiones), queda el padre retirado y permanecen seis secundarios activos con edades `[16,13,10,7,4,1]`.

La fixture x86 observó separación aproximada `(-33.8289,+12.3127)` en sus coordenadas; la proyección del runtime a media escala y coordenadas enteras da `(-17,+6),(-17,+6),(-17,+7),(-17,+6),(-16,+6)`. El gate verifica ese rango discretizado, junto con la vida, secuencias y conteos. Prueba `tests.test_remilia_412_spawn_probe`: 5/5. La compilación cruzada VitaSDK con `-Wall -Wextra -Werror` pasó.

Vita3K SDL aprobó el gate schema46 durante 600 frames: `regression_gate=1`, cinco rutas de objetos, cuatro con ataques, ráfaga Suwako de diez emisiones, Remilia linger y ciclo completo de trails; contratos y capturas BG33 también pasaron. VPK de auto-prueba: SHA-256 `e08d9412508058c3e8e29e9dd63848207174a781ddf1fdcae9b5d00c2c4f935f`.

La validación de esta ruta sigue usando la fixture x86 controlada y no sustituye la reproducción frame-step del replay ni una pelea completa con IA/guardia. Los efectos de spell, otras rutas especiales, recursos comerciales externos, las mecánicas de todos los escenarios y mediciones de FPS en hardware Vita siguen pendientes.
