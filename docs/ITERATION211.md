# Iteración 2.111: los callers encontrados son rutas de estado/configuración

Se recuperaron los límites de los tres métodos que contienen los callsites de [ITERATION210.md](ITERATION210.md), con el PE 2009 fijado por SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`:

- El handler de entrada `0x4209c1` llama a `0x43dee0` cuando `this+0x58==1` y `this+0x4f60>=0`, después de `0x41ffa0`. El selector que leerá el dispatcher sigue siendo el global `[0x85ec10]`; esta rama no fija su valor.
- El handler `0x425703` llama al dispatcher solo cuando `[0x85ec10]` leído por `0x43ccd0` equivale a `EBX=1`. Esa entrada selecciona el backend 1, cuya rama deja una sola fuente (`0x85ef20/null`). Si el getter devuelve cero, llama a `0x43ccf0`, que también instala una sola fuente. Esta ruta no es el selector Story 6/estado 2.
- El handler `0x44af00` llama al setter con argumentos `(modo=7, estado=1)`, prepara/copia campos de configuración e input y después llama a `0x43ccf0`. Tampoco demuestra configuración de replay Story.

La sonda registra estas guardas y el reporte separa explícitamente backend 1, modo 0, y preset modo 7/estado 1. Las pruebas `tests.test_replay_manager_selection_probe` pasan 1/1; `git diff --check` no reporta errores. No cambian runtime ni VPK.

Esto descarta usar esos callsites como prueba de `f0=3` durante playback. El candidato de replay `(6,2)` sigue localizado en `0x426de6`; falta hallar su caller/camino de entrada o capturar el estado live durante una sesión compatible. La automatización de ventana continúa temporalmente indisponible por el error del helper documentado en [ITERATION210.md](ITERATION210.md).
