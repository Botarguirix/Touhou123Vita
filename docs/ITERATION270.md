# Iteración 2.170: escritores positivos de `Player+0x884` hallados en jump tables

La búsqueda anterior solo seguía flujo directo y omitía los destinos de `jmp [table]`. El nuevo [escáner](../tools/scan_player_field_884.py) valida cada entrada slot 10 contra la vtable del manifiesto, el puntero a caso dentro de su tabla y la instrucción de store, además de encontrar el registro que se prepara con `0x12c`. El reporte reproducible está en [player-field-884-jumptable-cases.json](../artifacts/player-field-884-jumptable-cases.json). Confirma asignaciones positivas de `0x12c` (300) a `Player+0x884` en nueve updates:

| Personaje | Update slot 10 | Tabla | Caso que asigna 300 |
|---|---:|---:|---:|
| Reimu | `0x490490` | `0x4a7854` | `0x490795` |
| Marisa | `0x4bd430` | `0x4d023c` | `0x4bd6f2` |
| Alice | `0x5100b0` | `0x51e18c` | `0x51026a` |
| Patchouli | `0x541290` | `0x553c7c` | `0x5414cd` |
| Cirno | `0x6e31a0` | `0x6f54cc` | `0x6e33ce` |
| Meiling | `0x71a5e0` | `0x72c0c0` | `0x71a81e` |
| Sanae | `0x73c1b0` | `0x74a8a0` | `0x73c3dd` |
| Suwako | `0x765ab0` | `0x7819e4` | `0x765ebb` |
| Utsuho | `0x79f440` | `0x7b4f60` | `0x79f78b` |

En cada función, el registro usado por el caso se prepara con `0x12c`; el flujo común después del salto decrementa el campo si es mayor que 1 y lo limpia al llegar a 1, confirmando un contador temporal en esos caminos. Antes del despacho, el update obtiene el elemento 0 de la deque en `Player+0x5e8` y lee su primer `ushort`; el layout SokuLib y los CSV comunes permiten identificarlo como un ID del espacio de cartas de sistema, con los límites descritos abajo.

La condición previa común observada en las nueve funciones es `Player+0x7cc == 2`, al menos una carta (`byte Player+0x5e6 >= 1`) y lectura del elemento 0 mediante `0x456c80`. No etiquetar `+0x7cc` como modo de juego: el constructor del Player copia ese byte desde la estructura de inicialización junto al puntero del gestor de entrada (`+0x750`), y `0x46d7d0` lo usa para elegir una ruta virtual de actualización de input. El significado exacto del enum sigue pendiente. El `cmp` de ID acepta el máximo propio de cada personaje: Reimu `0..15`; Marisa, Alice y Patchouli `0..11`; Cirno, Meiling y Sanae `0..7`; Suwako `0..19`; Utsuho `0..15`. En estas rutas la tabla de mapeo empieza en `jump_table+4`; todos sus bytes hasta el guard máximo son cero, por lo que cada valor permitido cae en la entrada 0, el caso que asigna 300. `0x456c80` es el indexador genérico de la deque: valida el índice contra `+0xc/+0x10`, resuelve bloque/elemento mediante `+4/+8` y devuelve el puntero al elemento. SokuLib ubica la deque en `Player+0x5e8`, modela cada elemento como `Card` con `unsigned short id` en offset 0 y `CharacterManager::generateCard` copia el ID de entrada en `Card.id`. El cruce de `common/spellcard.csv` resuelve la discrepancia: las filas tipo `0` tienen IDs `0..20`, mientras las cartas de personaje tipo `1` usan IDs `100+`. Por tanto, los rangos consultados por estos handlers coinciden con IDs del espacio común de cartas de sistema; no son IDs 100+ de skill/spellcard. El ID concreto no selecciona una acción distinta en este dispatch: todo ID admitido selecciona el mismo caso que carga 300. El escáner registra los gates de tipo de input/mano, el indexador, esa intersección y el test fija el dominio común `0..20`.

La prueba `tests.test_scan_player_field_884` fija el hash del PE, las nueve parejas vtable/tabla/caso, los límites del guard, la tabla de bytes nulos y los valores que seleccionan el caso 0. Iteración 2.171 amplía el análisis: enlaza el expiry de Reimu con la acción común 1201 y recursos del gauge Spell Break, pero todavía no demuestra la alcanzabilidad del modo durante juego natural.

Este hallazgo corrige el alcance de la búsqueda anterior: sí hay productores positivos directos, pero los nueve pertenecen a updates de otros personajes. El update slot10 de Suika no contiene referencia directa a `+0x884`; su callback de transición 97→96 lee el campo y el helper accesible limpia a cero. Por eso las asignaciones de 300 en otras clases aún no explican la recuperación natural de Suika. El flujo exacto del timer de action96 sigue probado solo con entrada forzada y HUD aislado (Iteración 2.169).

## Siguiente

La identidad del campo como ID runtime de carta tiene apoyo convergente en el layout/copia de SokuLib y el dominio de cartas comunes 0..20; también están fijadas las condiciones estáticas `+0x7cc==2` (tipo de input según el dispatcher), mano no vacía e índice 0. El expiry Reimu termina en acción común 1201, cuyo PAT contiene assets llamados Spell Break gauge/bar. Falta observar la transición en juego y demostrar la semántica del tipo de input, así como localizar si una rutina genérica de round/hit escribe el campo de Suika. Ampliar análisis de indirect calls/copies antes de inferir que el productor está fuera del Player. Ver [ITERATION271.md](ITERATION271.md).
