# Iteración 2.70: decodificación distinta por slot de input

## Hallazgo y corrección

El análisis de las ramas de configuración completa el hallazgo de [ITERATION169.md](ITERATION169.md): `0x43dee0` resta uno a `[0x85ec10]` y despacha por la tabla `0x43e248`. Varias ramas asignan fuentes de input distintas a `0x8602ac/0x8602cc`. Por ejemplo, las escrituras en `0x43df65/0x43df6f` y `0x43dfcb/0x43dfd5` dejan una sola fuente (`0x85ef20`, null); `0x43e04b/0x43e051` instala dos fuentes en `input_manager+0x1f0/+0x1f8`; `0x43e0f5/0x43e118` instala `0x85ef20/0x85f70c`. No se asignan nombres a estos backends sin observar la configuración efectiva.

El decoder original `0x42a410` aplica el mapa de seis flags altos solo al slot 0 (`this+0x68`). El slot 1 (`this+0xd0`) conserva únicamente los diez bits bajos. El parser C ahora expone `t123_replay_decode_input()` para slot 0 y `t123_replay_decode_secondary_input()` para slot 1. El decoder Python recibe `slot=0|1`; el resumen se actualizó a schema 2 y etiqueta la alternancia como una interpretación condicional a `f0=3`, no como un hecho medido durante la sesión.

El oráculo Unicorn se reforzó para comparar ambos masks después de cada llamada, además de cada callback del primer slot. Los tres registros completos pasan: 16.910 llamadas/parejas, 33.820 words y 101.460 callbacks. Se regeneraron `artifacts/x86-replay-input-oracle.json` y `artifacts/replay-090815-layout.json` con el modelo corregido.

## Verificación y límites

- 10/10 pruebas `test_replay_layout.py` y 93/93 pruebas Python pasan.
- VitaSDK compila `src/replay.c` y `tests/replay_tests.c` con `-Wall -Wextra -Werror`; `build-vita/replay_tests.elf` se enlazó y `readelf` confirma ELF32 ARM EABI. El contrato C todavía no se ejecutó en Vita3K/hardware.
- No se obtuvo el valor efectivo de `[0x85ec10]` en la sesión del replay, por lo que no se confirma `f0=3` natural ni la cadence del juego. Las rutas `0x47ee10`/`0x481040` y el wait-sync `0x4600fe` requieren instrumentación del loop original antes del playback nativo.
- El runtime y el VPK no cambiaron.
