# Iteración 2.66: parser C y cursor de input replay

## Implementación

Se añadió `t123/replay.h` y `src/replay.c` al core compartido. `t123_replay_parse()` valida la cabecera del perfil 2009 (`0xc8`/`0x100c8`), el límite de registros, los vectores acotados y el consumo exacto del archivo. Crea vistas a la memoria suministrada, conserva los dos IDs de personaje por registro y localiza el vector final de words sin duplicarlo. El buffer de entrada debe vivir mientras se usen el archivo y sus cursores.

`t123_replay_cursor_init/peek/next` implementa la consulta sin avance observada en `0x45bc50` y el consumo con avance de `0x42a3a0`. `t123_replay_decode_input()` separa `word & 0x03ff` y enumera los seis IDs mapeados por `0x42a410`. Ninguna API decide cuántas veces consumir por frame ni interpreta los otros campos del canal.

## Verificación

- `arm-vita-eabi-gcc 15.2.0` compiló `src/replay.c` y `tests/replay_tests.c` con `-Wall -Wextra -Werror`; enlazó un ELF de contrato para Vita.
- La suite Python completa pasó 91/91.
- El contrato C cubre parseo sintético, IDs 15/16, peek sin avance, next, agotamiento, mapeo de input, versión incompatible, truncación y bytes extra. El ejecutable ARM se compiló/enlazó, pero no se ejecutó en hardware ni Vita3K.
- El GCC host MSYS2 quedó detenido al invocar `cc1`; MSYS2 reportó que no podía crear su directorio temporal predeterminado. No se pudo ejecutar el binario de contrato host ni CTest. No se tocaron permisos ni rutas del toolchain.
- El VPK no se reconstruyó: el runtime todavía no abre un `.rep` local ni usa el cursor durante combate.

## Siguiente paso

Usar ReplayInputView+/SokuStreaming o el juego original con pausa y avance de un cuadro para asociar word, estado de `[0x85eb58]` y tick. Tras demostrar esa relación, añadir la carga desde datos del usuario y conectar el cursor a la ruta de control del jugador en modo replay; después validar en Vita3K con el replay aportado.
