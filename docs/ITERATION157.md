# Iteración 2.57: replay Sanae compatible con el PE original proporcionado

El replay `090815_2219_sanae_story.rep` mide 67,881 bytes y tiene SHA-256 `6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e`; su primer DWORD little-endian es `0x100c8`.

La build actual fijada en `original/th123.exe` (SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`) usa el helper `0x43dc20`, que retorna `0xd2/0x100d2`; el caller `0x42c861` rechaza este replay por mismatch.

El ejecutable `F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe` tiene SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`. Su helper `0x43ca50` tiene bytes fijados que retornan `0xc8/0x100c8`. El caller `0x42bdd8` enmascara el DWORD leído cuando aplica el flag de modo, invoca ese helper y compara los valores; el branch de igualdad continúa el replay. El checker confirma los bytes del helper y del comparador para ese hash.

Resultados reproducibles:

- `artifacts/kernel/replay-compatibility-original-2009.json`: `compatible_with_exe=true` para el PE original suministrado.
- `artifacts/kernel/replay-compatibility-pinned.json`: `compatible_with_exe=false` para el PE fijado actual.
- El checker valida ambos perfiles por SHA-256 antes de interpretar sus firmas y ahora escribe los reportes con `--output`:

```powershell
python tools/x86_replay_compatibility_probe.py "F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\replay\story\090815_2219_sanae_story.rep" --exe "F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe" --output artifacts/kernel/replay-compatibility-original-2009.json
python tools/x86_replay_compatibility_probe.py "F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\replay\story\090815_2219_sanae_story.rep" --output artifacts/kernel/replay-compatibility-pinned.json
```

Esto establece compatibilidad estática de versión únicamente. No se verificó reproducción, decodificación de frames o entradas. El README de [SokuMods](https://github.com/SokuDev/SokuMods) documenta que se puede arrastrar un `.rep` sobre `th123.exe`; ReplayInputView+ permite pausar con F11, avanzar un cuadro con F12 y mostrar hitboxes con F4 (confirmar bindings en la instalación). Siguiente: reproducir el archivo con la build 2009 y capturar 10–30 cuadros alrededor de un combate para convertirlos en una traza de referencia. La ventana exclusiva del juego no pudo capturarse desde esta sesión, así que la reproducción queda pendiente. No cambió código Vita ni se recompiló el VPK.
