# Iteración 2.24: primer hit-confirm x86 entre acciones de personaje

Se amplió el harness PAT para conservar los 40 bytes originales de `CharacterFrameData` en cada pose. El resolver `0x47aa50` consume campos que el parser anterior descartaba: para Remilia 320/seq.0/frame3 el byte PAT en offset `0x26` vale 100. Con esos datos, una corrida controlada de `0x47c770` alcanza la rama de impacto normal y cambia `attacker+0x190` (`CollisionType`) de 0 a 1. Antes, al inicializar esos bytes en cero, caía en la rama air-hit (7).

La geometría confirmada fue Remilia 320/frame3 contra Remilia 321/frame0 (`frameFlags=0x41`). La pose 602/frame0 (`0x3041`) no sirve como objetivo para `0x47c770`: la función la descarta por `frameFlags&0x2000`. Acción 321/frame0 sí pasa ese filtro. El nuevo probe reproducible ejecuta los dos constructores base, setters e inicializadores, selector de pose `0x464b50→0x464ae0`, sincronizador de cajas y el resolver. Llega a la escritura normal `attacker+0x190=1` en `0x47ab26`.

La estructura comparativa de SokuLib nombra `+0x498` como `redHP`, `+0x4b4` como `comboCount`, `+0x4b6` como `comboDamage`, `+0x4b8` como `comboLimit`, `+0x4ba` como `untech` y `+0x4be` como `realLimit`; deja `+0x4bc` y `+0x4c4` sin identificar ([Player.hpp](https://github.com/SokuDev/SokuLib/blob/master/src/Player.hpp)). Estos nombres son referencia comparativa, no sustituyen la traza del PE local.

El desensamblado aclara que `0x439850` compara `Player+0xf0` (Y) con `0x4397f0`, un límite inferior derivado de `Player+0xec` (X); no es un guard de HP. Con Y=180/X=320, devuelve 1. Como `+0x4c4=0`, el gate `0x47ac67` permite elegir la reacción. La ejecución confirma `attacker+0x190=1`, incrementa `defender+0x4b4` (comboCount) y llama al emisor de efecto `0x479cb0`. SokuLib identifica `0x8985f0` como `EffectManager_Effect`; la sonda instala un `CreateEffect` observable que registra la petición `0xC9` en `(7,50)` y devuelve un objeto sintético para continuar el resolver.

El resultado clave es daño real del PE: al conectar los punteros de datos de ataque/defensa que consume `0x463f50`, el cálculo toma los 200 puntos de PAT; en `0x47b11c` el defensor tiene 1000 HP y `BX=200`, y en `0x47b123` queda en 800 (`Player+0x184`). Sin esos punteros, el daño calculado era cero pese al PAT correcto. La ejecución se interrumpe más tarde durante inicialización/limpieza de respuesta (`EIP=0`), pero no antes de hit-confirm, efecto solicitado, combo y pérdida de vida. `context+0x7c+team*4` permanece en 1000 y no es el contador de HP en esta ruta.

La instrumentación de selección añadió dos datos: el byte `attackerFrame+0x48` observado es 0 y el resolver llama el setter del defensor con acción 50 mientras este aún está en 321. Remilia sí contiene la acción 50. El fallo posterior no se explica por un PAT ausente; la siguiente prueba debe comprobar el resultado del lookup y los argumentos/contexto de inicialización de la secuencia 50.

La regresión Remilia 412 sigue pasando 5/5; la nueva `tests.test_x86_player_pair_hit_probe` verifica el hit-confirm de dos Players por separado. El daño de 120 del objeto 801 continúa siendo una ruta independiente. El VPK/runtime no cambió.

## Siguiente paso

1. Registrar el resultado del lookup PAT para acción 50 y compararlo con una inicialización normal de esa acción; luego completar la transición de reacción que actualmente termina en `EIP=0` después de aplicar el daño. El objeto de efecto continúa siendo sintético y su factory/render no están probados.
2. Reproducir un caso equivalente desde replay PC y cotejar frame, HP 1000→800, combo, reacción, hitstop y acción; usar ReplayInputView+/LabTool y SokuStreaming si exponen esos campos.
3. Conectar la actualización de dos jugadores a la secuencia de input/move-lock y verificar cancel natural a 321 tras confirmación.
4. Separar un perfil Vita3K smoke con criterios propios del gate integral de 600 frames; correr smoke en cambios cortos del runtime y gate full antes de entregar VPK.

## Alcance y evidencia

La muestra x86 ejecuta el resolver original del PE bajo Unicorn con PAT real, los dos constructores/setters base y posiciones/mapas de lookup controlados; verifica hit-confirm, petición de efecto y HP 1000→800. La respuesta completa aún no termina y no se compara con replay. Las suites `tests.test_remilia_412_spawn_probe` (5/5) y `tests.test_x86_player_pair_hit_probe` (1/1) pasan. Fuentes de aceleración y reutilización: [ANALYSIS_AND_TESTING_TOOLING.md](ANALYSIS_AND_TESTING_TOOLING.md).
