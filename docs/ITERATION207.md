# Iteración 2.107: callback Story y decoder consumen el replay Sanae completo

Se amplió `tools/x86_replay_story_callback_probe.py` para ejecutar tanto el callback Story `0x47ee10` como el decoder original `0x42a410` sobre el objeto global `0x85ec98`, con las palabras del replay Sanae fijadas por SHA-256 `6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e`. El PE 2009 se valida con SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`.

Con estado `[0x85ec08]=2` y `f0=3` preparado por el harness, cada llamada real a `0x47ee10` llega al decoder, que consume dos words: aplica las máscaras bajas a ambos canales y emite los seis setters de flags del primer word. Todas las parejas de los tres registros se agotaron sin residuo: 4,360 + 3,466 + 9,084 = **16,910 invocaciones Story**, cubriendo los 33,820 words del `.rep`. Cada invocación se verifica contra sus dos words y los seis flags.

Esto es evidencia nueva de que la ruta Story original puede consumir el archivo completo a nivel de callback. `f0=3` es aún una condición fijada en el harness; falta confirmar qué fuentes configura el juego real durante playback. Tampoco se ejecuta el loop completo del juego: las 16,910 invocaciones procesan una vez cada pareja a propósito y no demuestran que el original haga exactamente una invocación por frame. No se conectó aún el playback al runtime Vita.

La regresión `tests/test_replay_story_callback_probe.py` ejecuta el archivo completo. Reporte: `artifacts/kernel/replay-story-callback-original-2009.json`. Próximo: recuperar el estado real de las fuentes para mode/state de replay y obtener una traza de frame-step antes de elegir cadence para el core Vita.
