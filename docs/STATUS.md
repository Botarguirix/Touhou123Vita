## Iteración 2.199: escala de cajas y detección de impactos

Cajas PAT ordinarias y separación corporal pasan a unidades completas, contrastadas con el helper x86 (incluido ceil de posición). Se corrigió el registro de impactos en el frame del comando: Udonge 408:1/800 se registra en frame 0 y 409:1/400 conserva una sonda dedicada. Suite Python completa 146/146 y pruebas nativas de arena/colisión aprobadas; Vita3K SDL 600 frames passed, ambos VPK verificados. La suite C general conserva el fallo previo del fixture Suika. Falta migrar offsets/movimiento de objetos que siguen a media escala, especialmente Remilia 801. [ITERATION299.md](ITERATION299.md).

## Iteración 2.198: inicio PAT en 480/800 y cámara 640

El reset común x86 confirmó posiciones (480,0)/(800,0), orientación +1/−1 y velocidades cero; el constructor de cámara confirmó (640,0,1). El port aplica esos valores al reinicio PAT y mantiene explícitas las disposiciones de pruebas y selección. Python 23/23, prueba nativa de arena/reinicio aprobada y Vita3K SDL 600 frames passed, incluido `arena_spawn_contract=1`. Ambos VPK están reconstruidos y verificados. Persiste el fallo previo del fixture nativo Suika; falta escala de cajas y comparación visual con PC. [ITERATION298.md](ITERATION298.md).

## Iteración 2.197: arena PAT de 40 a 1240

Se reemplazó el límite de demo 35–605 en movimiento PAT y habilidad aérea por 40–1240, contrastado ejecutando la rama PE de arena plana. La prueba nativa nueva atraviesa la mitad derecha y verifica cámara/paredes; Python 11/11. Vita3K SDL pasó 600 frames y ambos VPK pasan validación estructural. La suite nativa general conserva un fallo previo del fixture Suika, reproducido antes y después del cambio. Posiciones iniciales, escala de cajas y paridad visual siguen pendientes; 27%. [ITERATION297.md](ITERATION297.md).

## Iteración 2.196: presentación dentro del lienzo 4:3

Los quads ya no invaden las bandas laterales. El runner comprueba los píxeles de las dos bandas de BG36; Vita3K SDL pasó 600 frames y las pruebas focales 7/7. Ambos VPK reconstruidos pasan validación estructural. Se abrió el original, pero Computer Use no pudo capturar imágenes del juego ni del Explorador: no se observó combate PC. La referencia BG36 debe obtenerse en Meiling contra Marisa; el contenido del replay Sanae corresponde a BG30/BG12/BG33. Posicionamiento y paridad visual siguen pendientes; global 27%. [ITERATION296.md](ITERATION296.md).

## Iteración 2.195: cámara de captura BG36

El reporte guarda cámara x/y/zoom en el mismo frame de BG36 y el runner valida su rango. Vita3K SDL schema46/600 pasó con cámara (392,0,1), nubes (-401.5,-301.0), 25 tiles y cuatro auxiliares. Auto VPK SHA-256 `ac19b63c4c2b0bec10f024210b83b8b1ede2197a4b00d08a8adfd250a43bc7f8`. Replay Story local compatible con el EXE por formato, todavía sin etapa identificada. Falta comparación visual; global 27%. [ITERATION295.md](ITERATION295.md).

## Iteración 2.194: gate de scroll BG36 en combate

El contrato Vita3K verifica el estado de las dos nubes BG36 tras los updates de combate, con la cadencia y wraps del PE. Tests focales 7/7; Vita3K SDL schema46/600 pasó, incluyendo posiciones −401.5/−301.0 tras un tick, 25 tiles y 4 auxiliares. VPK auto SHA-256 `e51a14a26d816133641acefcee6ae74bf6103f38813e511e7c7adc1c6a67534c` (8 entradas válidas); VPK interactivo SHA-256 `fef364b7eca5b878e872764f14a6c9a767056c077df6daaf029218448ccf16f4` (7 entradas válidas). Sigue pendiente la composición/cámara comparada con PC; el avance global permanece en 27%. Ver [ITERATION294.md](ITERATION294.md).

# Estado del proyecto

## Iteración 2.193: retícula BG36 en orden de slots PE
- El constructor carga `[01][01]` en slot 0 y aumenta las filas; se eliminó la inversión `[05]` que el port aplicaba en combate. La máscara de las 25 texturas disponibles ahora es `0x3ffff79c`, que refleja los cinco slots ausentes del DAT local.
- Pruebas focales BG36/BG37/BG38 7/7. Vita3K SDL pasó schema46/600, `regression_gate=1`, selector interactivo BG36, 25 tiles, auxiliares 4/4 y BG33 24 tiles. Auto VPK SHA-256 `bd7f3c82b324ee2f64b4b9625313129f6e314d0d42867bc6ecea47dfd85bcc4f`; captura: [fight-bg36.bmp](../artifacts/screenshots/fight-bg36.bmp).
- La cuadrícula ahora enlaza correctamente sus filas, pero falta verificar contra el mismo replay en PC la composición y cámara completas. Global 27%; BG36 no se marca terminado. [ITERATION293.md](ITERATION293.md).

## Iteración 2.192: selector BG33/BG36 utilizable en combate
- La preparación de práctica alterna el escenario con arriba/abajo y carga BG36/BG33 al entrar a la pelea. El autotest usa el mismo flujo, exige `battle_stage_selected_interactively=1`, luego recorre BG36 y BG33.
- Vita3K SDL pasó schema46/600 y `regression_gate=1`; BG36: 25 tiles, cuatro auxiliares y captura; BG33: 24 tiles y 12,570 draws. Auto VPK SHA-256 `f8bb7f2b939cf89cd4f2951bf5dd92a8524ecf06f2fc73ccfda1ea6f2975ef69`. Captura: [fight-bg36.bmp](../artifacts/screenshots/fight-bg36.bmp).
- La captura confirma el stage seleccionado, pero no paridad: el encuadre y las capas quedan mal distribuidos respecto al viewport. Falta cotejar el mismo frame/replay contra PC y ajustar origen/cámara/escala con evidencia. Global 27%; no se cuenta BG36 terminado. [ITERATION292.md](ITERATION292.md).

## Iteración 2.191: orden de composición BG36 corregido
- El renderer PE dibuja primero `clowd_l`/`clowd_s`, luego la retícula base `0x46f380` y después los torii. El render de combate Vita usa ahora cielo→nubes→tiles→torii.
- Auto VPK: 108,432 bytes, SHA-256 `983ef4d0b520b4dbbd613817da3718730f4254fd638d4211b8615e5b59659f7f`; Vita3K SDL pasó 600 frames, BG36 25 tiles y cuatro auxiliares, captura confirmada, hash coincidente. Interactivo: 108,266 bytes, SHA-256 `f9c74b09a3776adf4f5425b10cae7dbff8f8c7f087f180f6d2c1fecb25771542`. Ambos VPK pasan validación estructural sin errores ni advertencias.
- unittest BG36 3/3 y BG37/BG38 4/4; la captura pone nubes detrás de tiles y torii delante. Falta paridad con captura PC y selector/cámara completos; porcentaje permanece en 27%. [ITERATION291.md](ITERATION291.md).

## Iteración 2.190: cielo base BG36 reconstruido desde el PE
- El renderer dibuja el fondo de cielo BG36 con RGB base `(126,206,244)` antes de los tiles; el tono coincide con el fondo opaco del recurso `clowd_s`. El fondo BG10 sigue solo como fallback si no hay stage renderer.
- Auto VPK: 108,453 bytes, SHA-256 `defd5c0c651e3ec2cd98821f82ec385f4ead6de64353960d9059b6e638285fed`; Vita3K SDL pasó 600 frames, 25 tiles BG36, cuatro auxiliares y captura confirmada, hash coincidente. Interactivo: 108,287 bytes. Ambos VPK pasan verificación estructural sin errores/advertencias.
- unittest BG36 3/3 y BG37/BG38 4/4; el rectángulo de nube ahora se mezcla con el cielo en la captura. Parallax/tintes dinámicos y comparación PC pendientes; global permanece en 27%. [ITERATION290.md](ITERATION290.md).

## Iteración 2.189: BG36 ya no dibuja BG10 debajo
- El fondo BG10 ahora es fallback cuando no hay renderer BG33/BG36 listo; deja de aparecer bajo las capas transparentes del escenario activo.
- VPK auto nuevo: 108,536 bytes, SHA-256 `7815f2f78fd5d3183f15f581633accd957cd6d9962ca2c27fbe6b7d791045ebe`. Vita3K SDL fresco pasó 600 frames, `regression_gate=1`, BG36 25 tiles y cuatro auxiliares, captura confirmada; el hash del reporte coincide. Interactivo: 108,370 bytes.
- Contratos unittest: BG36 3/3 y BG37/BG38 4/4; `git diff --check` pasa. La nube conserva rectángulo azul y falta paridad visual con PC; el global sigue en 27%. Suite pytest global no ejecutada: falta pytest local y WSL denegó acceso. [ITERATION289.md](ITERATION289.md).

## Iteración 2.188: retícula base BG36 integrada y validada en Vita3K
- El código C calcula las 30 anclas PE de BG36 (x=700−256·col, y=946−256·fila), proyecta y dibuja los 25 tiles presentes; los cinco ausentes permanecen nulos. El gate de combate requiere 25/25 y máscara `0x1c7bffff` y captura fresca confirmada, además de cuatro auxiliares y su update.
- VPK autotest actual: 108,392 bytes, SHA-256 `DB2E73029E052F39B40F5DCA84B620AEC2CF0CB20043A328B69B7AD12F74E95D`. Suite Python 139/139 y contrato BG36 3/3 pasaron. Se generó también VPK interactivo de 108,226 bytes.
- Vita3K SDL fresco: 600 frames, `status=passed`, `regression_gate=1`, BG36 base 25/25 (máscara 477888511), auxiliares 4/4 y captura confirmada; hash del reporte coincide con el VPK. Captura muestra composición todavía incompleta y BG33 subyacente; avance global permanece 27%. [ITERATION288.md](ITERATION288.md).


## Iteración 2.187: auxiliares BG36 en combate
- La sonda automatizada de combate carga y dibuja `tori1`, `tori2`, `clowd_l` y `clowd_s` mediante los pivotes/proyección BG36 y actualiza el scroll. Exige máscara 15/15; el modo interactivo conserva BG33.
- VPK autotest: 107,875 bytes, SHA-256 `3f7c9fd18ee0cdfad841a78a490be87fa1646ff71f301710189511126ed97373`; Vita3K SDL schema46/600, `status=passed`, `regression_gate=1`. Interactivo: 107,709 bytes, SHA-256 `2564103721a330fce175fbe6c7ab4e87f33ccc7cde0cfd948332faf09a33b4c5`.
- Captura: [fight-bg36.bmp](../artifacts/screenshots/fight-bg36.bmp). Las auxiliares están sobredimensionadas; faltan escala/composición original y la matriz base, por lo que BG36 aún no es un escenario completo. Contrato focal BG36 3/3; suite completa 139/139. [ITERATION287.md](ITERATION287.md).

## Iteración 2.186: BG33 integrado a la escena de combate
- El combate carga los 24 tiles base BG33 en memoria separada del visor, avanza su contador original por tick y dibuja los 30 slots con la cámara activa.
- VPK autotest `artifacts/Touhou123Vita-current-auto.vpk`: 107,140 bytes, SHA-256 `fbd76df93d02e9aab172060ada0b7f9805ed1a8e4df6dbd658a7083ce636ccd5`; `check_vpk.py`: 0 errores/advertencias.
- Vita3K SDL: 600 frames, `status=passed`, `regression_gate=1`, 24 tiles, 420 updates, 12,600 draws, slots 30/30. Suite Python 139/139 y `git diff --check` pasan. Captura: [fight.bmp](../artifacts/screenshots/fight.bmp).
- Esto verifica la capa base de BG33 en la arena del prototipo, no el stage completo ni paridad global. Faltan sus auxiliares/mecánicas, integración jugable de los otros stages, rutas del roster y comparación visual por frame con PC. [ITERATION286.md](ITERATION286.md).

## Iteración 2.184: VPK instalables con LiveArea; Vita3K fresco pasa
- Se corrigió el pipeline: los VPK incluían eboot/assets pero no icono, fondo, startup ni template LiveArea. El generador local produce PNG indexados y el build los empaqueta.
- Autotest 106,680 bytes, SHA-256 `5c96965a2009caafcc061441899db3ffb449cbcca9e3c2b58b19190456d54613`; interactivo 106,514 bytes, SHA-256 `69d56fd332580c510fc71f661149d1c053c2464aea76649a503d6297d06bb82e`. Ambos pasan `check_vpk.py` con 0 errores/advertencias y comparten `eboot.bin` (`edeabed9bb5bcdcb09a851a54a86ba2a59fa6ba0bef2ac843f4ddb51fd2b90f6`).
- Vita3K SDL aislado corrió el auto VPK exacto: schema46, 600 frames, `status=passed`, `regression_gate=1`; reporte fresco [vita3k-result.json](../artifacts/vita3k-result.json), capturas en [screenshots](../artifacts/screenshots/). Suite Python 137/137 más prueba focal del generador 1/1. El interactivo comparte eboot pero no se corrió por separado. [ITERATION284.md](ITERATION284.md).

## Iteración 2.179: Namazu aparece en el final Story de Meiling
- Se inventariaron 15 stages en tres CSV del DAT: Cirno, Meiling y Sanae, cinco cada uno. El único rival Namazu está en Meiling stage 4, con cinco cartas/variante 3. El registro concreta dónde debe aparecer como rival; aún no se ha verificado el spawn en una partida ni su combate entero.
- La regresión valida las tres tablas y la fila única Namazu además de la conexión estática loader/factory. Sin runtime/VPK. [ITERATION279.md](ITERATION279.md).

## Iteración 2.178: carga de CSV Story para el roster principal
- `0x432bb0–0x43332f` recorre IDs 0–19 y arma `data/csv/<nombre>/story.csv`; `0x40f370` abre el recurso, el parser procesa filas y `0x43f440` consulta una cadena en el mapa global. Esto confirma que la tabla Meiling donde está la fila de Namazu participa en la carga Story, pero falta el stage activo y el enlace a `0x45ef50`/factory.
- Regresión ampliada para ruta, loader, conversión por mapa y límite del bucle. Test focalizado y `py_compile` pasan; sin runtime/VPK. [ITERATION278.md](ITERATION278.md).

## Iteración 2.177: Namazu es rival Story en la etapa 4 de Meiling
- El CSV extraído `data/csv/meirin/story.csv` asigna `Namazu` a stage 4 con cinco cartas/variante 3; el índice del `th123a.dat` contiene `data/csv/meirin/story.cv1`. SokuLib mapea Namazu al ID 21, igual que el factory PE. Prueba el uso como rival/jefe Story, pero no su elegibilidad en roster normal ni el enlace dinámico completo con caller/factory.
- Se añadió `tests/test_story_namazu_source.py`. Usa la extracción local CP932 y valida su ruta en índice/manifiesto; `shady-cli` no permitió repetir extracción limpia en esta sesión, por lo que no se afirma verificar el payload decodificado. La regresión también comprueba el orden PE lookup→store→factory bajo la condición `EBX >= 3`, y las referencias `data/csv/`/`/story.csv`. Sin runtime/VPK. Los otros callers `0x481c3d/e` preparan claves `win`/`lose`; la relación exacta con el CSV de etapa sigue sin probarse. Siguiente: trazar la instancia Story de Namazu, sus recursos y loop de combate. [ITERATION277.md](ITERATION277.md).

## Iteración 2.176: el productor Story consulta los datos CSV
- `0x43f440` busca una clave en la tabla CSV; el caller `0x45ef50` copia su resultado a `PlayerInfo.character` y solicita el slot 3 en `0x45f176`. El PE referencia `data/csv/story.csv`; esto acota el origen potencial de ID 21, pero todavía no prueba que un registro contenga 21 ni que Namazu sea seleccionable normalmente.
- Se registraron los callers, referencias de rutas y la escritura del campo. Solo análisis estático; sin cambio runtime/VPK. Siguiente: inspeccionar los CSV originales para identificar fila, evento y ciclo de vida de Namazu. [ITERATION276.md](ITERATION276.md).

## Iteración 2.175: desbloqueos persistentes limitados a 20 personajes
- `SaveDataManager::enableCharacter` (`0x42ee80`) compara el ID con 20 y solo escribe `enabledCharacters[id]` para IDs 0..19; el factory llama al helper tras crear el Player. SokuLib enumera Random=20 y Namazu=21, y modela el array persistente con longitud 20.
- Esto distingue un ID construible de un luchador dentro del roster guardado, y apoya tratar Namazu como ruta especial hasta identificar su productor. No prueba que no exista un acceso oculto alternativo. Regresión individual pasa, sin runtime/VPK. [ITERATION275.md](ITERATION275.md).

## Iteración 2.174: cola de creación y factory común de Player
- `GameDataManager::createQueue` (`List<pair<int,PlayerInfo*>>`) alimenta el factory `0x46da40`: helper `0x46ead0` puede crearlo síncrono o encolar; worker `0x46e6e0` drena la lista mediante `0x46e5c0`; el factory guarda cada Player en el arreglo `players[4]` (`+0x28`). Su dispatch de ID 21 llega a PlayerNamazu.
- Se fijó ese enlace y el layout local en una nueva regresión; las seis pruebas focalizadas pasan. Los callers `0x4386e6`, `0x45f176`, `0x47fce0/f3` y `0x4818d4/e7` todavía no revelan qué fuente configura Namazu ni el modo correspondiente. Sin runtime/VPK. [ITERATION274.md](ITERATION274.md).

## Iteración 2.173: writer del timer localizado en la clase Namazu
- El barrido PE de `.text` localiza un décimo writer que carga `+0x884/+0x886=300` en `0x7d47b2`. Slot10 del vtable `0x85f824` y RTTI `.?AVNamazu@@` lo identifican fuera del manifest del roster. La entrada 21 (`0x15`) de la jump table central llega al caso que reserva `0x8a0` bytes y llama al constructor Namazu en `0x46de1c`; no se ha localizado aún quién solicita ese índice ni si está en la selección normal.
- SokuLib también define `CHARACTER_NAMAZU=21`, `PlayerNamazu` y `GameObjectList_Namazu`; los DAT extraídos ya aportan 179 imágenes, 731 bloques y 3,276 poses PAT de `namazu`. Esto confirma soporte de clase/recursos, pero falta probar alcanzabilidad en modo normal y portar su comportamiento completo.
- Su ruta exige `+0x7cc==2`, mano/carta 0, mapping de IDs 0..15 a un único caso y expira hacia factory de acción 1201 si HP sigue positivo. Escáner/reporte y regresión cubren la evidencia; pruebas focalizadas 5/5. Sin cambio runtime/VPK. [ITERATION273.md](ITERATION273.md).

## Iteración 2.172: selector de input 2 asociado al lado derecho
- `0x43dec0` configura `PlayerInfo` izquierdo (`0x899d10`) con `isRight=0`, selector `+6=1`, y el derecho (`0x899d30`) con `isRight=1`, selector `+6=2`. El campo `+6` es distinto del flag de lado `+4` y llega a `Player+0x7cc`, que el dispatcher `0x46d7d0` usa para elegir la ruta virtual de input.
- Los callsites `0x42626c` y `0x44c2b1` prueban usos de la inicialización, pero no justifican generalizar ese enum a todos los modos. Regresión PE añadida; pruebas focalizadas 5/5. Sigue faltando alcanzar el timer de 300 de forma natural y resolver el productor de Suika/action96. [ITERATION272.md](ITERATION272.md).

## Iteración 2.171: expiración del timer enlazada con acción común Spell Break
- En Reimu, el caso con `+0x884=300` también inicializa `+0x886=300`. En el expiry limpia timers/campos auxiliares y, si HP sigue positivo, invoca `0x46eb30` para crear acción `0x4b1` (1201).
- La acción 1201 del `common.pat` contiene `spellBreakGage`, `spellBreakBar` y poses `breakGage000..010`; enlaza el spawn con recursos nombrados Spell Break, pero aún falta confirmar su presentación natural.
- Corrección: `+0x7cc` se copia de `PlayerInfo+6` junto al puntero `KeyManager` y `0x46d7d0` lo usa para elegir una ruta virtual de input. Iteración 2.172 vincula el valor 2 al lado derecho en una inicialización concreta; no es un “modo Spell Break”. El update consulta esa etiqueta y la carta al frente, sin prueba aún de que una activación de carta cause el timer.
- Cuatro pruebas PE/PAT pasan, incluida ejecución Unicorn del expiry desde `+0x884=1` hasta el factory 1201 con HP intacto y timers en cero. El estado es forzado; no se modificó/recompiló VPK. Falta captura natural y productor de Suika. [ITERATION271.md](ITERATION271.md).

## Iteración 2.170: nueve updates de personaje asignan 300 a `+0x884`
- Al seguir los destinos de jump tables omitidos por el CFG directo, aparecen stores positivos en slot10 de Reimu, Marisa, Alice, Patchouli, Cirno, Meiling, Sanae, Suwako y Utsuho. Todos asignan `0x12c`; el flujo común decrementa/limpia el timer. Las rutas consultan `Player+0x5e8` (deque de la mano), pero falta fijar el índice/efecto de carta que activa cada caso.
- Suika no tiene store positivo directo en su slot10; `+0x884` lo consulta el callback 97→96 y se encontró un helper que solo lo limpia. Estas otras clases aún no explican el productor natural de Suika. [ITERATION270.md](ITERATION270.md).
- El hallazgo quedó reproducible en `tools/scan_player_field_884.py` y `artifacts/player-field-884-jumptable-cases.json`; test focal valida vtables, tablas y stores.
- Las nueve rutas examinan tipo de input `Player+0x7cc==2`, mano no vacía y `Card.id` del elemento 0 vía `0x456c80`. `common/spellcard.csv` confirma IDs tipo 0 de sistema `0..20`; los rangos por personaje son subconjuntos y todos mapean al mismo caso que carga 300. El enum de input se copia en el constructor y se despacha en `0x46d7d0`; falta nombrar el tipo 2 y observar el timer en gameplay. El escáner/reporte/test fijan guards, índice, mapping y hash del CSV.

## Iteración 2.169: action96 sigue 1.200 ticks con InfoManager HUD aislado
- `0x8985e8` es `InfoManagerBase::instance`; constructor PE `0x47eaf0`, vtable `0x85b530`, callback +0x18 `0x47eb70` lee gauges/diseños. Un shim limitado al refresco HUD evita incluir recursos de UI en este harness y registra las tres llamadas originales del timer.
- Corregido conflicto de dirección entre shim y stub de suelo. Timer/update PE completan 1.200 ticks de action96 sin fetch inválido; action sigue en 96, `+0x884` no cambia. Entrada a 96 sigue forzada y no se reproduce el manager de round. [ITERATION269.md](ITERATION269.md).
- Referencias de otras clases muestran consumidores del mismo campo en Alice slot10 (`0x5100b0`) y Suwako slot10 (`0x765ab0`): decrementan/limpian `+0x884`; ningún escritor positivo directo encontrado. Falta ampliar rastreo a escrituras calculadas y estado compartido del round.

## Iteración 2.168: fetch de action96 atribuido a callback global del timer
- Los 181 updates PE válidos de action96 retornan al sentinel correcto; el fetch nulo del tick 182 ocurre dentro de `0x46a330` → `0x463b69`, donde se llama `object+0x18` del singleton `0x8985e8`, todavía ausente del harness. No indica corrupción del stack ni terminal/bloqueo de action96.
- Siguiente: encontrar e inicializar ese manager/callback en el harness y seguir el camino real de recuperación. Probe y test actualizados; runtime/VPK sin cambios. [ITERATION268.md](ITERATION268.md).

## Iteración 2.167: action96 PE recorre 181 actualizaciones válidas sin salir
- Con Player construido, setter96, timer, handleInputs neutral y updater PE, action96 permanece activo en 181 ticks completados; `setSequence(3)` llega desde `0x4851e7`, el frame pointer sigue en los 10 frames originales y `+0x884` no se escribe.
- En el siguiente tick el harness detiene un fetch de baja dirección al retornar de la ruta común. Manager/round caller y stack externo siguen incompletos; no se infiere que el juego real termine o se bloquee. Test del probe ya fija esos límites. Sin cambio Vita/VPK. [ITERATION267.md](ITERATION267.md), [reporte x86](../artifacts/x86-suika-constructed-handler.json).

## Iteración 2.166: autociclo singleton de PAT96 coincide con loader original
- `FUN_004679e0` (cargador `data/character/%s/%s.pat`) inicializa el primer nodo en `0x467df2–0x467df9` con `next=0` y `prev=self`. Action96 de Suika tiene un único nodo seq0 de diez frames; por tanto seq1/3 siguen usando ese mismo frame range en el juego original y en el fixture.
- Corrige Iteración 2.165: no es un alias gráfico inventado por la fixture. El trigger natural de action96 y la semántica/final de la secuencia aún necesitan combate/manager real. Tres tests focalizados pasan, incluyendo bytes PE y construcción del singleton. [ITERATION266.md](ITERATION266.md).

## Iteración 2.165: alias gráfico action96 causado por autociclo de fixture
- `0x4652a0` sigue el enlace de secuencia `+0x1c` tantas veces como indica el índice. La fixture action96 tiene un solo nodo de 10 frames con prev/next apuntando al mismo nodo; por eso seq3 conserva el ID 3 pero carga el payload de seq0. Los índices son PE, el alias visual es fixture.
- No inferir la animación original de levantamiento desde esa ruta; falta recuperar enlaces que construye el loader PAT o confirmar su lógica para action96. Testa el dispatch y autociclo: 2/2. [ITERATION265.md](ITERATION265.md).

## Iteración 2.164: action96 comparte el update de derribo con action97
- Resolución de tablas PE confirma que `0x483f40` enruta 96 y 97 al mismo handler `0x485115`; action98 va a `0x4852a0`. El callback de cambio de acción usa otra tabla: 96→default `0x48be20`, 97→consumer `0x48b85f`, 98→`0x48b8f6`.
- En el probe PE action96 llega a sequence1 en tick30 y su handler solicita sequence3 en tick31 (`0x4851e7`). El PAT efectivo de action96 solo aporta diez frames de seq0, así que las secuencias siguientes siguen sin fixture gráfica fiel. Esto vincula 96 con la familia update de caída/recuperación, pero no demuestra el productor natural de `+0x884` ni el rol gameplay exacto. Test de dispatch añadido; [ITERATION264.md](ITERATION264.md).

## Iteración 2.163: `+0x884` en call graph Suika solo se limpia
- El escaneo interprocedural cubre 25 entradas ejecutables del vtable, 392 funciones y 29,963 instrucciones; encuentra una referencia: slot17 `0x608670→0x48b000→0x48b15a`, donde `xor eax,eax` precede a la escritura. Es reset a cero, no el productor positivo que activa action96.
- Añadí el escáner reutilizable y un test que fija hash, referencia/cadena y límite de cobertura. JSON: [suika-field-884-callgraph.json](../artifacts/suika-field-884-callgraph.json). Falta resolver managers, tablas/saltos y llamadas indirectas. Sin cambio Vita/VPK. [ITERATION263.md](ITERATION263.md).

## Iteración 2.162: scan CFG de métodos Suika y probe PAT de action96
- CFG básico desde 48 punteros del vtable Suika, siguiendo ramas directas y sin cruzar calls, no halló referencias a `+0x884`; tampoco en métodos slot 10/15/20. Dispatch indirectos, helpers compartidos y manager siguen fuera de cobertura.
- La acción PAT96 tiene diez frames en seq0; setter/update PE la ejecutan. En 60 ticks la fixture entra en secuencias 1/3 no presentes en el PAT efectivo extraído, por lo que esto confirma ejecutabilidad parcial, no levantamiento natural ni animación completa. No portar todavía. [ITERATION262.md](ITERATION262.md).

## Iteración 2.161: referencia `+0x884` clasificada como Reimu, no Suika
- El bloque `0x490795` escribe `Player+0x884/+0x886`, pero la función ancla `0x490490` corresponde a Reimu: manifest Ghidra `vtable 0x85bf4c`, slot 10. El slot 10 de Suika es `0x5ee620`; se descarta esa referencia como productor de Suika.
- El escaneo lineal no basta para escribir conclusiones porque no sigue las tablas de saltos. Aún faltan los escritores dinámicos de Suika/manager y el significado de action96; siguiente: revisar `0x5ee620` y la ruta real del manager, luego ampliar la captura a más reacciones. Sin runtime/VPK nuevo. [ITERATION261.md](ITERATION261.md).

## Herramienta evaluada: psp2-tooling (confirmación, 18 octubre 2026)
- Sí sirve, pero para validar y perfilar una **Vita física** después de integrar una escena de combate: USB/host0, lanzar VPK, entrada, capturas HDMI, dumps y perfiles CPU/GPU. El host es Linux y no participa en la decompilación x86, compilación VPK ni Vita3K.
- Próximo paso actual sin cambios: continuar el productor de `Player+0x884` y las rutas faltantes del combate; mantener la regresión Vita3K. Retomar `devkit/` cuando haya host Linux, hardware y escena estable. `retail-cp` exige revisar PCH-2000/FW 3.65/Ensō/taiHEN y módulos DevKit externos antes de plantearlo.
- Confirmado con el [README upstream](https://github.com/Grarak/psp2-tooling) y registrado en [ROADMAP.md](ROADMAP.md) y [ANALYSIS_AND_TESTING_TOOLING.md](ANALYSIS_AND_TESTING_TOOLING.md).

## Iteración 2.160: `+0x884` se consume al entrar en action97
- Hook de escritura instalado desde antes del resolver: cero escrituras PE a `Player+0x884` durante la reacción/300 ticks. Ocho botones/abajo+botón sostenidos 24 ticks tampoco lo cambian ni salen de action97.
- Si la fixture fuerza `+0x884=1` justo antes del aterrizaje, el PE hace `74→97→96` en el callback (`0x4846a7`, `0x48b8ef`). No identifica el productor natural ni demuestra que action96 sea levantamiento; el valor se consume en la entrada, no como timer observado. [ITERATION260.md](ITERATION260.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

## Iteración 2.159: handler gameplay 97 tiene salida condicional a action96
- `0x6086a0` despacha action97 a `0x48b85f`; este compara `Player+0x884` y pide action96 en `0x48b8e4` si el valor es positivo. El significado de action96 y el productor de `+0x884` siguen desconocidos.
- En la fixture, `+0x884=0` durante 300 ticks y diez entradas de un tick; no entra a la rama. Esto acota, no confirma, la hipótesis de transición gestionada fuera del Player. Próximo: identificar escrituras dinámicas a `+0x884` en una secuencia natural. [ITERATION259.md](ITERATION259.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

## Iteración 2.158: transición de aterrizaje action74→97 trazada
- En tick10 input neutral conserva action74. El dispatcher `0x483f40` entra al handler 74 (`0x4849f6`); gate PE de suelo `0x487ea0` retorna verdadero y el bloque `0x4847d4→0x484807→0x484696` solicita action97 (`0x4846a5/return 0x4846a7`). Luego `0x6086a0` actualiza action97.
- La caída no depende del input neutral ni del round manager; el piso sigue controlado por harness. Falta localizar el caller/estado que sale del PAT circular de action97. [ITERATION258.md](ITERATION258.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

## Iteración 2.157: grafo PAT de action97 no tiene secuencia terminal
- El PAT efectivo en memoria forma el anillo `0→1→2→3→0`; enlaces previos `[3,0,1,2]`, modos de frame `[0,0,1,0]`. Solo seq.2 repite su frame.
- `0x464bf0` informa terminal solo para nodo sin `prev` (`+0x18=0`); ninguno del anillo lo cumple. El avance local de action97 no basta para action98, incluso alterando el loop bit. Un barrido de literal `push 0x62` halló solo la solicitud del handler 97; setters con argumentos calculados no quedan descartados. Falta identificar el estado/callback externo del manager de combate que provoca la recuperación natural. [ITERATION257.md](ITERATION257.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

## Iteración 2.156: condición terminal de action97→98 acotada
- El dispatcher x86 de action97 consulta `0x438c60`; si la animación/secuencia devuelve terminal, el handler pide action98 desde `0x4851f9`. En Suika, callbacks `0x464b70` y `0x464bf0` dependen del wrap de pose/bit loop y del enlace previo del nodo PAT (`+0x18`).
- Se amplió el diagnóstico artificial de apagar el loop del seq.2 a 120 ticks: contador 23, nodos PAT 0/1/2/3 recorridos y action97 sin setter de acción. Esto no prueba la recuperación natural; indica que falta reconstruir el grafo efectivo y el contexto externo de combate. La corrida principal de 300 ticks no se alteró.
- Sonda actualizada y reporte fresco; sin cambios al runtime Vita ni VPK. [ITERATION256.md](ITERATION256.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

## Iteración 2.155: loop de derribo medido durante 300 ticks
- El temporizador y update PE, tras reacción 74, pasan a action97 y recorren PAT `0→1→3→0→1→2`; tick43 entra en seq.2 loop mode 1. `handleInputs` neutral no pide setters nuevos y completa 300 ticks en action97/seq.2, Y=500/vy=0. Action97 enruta a `0x485115`; la rama de aterrizaje pide `setSequence(3)` desde `0x4851e7` en tick17. La iteración 2.156 amplía el diagnóstico artificial de cambiar el loop bit a 120 ticks: action97 persiste. [ITERATION255.md](ITERATION255.md), [reporte](../artifacts/x86-suika-constructed-handler.json).
- Suite focal x86 7/7 y py_compile/diff-check pasan. Sin cambio a runtime Vita/VPK.

## Iteración 2.154: hitstun/reacción 74 con traits PAT completos
- Se corrigió `_prepare_pat_actions`: ya copia los 40 bytes `combat_traits` antes de normalizar damage/stun/flags. Sin ese payload, `CharacterFrameData+0x26` quedaba 0 aunque el PAT declara 100.
- Con action 418/seq.2/pose0 y defensor construido por PlayerSuika en action400, el resolver PE aplica 1200 (PAT900+trait100), HP fixture 2000→800 y selecciona reacción action74/seq0. Resolver completo, sin accesos inválidos.
- `0x46a330` consume el hitstop PE de 10 a 0; luego el update solicita action97. La iteración 2.155 amplía a 300 ticks: `+0x13e` es contador, `+0x15c` demuestra seq.2 (loop mode 1) desde tick43 hasta tick300. Y llega al suelo controlado 500. Se demuestra la caída y persistencia del loop bajo el par timer/update; falta integrar manager/callback de round para observar levantamiento/fin de recuperación.
- Pruebas Suika 3/3 fijan daño/reacción y timeline parcial. Efectos/round manager y suelo siguen controlados; HP2000 es fixture no letal. Corrige y supersede la iteración 2.153. [ITERATION254.md](ITERATION254.md), [reporte](../artifacts/x86-suika-constructed-handler.json).
- Próximo: integrar stage/fight/input managers, averiguar cómo sale acción97 del PAT seq.2 loop con replay normal y validar levantamiento/KO.

## Iteración 2.153: resolver PE aplica 900 de daño en flujo Suika 200→418
- Registro histórico supersedido: faltaba `combat_traits` crudo en el harness; no representa el daño/reacción correctos. Ver [ITERATION254.md](ITERATION254.md).
- Próximo: sustituir estado sintético del defensor por constructor completo + contexto de round y continuar reacción/stun en frames posteriores.

## Iteración 2.152: geometría de ataque 418 confirma contacto PE
- El flujo C+NRNR→418 y 16 updates originales alcanza seq.2/pose.0, daño PAT 900; el helper PE `0x47a5b0` confirma overlap 1/1. [ITERATION252.md](ITERATION252.md).

## Iteración 2.151: dash Suika 200→418 avanza hasta frame ofensivo
- En el mismo Player PE, el flujo C+NRNR llega a action 418; cleanup original más 16 updates virtuales de Suika avanzan seq.0→seq.1→seq.2 sin error. Tick 16 es seq.2/pose.0, daño PAT 900 y una caja ofensiva.
- Prueba focalizada 1/1; refresco de input, suelo/escenario/callbacks controlados. Sin runtime Vita/VPK. [ITERATION251.md](ITERATION251.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

## Iteración 2.150: origen del gate C y cadena de dispatch Suika 418
- `0x46d73e` deriva `Player+0x784` de `Player+0x764 == 1` (botón C). El input update/matcher originales sobre el ring del Player construido y el handler llegan desde action 200 a setter 418.
- Se verificó el productor del guard; refresco físico, servicios de suelo/escenario y caller completo siguen controlados. No cambia runtime Vita/VPK. [ITERATION250.md](ITERATION250.md), [INPUT_STATE.md](INPUT_STATE.md).

## Iteración 2.149: PlayerSuika construido y action 418 seleccionado por el handler
- El PE construye PlayerSuika con `0x609d40`, expone vtable `0x85da84` y crea su manager. El setter original `0x464930` inicia action 200 con PAT local; `handleInputs 0x609dc0` se ejecuta hasta `0x60be83`, llama setter original 418 y llega a `0x46cac0`.
- KeyInput, `Player+0x784=1`, suelo/stage y servicios de plataforma siguen controlados. El matcher/deque construido no está conectado a esta instancia; cleanup body se verifica por la sonda separada. Cinco pruebas focalizadas pasan; no cambia Vita/VPK. [ITERATION249.md](ITERATION249.md), [evidencia](../artifacts/x86-suika-constructed-handler.json).
- Próximo: usar el PlayerInfo/deque del constructor para input update/matcher y después seguir acción/PAT con rival, colisión y replay.

## Iteración 2.148: handler de Suika desde prólogo alcanza acción 418
- Se corrigió la condición anterior: `handleInputs` carga `BX=0xc8`; 418 sale de acción actual 200 (dash), no 300. Las notas 2.145–2.147 se corrigieron para reflejarlo.
- La ejecución PE encadena updates `0x46d5d0`, matcher `0x487020` y handler completo `0x609dc0` hasta la rama `0x60be83`. Con `[1,0]` producido y estado 200/facing derecha sembrado, registra solicitud setter 418 y alcanza `0x46cac0`. Servicios de estado/recurso/suelo y el cuerpo del setter son controlados; el cuerpo del limpiador tiene sonda separada. Pruebas focalizadas 6/6. Sin cambio Vita/VPK. [ITERATION248.md](ITERATION248.md), [evidencia](../artifacts/x86-suika-input-matcher.json).
- Próximo: sustituir campos/servicios sintéticos con Player/PlayerInfo del constructor original, ejecutar setter/update PAT y enlazar oponente, colisión y replay. NRNR no dispara 418 directamente; el handler lee KeyInput actual.

## Iteración 2.147: input PE y rama de Suika (corregida)
- La secuencia NRNR mantiene validez como evidencia del matcher, pero el salto a bloque interno tenía mal la acción previa (usó 300). No demuestra la transición 418; ver corrección y ejecución desde prólogo en [ITERATION248.md](ITERATION248.md).

## Iteración 2.146: rama 418 del handler Suika verificada en el PE
- El código original `0x609dc0` ejecuta desde `0x60be34` hasta la rama `0x60be83`, solicita 418 por setter virtual y llama al limpiador original `0x46cac0`, que vacía buffered KeyInput.
- Seis casos cubren dash frontal/action 300, suelo, eje vertical y dirección; también se comprobó que esta rama no consulta move-lock. La fixture empieza dentro del handler y controla suelo/setter; dispatch completo, polling real y update PAT/colisión quedan pendientes. Sin cambio Vita/VPK. [ITERATION246.md](ITERATION246.md), [reporte](../artifacts/x86-suika-418-handler-branch.json).
- Próximo: hacer entrar al handler desde su prólogo con estado de jugador consistente, enlazar el ring/matcher con KeyInput y después continuar por setter, PAT y combate contrastado con replay.

## Iteración 2.145: matcher PE detecta NRNR tras cuatro updates consecutivos
- Deque ABI correcto: mapa 16 slots, 12 bloques de 8 words, size 90. Cuatro `0x46d5d0` más el matcher original `0x487020` procesan N,R,N,R como muestras `0,2,0,2`; NRNR (`Player+0x7c4 & 1`) aparece solo en el cuarto tick y size se conserva en 90.
- Refresco físico de controles aislado; input update, append circular y matcher sí ejecutan desde el PE. Corrección de atribución: `0x4b0ac2` pertenece al handler de Reimu, por lo que sus ocho guards no cuentan como validación de Suika. La rama Suika 418 se localizó en `0x609dc0:0x60be83→0x60b721`; usa acción 300, estado de suelo, KeyInput horizontal/facing y vertical actual neutral; ese bloque no consulta move-lock. Pruebas focalizadas originales, 4/4. Sin cambio Vita/VPK. [ITERATION245.md](ITERATION245.md), [traza](../artifacts/x86-suika-input-matcher.json), [guard Reimu](../artifacts/x86-suika-418-producer.json).
- Próximo: ejecutar la rama Suika bajo contexto reproducible, observar setter y limpiador y correlacionar con input/update PAT; luego validar dispositivo/replay y ampliar a todos los personajes y escenarios.

## Iteración 2.144: input update x86 encadenado con guard 418
- `0x46c8e0/0x46d5d0` ejecutados sobre KeymapManager sintético: horizontal=1 genera KeyInput actual `[1,0]`/sample `0x02`; horizontal=1+A genera buffered `[1,0]`, timer 9/sample `0x12`. Ambas salidas pasan el bloque original `0x4b0ac2` y llegan a la solicitud 418; `0x46cac0` limpia el buffered.
- Diez casos dinámicos pasan. Refresco físico, matcher ring slot, grounded/move-lock y setter permanecen aislados; no es loop natural de Suika ni combate/replay. Sin cambio Vita/VPK. [ITERATION244.md](ITERATION244.md), [reporte](../artifacts/x86-suika-418-producer.json).
- Próximo: correr `0x487020` sobre el ring original e integrar slots Suika y update PAT.

## Iteración 2.143: productor condicional PE de acción 418 localizado
- Ruta `0x4b0ac2` ejecutada bajo Unicorn: solicita 418 con horizontal actual o buffered hacia facing y eje vertical actual neutral; ocho casos confirman los guards. `+0x778` no es requisito. El limpiador PE `0x46cac0` borra bufferedKeyInput tras setAction.
- Los guards de suelo, move-lock y setAction se aislaron; no se ejecuta el loop KeyManager ni se confirmó la implementación virtual concreta de Suika. Fixture de aterrizaje sigue con suelo controlado/Y fija; sin cambio runtime/VPK. [ITERATION243.md](ITERATION243.md), [caller](../artifacts/x86-suika-418-producer.json).
- Próximo: ejecutar actualización de input que escribe los dos KeyInput, enlazarla con esta ruta y seguir el timeline.

## Iteración 2.142: el gate PE de aterrizaje explica Suika 418 seq2→seq5
- `0x487ea0` compara Y con el helper de suelo, exige velocidad vertical no positiva y bandera `Player+0x4c4` despejada. En tick27 retorna verdadero a `0x5f4a5d`; el caller llega a `0x603644` y el setter solicita seq5. La fixture observó `vy=-0.5`; tick26 aún tenía `vy=0.0`.
- Probe y artefacto ahora guardan observaciones del gate; regresión focalizada pasa y Python completa 119/119. Y sigue fijada a cero y la acción se inyecta; es evidencia de transición condicional, no de dash/salto natural. Sin cambio Vita/VPK.
- Siguiente: ejecutar cruce de suelo desde posición/física natural y hallar productor input de acción 418. [ITERATION242.md](ITERATION242.md), [reporte](../artifacts/x86-suika-418-sequence.json).

## Iteración 2.141: setter/update PE de Suika 418 llega a la hitbox de secuencia 2
- La fixture de `x86_suwako_808_factory_probe.py` usa secuencias efectivas del PAT; retiene el conteo de definiciones crudas para Alice 849.
- Nuevo probe con PE y PAT fijados: setter de acción 418 inicia seq0; el update llega a seq1 en tick8 y a seq2/pose0 en tick16 (daño 900, una hitbox), permanece activo hasta tick26 y salta a seq5 en tick27. Falta comprender ese branch; la secuencia 6 observada después no se interpreta aún como índice PAT.
- Suite Python 119/119, focalizada 11/11. No cambia motor Vita/VPK; acción 418 se inyecta directamente, sin input natural ni rival. Evidencia: [ITERATION241.md](ITERATION241.md), [reporte](../artifacts/x86-suika-418-sequence.json).

## Iteración 2.140: extractor PAT ofrece vista efectiva para sondas de combate
- `action_sequence_metadata(..., effective=True)` aplica la semántica del decoder C cuando una acción PAT se redefine; la vista cruda sigue disponible y es el default de los inventarios. El probe de parejas x86 solicita explícitamente la vista efectiva.
- En `th123c.dat`, Suika 418 es 12 registros crudos/6 efectivos (ventana ofensiva index 2, frames 0–7); Udonge 6/6 (index 1, frames 0–2); Utsuho 4/4 (index 1, frames 0,1,6,7,8). Hashes: [resumen](../artifacts/pat-action-418-effective-summary.json).
- Pruebas focalizadas 17/17; suite Python 118/118. No cambia el motor/VPK. La selección de índice por el PE y la causa de los no impactos siguen pendientes. Ver [ITERATION240.md](ITERATION240.md).

## Iteración 2.139: reconstrucción actual y gate Vita3K repetido
- Se añadió `-BuildDirectory` al script de build Vita nativo para controlar la ubicación de intermedios. VPK fresco: `artifacts/Touhou123Vita-continuation-auto.vpk`, 104,294 bytes, SHA-256 `6ae6e39959e63e486668126c5960848a5170a4de9a9d13146df0a584aaeb688f`.
- También se compiló el VPK interactivo `artifacts/Touhou123Vita-continuation.vpk` (104,128 bytes, SHA-256 `ab013afd5547b3b8a648256cdd6883630f4daa787ea2389a91dc72f5afad3792`); ambos contienen idéntico `eboot.bin` (SHA-256 `edeabed9bb5bcdcb09a851a54a86ba2a59fa6ba0bef2ac843f4ddb51fd2b90f6`).
- Vita3K local aislado/SDL pasó schema46/600 con evidencia fresca y gates Suika 623B/623C, objetos, crop PAT, cámaras y escenas BG33/BG36/BG37/BG38. Reporte: [vita3k-result.json](../artifacts/vita3k-result.json); corrida y cobertura: [ITERATION239.md](ITERATION239.md).
- Python: 117/117. CTest host no ejecutado porque su cache apunta a WSL y `cmake` no está en PATH Windows. La compilación ARM sí recompiló las fuentes. Sin prueba en hardware ni afirmación de paridad total.

## Iteración 2.138: sincronización Story condicional; replay revalidado
- El `.rep` local y PE 2009 coinciden con los hashes registrados. Probes frescos recorrieron las 16,910 parejas Story y los 33,820 words del método `0x481040`; layout de 3 registros y vectores 20/3, 20/3, 20/4 confirmado.
- Corrección de análisis: `0x4600fe` compara el word contra `[0x85eb58]`; mismatch retorna sin consumir, igualdad consume. No es espera activa. Pruebas replay 3/3 y dispatch 1/1 (9 contratos PE). La frecuencia de invocación por frame y playback en vivo siguen abiertos. Evidencia: [ITERATION238.md](ITERATION238.md). Sin cambio de runtime/VPK.

## Iteración 2.137: barrido geométrico PE de Udonge 418
- El probe x86 ahora acepta posiciones/facing y barrido reproducible. Con atacante X=320/facing +1 y defensor facing -1, Udonge 418:1/pose0 vs 400:0/pose0 conecta en X=320–450; X=318 y 460 no conectan. Al invertir facing, X=320 conecta y X=322 no: la caja PAT no se refleja como un intervalo simétrico. Transformadores y hit-vs-hurt del PE se ejecutan en la fixture.
- Regresión focalizada 5/5. Es una pose estática con cámara/escenario y datos de combate controlados; no equivale a combate/replay ni permite ajustar directamente Vita. Evidencia: [ITERATION237.md](ITERATION237.md) y `artifacts/kernel/x86-udonge-418-position-sweep.json`. Sin VPK nuevo (runtime sin cambio).

## Iteración 2.136: Udonge 418:1 y transform de ataque original; fixture Vita sin cruce simultáneo
- El diagnóstico Vita marca intersección horizontal y vertical por separado, pero no simultánea, incluso barriendo 0–8 cuadros de dash. B natural sigue 18/20 y C 17/20. El oracle x86 ejecuta `0x4640b0` para las cajas de ataque, confirma contacto y aplicación de daño de Udonge 418:1; la hurtbox defensora sigue controlada y falta `0x464200`, por lo que no acredita alcance natural.
- Python focalizado 4/4; Vita3K SDL schema46/600 pasó. El resolver aún termina en `0x0` tras el daño. VPK/evidencia y siguientes pasos: [ITERATION236.md](ITERATION236.md).

## Iteración 2.135: métrica de contacto C limitada a ventanas PAT activas
- La sonda ya no cuenta solapamientos en poses sin daño. Vita3K SDL schema46/600 pasó; Reimu 418 conecta 900 y los C naturales de Suika/Udonge/Utsuho siguen pendientes. Sus ventanas llegan a 20 unidades de separación central y hay contacto vertical en alguna pose, pero aún no intersección completa registrada.
- VPK y datos: [ITERATION235.md](ITERATION235.md), [roster-bc-natural.tsv](../artifacts/roster-bc-natural.tsv). Siguiente: medir las brechas horizontales de las cajas en el mismo cuadro y cotejar facing/movimiento con x86 antes de tocar el resolver.

## Iteración 2.134: Udonge B 409 conecta; diagnóstico guarda acciones/variantes
- El sondeo muestra que Udonge alcanzaba 408/409/418 pero 409:0 carece de hitbox; runtime selecciona provisionalmente 409:1. Udonge conecta 400 en frame12/gap28; Tenshi y Cirno también conectan B por 409:1. B natural 18/20, C normal 17/20.
- Runner exige la regresión Udonge y pasó Vita3K SDL schema46/600. Paquetes y límites: [ITERATION234.md](ITERATION234.md). La variante seleccionada aún debe cotejarse con el selector original x86.

## Iteración 2.133: cobertura natural B/C del roster y comandos especiales
- La sonda evalúa 3 separaciones por ruta y registra gap/origen del impacto. Cobertura observada B normal 15/20, C normal 17/20; Alice conecta B/C por PAT 849. Se inventarían aparte las tres ramas de Suika 623C (521/1000, 526/500, 531/800) y el runner las exige.
- Vita3K SDL pasó schema46/600 con la regresión Remilia 2C. VPK y diagnóstico: [ITERATION233.md](ITERATION233.md), [roster-bc-natural.tsv](../artifacts/roster-bc-natural.tsv). Sin impacto B observado: Reimu, Remilia, Udonge, Tenshi, Cirno; C normal: Suika, Udonge, Utsuho.

## Iteración 2.132: contrato de vida/reacción Suika 623B
- PAT 821/acción 530 aplica el impacto una sola vez en el spawn, se elimina en el siguiente tick y conserva reacción terrestre 50/timer20. Vita3K SDL schema46/600 valida el contrato nuevo en la máscara route127, más las regresiones actuales.
- VPK interactivo/autotest, hashes y alcance: [ITERATION232.md](ITERATION232.md). WSL devolvió `E_ACCESSDENIED`; no se recompiló `fight_tests` host. El ARM compila y la build autotest corre en Vita3K.

## Iteración 2.131: Suika 623B nivel 9 crea y conecta PAT 821
- La acción 530 crea el objeto `0x335`→PAT 821 al llegar a pose 7 (update 20); se portaron MT19937, el spawn y la caja PAT de 800 de daño. Vita3K valida una instancia, impacto de 800 y coordenadas x86-matched; suite Python 115/115 y C 10/10.
- Hashes y cobertura: [ITERATION231.md](ITERATION231.md). El impacto de la prueba usa defensor fijo en el spawn; queda comprobar el rango contra movimiento natural y armonizar la semilla/avance RNG global del juego.

## Iteración 2.130: alcance geométrico controlado para Suika 623B nivel 9
- La sonda mantiene PAT 821 en el spawn PE `(344.62,261.13)` y barre al defensor: 56/121 posiciones contactan; el centro alcanza el resolver/impacto PE y aplica 800 de daño. La transformación de cajas es reconstruida y cotejada con salidas PE porque falta el fixture de cámara/escenario; no equivale a una traza de combate real.
- Suite Python 115/115; Vita3K SDL schema46/600 frames pasó con regresiones, skills, objetos y contratos de escenarios. VPK/hash y limitaciones: [ITERATION230.md](ITERATION230.md). 530 aún no está implementada en runtime Vita.

## Iteración 2.129: PAT 821 localizado en la ruta Suika 623B nivel 9
- El factory PE original (`0x784020`) resuelve el `0x335` de la acción 530 como PAT 821/seq.0, nueve poses, daño PAT 800. La prueba ejecuta el RNG original y conserva una variante de contacto con posiciones alineadas de forma controlada.
- El objeto natural del fixture aparece en `(344.6202,261.1317)` y termina tras dos updates; el HP -800 solo se acredita en el resolver con contacto forzado. No demuestra rango/impacto de combate natural.
- Prueba enfocada del probe Suika: 2/2; suite Python completa: 115/115. No se modificó el motor Vita ni se creó VPK; falta trazar el comando con entrada/replay natural antes de portarlo. Evidencia: [ITERATION229.md](ITERATION229.md).

## Iteración 2.128: Suika 623B integrado y validado
- Dispatcher PE: nivel9→530, nivel5→525, base→520, ambos niveles activos→bloqueo; se comprueban efectos laterales de `useSkill`.
- Vita3K SDL: `route_mask=15`, daño 1000/500 y activación 530; permanecen aprobadas las regresiones 623C/PAT 821 y escenarios.
- VPK y alcance: [ITERATION228.md](ITERATION228.md). Falta el efecto de 530, progresión real de cartas y cubrir skills/roster y escenarios completos.

## Iteración 2.127: reacción de impacto de Remilia para PAT 821
- El primer cuadro post-impacto verifica HP -800, acción 50/seq.0/pose0 y stun20, cotejado con la selección de reacción y temporizador x86.
- Ambos objetos conservan sus 27 actualizaciones comparadas. Vita3K SDL: schema46/600, route mask31 y gates de escenario; Python 114/114.
- VPK, hashes y límites: [ITERATION227.md](ITERATION227.md). Falta comparar la reacción completa con replay, además de guardia, cartas, roster, escenarios y Vita física.

## Iteración 2.123: ramas 623C por nivel
- Se portó el selector x86 623C de Suika para niveles 5/9. La regresión Vita3K pasó las rutas 521 (1000), 526 (500), 531 (una activación, sin daño atribuido) y bloqueo ambos niveles; route mask 15, schema46/600.
- VPK/hashes, alcance y pendientes: [ITERATION223.md](ITERATION223.md). Reporte actual: `artifacts/vita3k-result.json`.
- Falta conectar el nivel al sistema de cartas/progresión y reconstruir los efectos de 531; el resto de skills y roster sigue incompleto.


## Iteración 2.122: ambos impactos de Suika 623C
- Se corrigió el latch de impacto de las skills para rearmar en poses PAT sin hitbox; la acción 521 ahora conecta sus ventanas de 400 y 600. Vita3K: schema46, 600 frames, gate Suika 1, un uso, daño acumulado 1000.
- VPK hashes y evidencia x86: [ITERATION222.md](ITERATION222.md); reporte guest en `artifacts/vita3k-result.json`. Suite Python 114/114.
- Las rutas de nivel para acciones 526/531 siguen sin integrar; la paridad de hitstop/stun y matchups tampoco está cubierta.


## Iteración 2.121: Suika 623C → PAT 521
- El VPK auto-test pasó Vita3K SDL (schema46, 600 frames); métricas guest: comando/acción/uso = 1/1/1 y daño PAT = 400. El VPK interactivo se reconstruyó con el mismo código.
- Suite Python: 114/114. Hashes y detalle: [ITERATION221.md](ITERATION221.md), [vita3k-result.json](../artifacts/vita3k-result.json).
- Cobertura parcial: niveles de habilidad asumidos cero; no se reprodujo la transición/daño posterior del probe x86. Faltan el flujo completo de esta skill y las skills del resto del roster.


## Iteración 2.120: rebuild actual y gate completo de Vita3K
- Reconstruidos VPK interactivo y autotest desde el árbol actual; ambos comparten `eboot.bin` SHA-256 `d1d730c7849097d8b78a09e75ccc708b2668a9b39cf1e716c9a39abd2879fdf5`.
- Suite Python: 114/114 aprobadas. El autotest pasó Vita3K SDL, schema46/600 cuadros, regresiones, objetos, PAT, cámara y contratos BG33/BG36/BG37/BG38.
- Hashes, reporte y alcance: [ITERATION220.md](ITERATION220.md), [vita3k-result.json](../artifacts/vita3k-result.json). La paridad completa del juego continúa pendiente.

## Iteración 2.119: cursor y contador dentro de un mismo update Story
- `0x47f810` procesa primero el replay por slot 16 (`0x47ee10`), luego llama `0x478640`; este despacha slot 15 (`0x47f7c0`), que llega a `0x4787f0` e incrementa `[0x85eb58]`.
- El probe ahora valida el orden y pasa 53 checks con el PE 2009 fijado. Se prueba un incremento por ejecución del slot 5, no la frecuencia por frame/tick.
- Evidencia y límites: [ITERATION219.md](ITERATION219.md), reporte `artifacts/kernel/replay-manager-selection-original-2009.json`.

## Iteración 2.118: slot 5 Story y cadence del replay
- El caso 3 de `0x43d480` despacha slot 1 (`0x47eaa0`), mientras slot 5 (`0x47f810`) invoca slot 16 (`0x47ee10`) una vez por ejecución. No está probado cuántas veces corre slot 5 por tick/render.
- `0x4787f0` incrementa el contador `[0x85eb58]` tras llamar un slot 5 obtenido de `[0x85eb70]`; ese global es distinto del manager Story `[0x85eb64]`, así que queda como pista separada.
- Probe y prueba focalizada pasan con el PE 2009 SHA-pinned (52 checks); análisis y límites: [ITERATION218.md](ITERATION218.md) y `artifacts/kernel/replay-manager-selection-original-2009.json`.

## Iteración 2.117: VPK actual y psp2-tooling
- Reconstruidos VPK interactivo y de autotest desde el árbol actual con VitaSDK 2026.08; el autotest pasó Vita3K SDL, schema46/600 cuadros y gates de regresión, sprites, objetos y escenarios. Hashes, reporte y límites: [ITERATION217.md](ITERATION217.md), `artifacts/vita3k-result.json`.
- `psp2-tooling` queda registrado como apoyo para profiling/debug en Vita física; no sustituye Vita3K ni ayuda a decompilar el PE. La configuración DevKit/retail tiene dependencias de hardware y firmware que se aplazan hasta tener escena integrada y una consola compatible.
- Esto no prueba paridad total del juego ni FPS en hardware.

## Iteración 2.112: transición de CTitle a Story
- RTTI confirma `0x426d50` como slot 1 de `CTitle`; la tabla de estados enruta estado 12 a `(modo=6, estado=2)`, mientras estados 8/9 asignan modos 4/5 y estado 1.
- Esto prueba un camino estático de la pantalla título hacia el manager Story, pero no que sea la selección de replay Sanae ni la carga de `.rep`. No cambia runtime/VPK.
- Prueba focalizada 1/1, contratos de sonda 36/36: [ITERATION212.md](ITERATION212.md), reporte `artifacts/kernel/replay-manager-selection-original-2009.json`.

## Iteración 2.111: condiciones reales de los callers
- `0x425703` llega al dispatcher de backend únicamente con selector 1 y usa el setup de una fuente si el selector es 0. `0x44af00` fija modo 7/estado 1 antes de inicializar una fuente; `0x4209c1` conserva el selector como estado dinámico.
- Estas rutas de input/configuración no demuestran que el replay Story tenga `f0=3`; no cambia el runtime ni el VPK.
- Sonda/reporte, prueba 1/1 y alcance: [ITERATION211.md](ITERATION211.md), `artifacts/kernel/replay-manager-selection-original-2009.json`.

## Iteración 2.110: callsites de configuración de input
- El scanner `E8 rel32` encontró callers directos del backend (`0x420a91`, `0x4258fe`) y del setup de fuente única (`0x4258ec`, `0x44b091`); se añadió su contexto al reporte JSON y a la regresión.
- El orden de esas rutas respecto a replay Story sigue sin demostrarse. El helper de ventanas falló al inicializar y el ejecutable original no estaba abierto; no se obtuvo traza live. Runtime/VPK sin cambio.
- Evidencia/pruebas: [ITERATION210.md](ITERATION210.md), pruebas focalizadas 3/3.

## Iteración 2.109: slots de fuente para los ocho selectores
- Inventariadas las ocho ramas de `0x43dee0`: selectores 1/2/8 usan una fuente; 3 usa dos punteros fijos; 4/5 enlazan dos ranuras del manager; 6/7 conservan directamente la configuración previa. La inicialización común deja una fuente.
- El writer de input convierte la presencia de esos dos slots en `+0xf0` del objeto de decoder. El modo 6 no permite deducir el valor efectivo sin conocer la secuencia previa de setup; no se conectó playback al motor.
- Evidencia/pruebas: [ITERATION209.md](ITERATION209.md), `tests/test_replay_manager_selection_probe.py`, `artifacts/kernel/replay-manager-selection-original-2009.json`.

## Iteración 2.108: fuentes de input del selector 6
- La tabla de `0x43dee0` confirma que selector 6 indexa `0x43e122`, ruta común sin escrituras directas a los slots de fuente `0x8602ac/0x8602cc`; la asignación explícita de dos punteros ocurre en la rama de selector 3 (`0x43e0a0`).
- Por tanto, dos slots del manager Story no demuestran dos fuentes activas y `f0=3` sigue siendo una condición del harness. No cambió runtime ni VPK.
- Prueba y alcance: [ITERATION208.md](ITERATION208.md), `tests/test_replay_manager_selection_probe.py`.

## Iteración 2.107: replay completo en callback Story
- Se ejecutaron las instrucciones originales `0x47ee10 → 0x42a410` sobre todos los words del replay Sanae. El callback consumió las 16,910 parejas de sus tres registros (33,820 words), cotejó ambas máscaras y los seis setters por pareja, y terminó con cursor en cero.
- El harness fijó estado 2 y `f0=3`; no demuestra selección del menú, número natural de fuentes ni cadence por frame. No se integró playback al runtime Vita.
- Evidencia/reporte: [ITERATION207.md](ITERATION207.md), `artifacts/kernel/replay-story-callback-original-2009.json`.

## Iteración 2.106: dispatch Story validado en Unicorn
- Se ejecutó el prefijo original de `0x47ee10`: estado 2 llama una vez al decoder `0x42a410` con `ECX=0x85ec98`; estado 1 lo omite. El getter de estado ejecuta desde el PE; solo se intercepta el decoder.
- No consume el `.rep`, no demuestra que el menú entre por esa ruta ni mide cadence por frame.
- Evidencia: [ITERATION206.md](ITERATION206.md), `artifacts/kernel/replay-story-callback-original-2009.json`.

## Iteración 2.105: input compartido con el decoder Story
- `0x4281a2 → 0x42d6b0` escribe `+0xf0` del objeto devuelto por `0x43cec0` (`[0x85ec98]`); `0x47ee10` obtiene el mismo objeto y lo pasa a `0x42a410` cuando `[0x85ec08]==2`. La identidad que antes faltaba queda confirmada estáticamente.
- El bloque `0x426de6` solicita selector de manager 6 y estado 2; aún no se probó que sea la rama tomada para el replay Sanae. El número de fuentes efectivas y la cadence siguen sin medirse.
- Evidencia y límites: [ITERATION205.md](ITERATION205.md), reporte `artifacts/kernel/replay-manager-selection-original-2009.json`.

## Iteración 2.104: fases del ciclo global identificadas
- El dispatcher `0x43d480` usa `[0x85ec0c]`: estado 2 llama al selector de manager `0x43cca0`; estados 3–5 llaman sus rutas de update. El selector usa `[0x85ec10]`, escrito por `0x43d8e0`, para elegir la variante Story u otras.
- No se midieron estos valores durante el replay ni su cadencia por frame. La ruta de flags de input sigue sin demostrar identidad con el objeto del decoder.
- Evidencia y pruebas: [ITERATION204.md](ITERATION204.md), reporte `artifacts/kernel/replay-manager-selection-original-2009.json`.

## Iteración 2.103: selector Story e input separados
- `0x43cca0` elige el inicializador Story `0x43b440` para modo 0 y `0x4378d0` para modo 6; ambos escriben `[0x85eb64]` con la instancia Story. El modo efectivo del replay Sanae no está medido.
- `0x42d6b0` escribe flags de presencia de fuentes en el objeto global de input `[0x85ec98]`. No está demostrado que ese sea el mismo objeto que `0x42a410` usa al consumir replay; `f0=3` sigue limitado al harness.
- No se conectó playback ni se infirió cadence. Evidencia y límites: [ITERATION203.md](ITERATION203.md), reporte `artifacts/kernel/replay-manager-selection-original-2009.json`.

## Iteración 2.102: manager y fuentes del replay diferenciados
- `0x85eb64` recibe el objeto con vtable Story en dos inicializadores; los dispatchers globales usan esa instancia. No se ha probado todavía qué inicializador activa el replay Sanae.
- `0x42a410` lee el canal primario/secundario de acuerdo con bits 0/1 de `this+0xf0`; `f0=3` es condición del harness anterior, no configuración medida de cada sesión. No se infiere cadence ni se conecta playback.
- Evidencia: [ITERATION202.md](ITERATION202.md). Siguiente: rastrear selector de inicializador y escritor de `f0`; medir cadence con frame-step.

## Iteración 2.101: RTTI identifica el callback Story del replay
- El PE original confirma que `CBattleManagerStory` reemplaza el slot virtual 16 con `0x47ee10`; base y Arcade usan `0x481040`. El método virtual Story `0x47f810` llega al slot 16 de la misma instancia.
- Esto distingue el callback elegido en una instancia Story, pero no demuestra qué clase construye la sesión del replay ni cadence por frame. No cambió el runtime. Prueba focalizada: 12/12.
- Detalle y reporte: [ITERATION201.md](ITERATION201.md), `artifacts/kernel/replay-manager-vtable-original-2009.json`.

## Iteración 2.100: el cursor C consume parejas atómicas del replay real
- Añadido `t123_replay_next_input_pair()`, que modela los dos words por invocación del decoder x86 cuando ambos slots están activos; un word final sin pareja no modifica cursor ni resultados.
- El build manual Vita incluye ahora `src/replay.c`. El VPK de contrato leyó en Vita3K el replay Sanae de `ux0:data`, validó los tres registros y consumió las 16,910 parejas con salida de aplicación 0. Esto no prueba playback ni cadence por frame; el cursor no se conecta aún a combate.
- El auto-VPK, recompilado tras incorporar el parser al build manual, pasó schema46/600 frames en Vita3K; SHA-256 `01cf0b4b492992c73ade61ddd0ae1f11fd0f794de19b9ac49b3c39797a76afb8`. El paquete interactivo [`Touhou123Vita-replay-core.vpk`](../artifacts/Touhou123Vita-replay-core.vpk) comparte exactamente el `eboot.bin` probado. Reporte fresco: [`vita3k-result.json`](../artifacts/vita3k-result.json).
- Evidencia, hashes y límites: [ITERATION200.md](ITERATION200.md).

## Iteración 2.99: replay ejecutado word por word contra el PE original
- Unicorn ejecutó el método original `0x481040` sobre los 33,820 words de los tres registros del replay Sanae 2009; todas las lecturas, callbacks 0x3c/0x3d, incrementos de cursor y la guarda de fin pasaron. Hashes PE/replay fijados en la nota.
- Esto confirma mecánica por invocación, no cadencia por frame, reproducción completa ni sincronía de ambos jugadores. No se conectó el cursor al loop Vita. Evidencia: [ITERATION199.md](ITERATION199.md).

## Iteración 2.98: gate integral de Vita3K renovado
- El 18 oct 2026 se ejecutó `Touhou123Vita-pat-crop-guest-auto.vpk` en la copia aislada de Vita3K SDL: schema46, 600 frames, `status=passed`, regresión, recorte PAT, cámara/viewport, BG33 y scroll BG36–BG38 aprobados. Hash auto VPK: `96e1782e6bdf7c5dd6a5e627d8b2b52fd1ac4e415136fc603b772815bdab6b71`.
- El interactivo [`Touhou123Vita-pat-crop-guest.vpk`](../artifacts/Touhou123Vita-pat-crop-guest.vpk) es SHA-256 `c511fb78937fe3b12a2b686220f860420ab3729ad784c96e242730a05601b46d`; comparte exactamente el `eboot.bin` probado, SHA-256 `d1d730c7849097d8b78a09e75ccc708b2668a9b39cf1e716c9a39abd2879fdf5`. La corrida integral instaló el auto-VPK; el interactivo se comprobó por igualdad del eboot.
- Reporte/capturas frescos: [`vita3k-result.json`](../artifacts/vita3k-result.json) y [`screenshots/fight.bmp`](../artifacts/screenshots/fight.bmp). El overlay de auto-test impide usar esa captura para paridad visual precisa. Ver [ITERATION198.md](ITERATION198.md).

## Iteración 2.96: WRAP inicial del sampler encontrado
- La inicialización D3D llama a `0x404ad0` para establecer `ADDRESSU=1/WRAP` y `ADDRESSV=2/WRAP` en samplers 0 y 1. El wrapper de filtro `0x404af0` modifica MAG/MINFILTER, no dirección.
- El render directo del jugador `0x4389d0→0x4075d0` no establece U/V; hereda el estado actual. Otra ruta genérica `0x4571a4/0x4571b6` sí cambia sampler 0 U/V desde campos por objeto, así que el valor al instante del frame depende del orden de dibujo. No se atribuye todavía WRAP a los frames extremos concretos.
- Reportes del PE: [`d3d9-sampler-generic-callers.tsv`](../artifacts/kernel/d3d9-sampler-generic-callers.tsv), [`d3d9-sampler-mode-manager.tsv`](../artifacts/kernel/d3d9-sampler-mode-manager.tsv), [`d3d9-sampler-active-paths.tsv`](../artifacts/kernel/d3d9-sampler-active-paths.tsv). Próximo: seguir orden de draw o capturar `GetSamplerState` justo antes del render de un frame PAT. Ver [ITERATION196.md](ITERATION196.md).

## Iteración 2.95: ruta de dibujo de los recortes extremos confirmada
- El descriptor PAT pasa por `0x466720→0x406c60→0x406d30`; la ruta común `0x4075d0` liga la textura y somete dos primitivas a Direct3D sin filtrar por UV fuera de rango ni por flags. Esto confirma el envío del quad, no su apariencia final.
- Se inspeccionó la alpha de borde de los ocho CV2 resueltos: siete tienen bordes opacos y Sakuya `attackAa000.bmp` transparente. El PE usa D3D9; su helper no establece ADDRESSU/V, cuyo default documentado es WRAP, así que el tiling es la hipótesis actual. Falta confirmar cambios globales/efectos en una corrida del original; no se cambia todavía el renderer Vita.
- Disassemblado fijado por SHA en [`pat-crop-render-chain.tsv`](../artifacts/kernel/pat-crop-render-chain.tsv) y [`pat-component-constructor.tsv`](../artifacts/kernel/pat-component-constructor.tsv). Próximo: hallar la configuración global de direccionamiento Direct3D y observar uno de estos frames en el original. Ver [ITERATION195.md](ITERATION195.md).

## Iteración 2.94: clasificación de registros PAT con recortes extremos
- La auditoría previa encontró 8/17,586 frames con `tx/ty` no cero, pero no todos son `alpha000.bmp`: siete usan esa imagen y uno es Sakuya `attackAa000.bmp` (action 40, seq.0/frame0). Los registros tienen `flags` 0, 1 y 2; por tanto, el byte de variante no explica por sí solo la geometría extrema.
- El extractor [`extract_pat_pose_metadata.py`](../tools/extract_pat_pose_metadata.py) expone ahora `flags` y los 16 bytes opcionales como hexadecimal para conservar la variante PAT en el análisis. La presencia de estos valores no prueba todavía si son frames invisibles, una ruta de textura distinta o una convención de UV especial; no se han cambiado las reglas del runtime.
- Ejemplos: Marisa action 47/frame0 (`alpha000.bmp`, `ty=-19704, tw=10876, th=19704`, flags 1); Alice action 304/frame0 (`alpha000.bmp`, `ty=-25016, tw=10876, th=25016`, flags 0); Sakuya action 40/frame0 (`attackAa000.bmp`, `ty=-720, tw=16044, th=720`, flags 1). Las poses siguientes suelen tener rectángulos 64×64/64×128 convencionales. Los `special_data` de los casos flags 2 se preservan para el siguiente cruce con el loader x86.
- Iteración 2.95 demostró que el helper común sí somete el quad, pero aún no identifica el estado global de muestreo; seguirlo antes de atribuir el resultado visual. Ver [ITERATION195.md](ITERATION195.md).

## Iteración 2.93: test de recorte desplazado en Vita3K
- Se añadió `soft2d_texture_region_crop_contract()`: rasteriza un rectángulo `[1,3)×[1,3)` de una textura sintética 4×4, comprueba los cuatro colores fuente y confirma que no alcanza los píxeles externos. El auto-test exige `sprite_region_crop_contract=1`; Vita3K SDL pasó schema46/600 frames con ese campo y todos los gates acumulados en 1.
- `action_sequence_metadata` conserva `tx/ty/tw/th/ox/oy` para cada frame en análisis host. La primera clasificación dijo que los 8 recortes no cero eran `alpha000.bmp`; Iteración 2.94 corrige el resultado: siete son `alpha000.bmp` y uno es `attackAa000.bmp` de Sakuya. Solo queda pendiente aclarar semántica y ruta x86, ver [ITERATION194.md](ITERATION194.md).
- VPK interactivo: [`Touhou123Vita-pat-crop-guest.vpk`](../artifacts/Touhou123Vita-pat-crop-guest.vpk), SHA-256 `c511fb78937fe3b12a2b686220f860420ab3729ad784c96e242730a05601b46d`. Auto-VPK validado: [`Touhou123Vita-pat-crop-guest-auto.vpk`](../artifacts/Touhou123Vita-pat-crop-guest-auto.vpk), SHA-256 `96e1782e6bdf7c5dd6a5e627d8b2b52fd1ac4e415136fc603b772815bdab6b71`. `eboot.bin` compartido: `d1d730c7849097d8b78a09e75ccc708b2668a9b39cf1e716c9a39abd2879fdf5`.
- Suite Python completa: 110/110; VitaSDK compiló los dos VPK; Vita3K test aislado schema46/600 cuadros aprobados. Reporte fresco en [`vita3k-result.json`](../artifacts/vita3k-result.json), incluida la nueva aserción de guest.
- Siguiente: trazar cómo se consumen los registros `alpha000.bmp` y qué textura/formato representan; crear fixture de personaje con recorte no trivial si se encuentra un caso semánticamente normal, y seguir la comparación con PC/replay, combate completo y recursos/escenarios pendientes.

## Iteración 2.92: corregidos los límites del recorte PAT
- El oracle [`x86_sprite_component_probe.py`](../tools/x86_sprite_component_probe.py) ejecuta el constructor x86 `0x406c60` en tres fixtures con origen desplazado y dimensiones distintas. Confirma que `tw/th` son tamaño geométrico del quad y que el UV final es `(tx+tw, ty+th)` dividido entre el tamaño de textura. Reporte: [`sprite-component-contract.json`](../artifacts/kernel/sprite-component-contract.json).
- Se corrigieron las llamadas de render de jugadores y objetos: Soft2D recibe ahora `tx,ty,tx+tw,ty+th`. Antes se pasaban `tw/th` como límites absolutos, lo que recortaba de más cualquier frame cuyo origen PAT no fuera cero.
- Suite Python 110/110 y prueba focalizada 10/10; VitaSDK generó ambos VPK y Vita3K SDL aislado pasó schema46, 600 frames y todos los gates de regresión/cámara/BG33/BG36–BG38. Auto VPK probado: [`Touhou123Vita-pat-crop-auto.vpk`](../artifacts/Touhou123Vita-pat-crop-auto.vpk), SHA-256 `fd15c4fdbbbb522c33f40a491b32cf67a7ad12d841b0313ad6f41983fa8f3b26`; interactivo: [`Touhou123Vita-pat-crop.vpk`](../artifacts/Touhou123Vita-pat-crop.vpk), SHA-256 `2e6d9e9445040bffea8acce0f3a462eb0051305cc9d0137da130cac3b9d4e9dc`. `eboot.bin` común: `82963353ebf4c610204bfba41e8e8632755e52ab4941744b38363bb4ba8ac026`.
- Captura/reportes frescos: [`fight.bmp`](../artifacts/screenshots/fight.bmp), [`vita3k-result.json`](../artifacts/vita3k-result.json). Aún falta un test de guest que fuerce recortes PAT con `tx/ty` no cero y una captura comparativa sincronizada del juego original. El oracle valida el constructor del quad, no el mapeo de escala de mundo ni paridad de píxeles.
- VitaFS de esta instancia está bajo `artifacts/vitafs`: contiene los DAT montados para Vita3K y reportes/capturas de las corridas, fuera del VPK y del control de versiones. No se añadieron recursos comerciales al paquete.
- Próximo: introducir una pose de jugador y otra de objeto con recorte desplazado al smoke Vita3K, comparar un cuadro contra el juego original usando una versión compatible del replay y seguir con skills/B/C, objetos y composición de escenarios faltantes.

## Iteración 2.91: recorte de textura PAT aplicado al renderer
- La sonda SHA-pinned [`x86_sprite_quad_probe.py`](../tools/x86_sprite_quad_probe.py) pasa contra `th123.exe` (`f0db9366…16731e`) y confirma layout del registro en disco, traslado loader a offsets runtime, signo de `ox/oy/tx/ty`, paso del rectángulo a `0x406c60` y normalización UV por dimensiones de textura.
- El renderer Soft2D consume ahora el rectángulo PAT (`tx,ty,tw,th`) con espejo horizontal por facing y coloca el sprite con `ox/oy` firmado dentro de la proyección dinámica de cámara. Esto implementa el contrato del quad/recorte; el anclaje exacto y la escala contra coordenadas del juego siguen experimentales y requieren comparación de poses del PE/replay.
- Pruebas: test focalizado de cámara/renderer 10/10; suite Python 110/110; Vita3K SDL aislado pasó 600 cuadros, schema46, `regression_gate=1`, contratos de cámara/viewport/BG33/BG36–BG38 aprobados. Reporte fresco: [`vita3k-result.json`](../artifacts/vita3k-result.json); captura de pelea: [`fight.bmp`](../artifacts/screenshots/fight.bmp). La captura muestra ambos sprites completos, pero el texto de autotest cubre el piso y no permite afirmar paridad visual exacta.
- VPK interactivo para revisar: [`Touhou123Vita-pat-quad.vpk`](../artifacts/Touhou123Vita-pat-quad.vpk), SHA-256 `11cf2ba5d80774dae7ea42d641ebea5bb4d5b14d37a62cc515162f9a44959f4e`. VPK automático probado: [`Touhou123Vita-pat-quad-auto.vpk`](../artifacts/Touhou123Vita-pat-quad-auto.vpk), SHA-256 `d6a2992612afafa139b7c234ddf9a0fd25c7d32b5e96f1688dfb7eaa1101ea74`. Ambos contienen el mismo `eboot.bin` (SHA-256 `35cdbd4005b5a41293210fb320a65a88e55ace9f89dd45f27639a2e48c39ebbf`).
- Siguiente: comparar poses PAT quieta, aérea y de ataque con coordenadas/capturas del juego de PC; recuperar origen/escala exactos; después llevar el mismo contrato a objetos y completar las rutas de combate y escenarios que faltan. Esta prueba no cierra la decompilación ni una ronda completa.

## Iteración 2.90: offsets PAT y renderer compartido
- El parser C/extractor Python preservan `tx/ty` como `int16`; `0x466670` los lee con signo y los copia al componente gráfico. El probe del PE demuestra que Reimu, objeto base y Suwako 808 comparten el callback de slot 11 `0x438d20`.
- Se descartó la fórmula que colocaba el sprite directamente desde esos offsets: el PAT idle de Reimu tiene `tx=ty=0`, y la captura mostró el sprite cortado bajo el HUD. El quad/origen configurado por `0x406c60` aún debe reconstruirse; el renderer conserva el anclaje anterior basado en `ox/oy` mientras tanto.
- VPK revisable [Touhou123Vita-pose-anchor-review.vpk](../artifacts/Touhou123Vita-pose-anchor-review.vpk), SHA-256 `643ddd9dcd7125bd524025aa75e83548b6a6c8fbbd47ccd3fc6be7fcff084a51`; VPK automático [Touhou123Vita-pose-anchor-review-auto.vpk](../artifacts/Touhou123Vita-pose-anchor-review-auto.vpk), SHA-256 `3317de974109c2f5c8850a32b642ac912acb3581e25db21daf2a13745b738058`. Vita3K SDL pasó 600 cuadros/schema46 y gates acumulados; Python 110/110 y prueba focalizada 10/10. Captura: [fight.bmp](../artifacts/screenshots/fight.bmp).
- La fixture C de offsets negativos está añadida, pero no se ejecutó en host. Siguiente: reconstruir el contrato geométrico del quad y el origen local con evidencia x86, y después comparar varias poses. Ver [ITERATION190.md](ITERATION190.md).

## Iteración 2.89: inicialización del sprite del jugador localizada
- El slot 11 de Reimu (`0x438d20`) dibuja `Player+0x154` por `0x4389d0`; este aplica la cámara mediante `0x4293f0`.
- `0x466670` crea/configura el componente gráfico y carga dos palabras del registro de imagen en `+0xf0/+0xf4`; esos valores son metadatos de pose/imagen, no dimensiones. Falta mapear el registro exacto a `T123Pose`.
- Test focalizado de cámara 10/10; runtime y VPK no cambiaron. Evidencia: [ITERATION189.md](ITERATION189.md).

## Iteración 2.88: cámara dinámica conectada a personajes y objetos
- El vtable de Reimu confirma que el slot 11 (`0x438d20`) dibuja `Player+0x154` mediante `0x4389d0` y la transformación de cámara `0x4293f0`; ya está probada la ruta de jugador. Queda mapear los campos locales del componente y su anclaje PAT a píxeles. La proyección queda `(world - camera - viewport) * zoom + (320,420)`.
- `Fight` mantiene y actualiza `T123StageCamera` cada tick; las posiciones X del prototipo pasan en unidades originales y la altura Y se invierte. Sprites, objetos y piso usan ahora la proyección dinámica; UI y fondo placeholder permanecen en su espacio actual.
- Python 110/110; Vita3K SDL pasó 600 cuadros/schema46, regresiones, gate de cámara y gates acumulados de escenarios. Captura fresca: [fight.bmp](../artifacts/screenshots/fight.bmp). El build host C con GCC/MSYS2 se atascó sin CPU; el build VitaSDK y el gate ARM corrieron correctamente.
- VPK auto-test `Touhou123Vita-live-camera-auto.vpk` SHA-256 `79343255129ded37359fccd75bc8d662b0df3fc0851ffdb0ff4c1ebafd1e8203`; interactivo `Touhou123Vita-live-camera.vpk` SHA-256 `cf4bd425caac95eeeff8d54c546be72a63a3bcdd64a6f0b3b690b60932ce295e`. Comparten `eboot.bin` SHA-256 `a1990b578618cf789ee7d1ca0b5c22734935d827bf2d964ca65cf2450ff6667b`. La cámara dinámica se limita a combate; la UI conserva la vista neutral.
- Falta mapear los campos de posición/escala del componente del luchador y recuperar su anclaje vertical exacto y sustituir el fondo placeholder por la composición real del escenario antes de afirmar paridad visual. Evidencia y pasos: [ITERATION188.md](ITERATION188.md).

## Iteración 2.87: actualización completa por tick de cámara
- Se añadió `T123StageCamera` y `t123_stage_camera_step`, que refresca centro/zoom/target Y y aplica en secuencia el easing de zoom, X e Y medido en el PE.
- El vector encadenado de constructor + segundo update concuerda con el oracle x86; el gate ARM/Vita3K pasó 600 frames/schema46 y la suite Python pasó 109/109.
- VPK auto-test: `Touhou123Vita-camera-state-auto.vpk`, SHA-256 `590ae74f9bad57f761e4a00630168bc9490f9fe89a2088fa00eefca51602063c`. Interactivo: `Touhou123Vita-camera-state.vpk`, SHA-256 `78f75bbf5fe38b145aee00202c3cc0aa3fcb1793f57cb09e0dd3d67774535720`.
- El estado aún no vive en `Fight` ni proyecta sprites/fondos: la escala y orientación entre las coordenadas simplificadas del prototipo y el espacio de escena original siguen por demostrar. Próximo: medir esta conversión con vectores del PE y luego conectar el mismo estado al tick/render de combate. Ver [ITERATION187.md](ITERATION187.md).

## Iteración 2.86: easing vertical de la cámara
- `FUN_00429040` actualiza Y con divisor 20 (jugadores con mínimo Y ≤ 270) o 10 (mínimo > 270), añade el paso constante ±1, hace snap al cruzar el objetivo y limita la vista a `[-420*(2*zoom-1), 0]`.
- Se implementó `t123_stage_camera_y_step`; el oracle Unicorn/x86 y la suite Python completa pasan 109/109. Vita3K SDL pasa 600 cuadros, schema46, `regression_gate=1` y `stage_camera_pair_contract=1`.
- El VPK interactivo comparte `eboot.bin` con el auto-VPK probado. Esta rutina aún es contrato aislado y no está conectada al seguimiento de cámara del combate. Evidencia: [ITERATION186.md](ITERATION186.md).

## Iteración 2.79: proyección común de auxiliares BG36
- Los cuatro slots del constructor usan ahora un helper geométrico común con sus pivotes y anclajes del renderer x86; el visor preserva sus posiciones/tamaños relativos en una referencia de cámara cero.
- Vita3K SDL aprobó schema46/600 cuadros y el contrato numérico `stage_bg36_aux_projection_contract=1`; Python 100/100. Interactivo recompilado con el mismo `eboot.bin` del auto-VPK probado. Cámara dinámica e integración de fondos al combate siguen abiertas. [ITERATION179.md](ITERATION179.md).

## Iteración 2.78: gate estable para proyecciones BG36
- La navegación reiniciaba el contador de nubes al volver a BG36 después de tomar la captura. Se conserva ahora la evidencia acumulada durante la corrida, sin alterar el reinicio del scroll.
- Vita3K SDL: schema46, 600 cuadros, `regression_gate=1`, cuatro proyecciones BG36; suite Python 100/100. El VPK interactivo se reconstruyó y su `eboot.bin` coincide con el binario probado. Cámara viva e integración de escenarios en combate siguen pendientes. [ITERATION178.md](ITERATION178.md).

## Iteración 2.77: anclaje común y pivotes de nube BG36
- El renderer envía ambos pases de nubes al mismo anclaje (+0x44/+0x48); el constructor define pivotes distintos. El core modela la conversión a origen de dibujo y la página los compone según ese pivote.
- Vita3K SDL pasó 600 cuadros/schema46 y la suite 100/100. La escala/cámara de combate sigue pendiente. [ITERATION177.md](ITERATION177.md).

## Iteración 2.76: auxiliares BG36 y export de renderers
- La página BG36 muestra ahora los cuatro auxiliares del constructor; el análisis PE separa los transforms conocidos de torii de las posiciones de nubes aún por recuperar. Nuevo exportador SHA-pinned: 1,667 instrucciones BG36–BG38.
- VPK recompilados; Vita3K 600 cuadros/schema46 pasó y la suite Python pasó 100/100. [ITERATION176.md](ITERATION176.md).

## Iteración 2.75: mapeo de slots de renderer BG36–BG38
- Contraste entre constructor y renderer corrigió la semántica: BG36 desplaza tori1/tori2; BG37 desplaza tori1/clowd_l y coloca clowd_s fijo en (492, −401); BG38 desplaza clowd_l/clowd_s.
- VPK interactivo y automático recompilados. Vita3K SDL pasó 600 cuadros/schema46; Python 100/100. Las capturas siguen siendo diagramas de diagnóstico; aún falta integrar las capas y reconstruir cámara/composición. [ITERATION175.md](ITERATION175.md).

## Iteración 2.74: callbacks de scroll BG37/BG38
- Los rates, wraps, offsets iniciales y diferencia de contador se midieron correctamente; la etiqueta previa de ambos offsets como nubes fue refinada en 2.75 al cotejar constructor y renderer. [ITERATION174.md](ITERATION174.md).

## Iteración 2.73: cobertura auxiliar exacta BG37/BG38
- El constructor Ghidra/x86 de BG37 reserva y carga tres auxiliares (`tori1`, dos nubes); BG38 reserva y carga dos nubes. El auditor ya no espera torii que el PE tampoco solicita.
- Auditoría regenerada: BG36 4/4, BG37 3/3, BG38 2/2. Pruebas focalizadas 4/4; Python total 96/96. Esto corrige inventario, no integra escenas ni modifica VPK. [ITERATION173.md](ITERATION173.md).

## Iteración 2.72: replay completo sobre el método x86
- Unicorn ejecutó las 33.820 palabras reales del replay Sanae a través de las instrucciones originales de `0x481040`: máscara escrita, callbacks `0x3c/0x3d`, avance de cursor y guard de fin de vector coinciden en todos los casos.
- Los guards, getters y auxiliares están controlados; esto no mide llamadas/frame ni es playback en vivo. Reporte: [JSON](../artifacts/x86-replay-update-method-full-original-2009.json); detalle: [ITERATION172.md](ITERATION172.md). Runtime/VPK sin cambio.

## Iteración 2.71: dispatch y cursor de replay
- El PE 2009 verifica que `0x481040` lee una palabra por avance de `[0x85d748]+0x14`, escribe flags de input `0x3c/0x3d` en la rama guardada y avanza el cursor; `0x4600fe` hace peek/compare/consume. Ambos callbacks revisados llaman `0x42a410` en modo 2.
- La frecuencia por frame y el callback natural de cada modo siguen desconocidos. Sonda y evidencia: [ITERATION171.md](ITERATION171.md), [JSON](../artifacts/x86-replay-dispatch-original-2009.json). Runtime/VPK sin cambio.

## Iteración 2.66: parser y cursor replay en C
- `src/replay.c` valida el formato 2009 y expone IDs, cursor de secuencia y decodificación de la máscara/flags sin copias ni supuestos de cadence; se integró a `t123_core` y su contrato C a CTest.
- VitaSDK 15.2 compila módulo y prueba con warnings como errores, y enlaza el ELF de contrato; Python 91/91 pasa. No se ejecutó el ELF ARM. GCC host se atascó en `cc1` y reportó temporal MSYS2 denegado; CTest host queda pendiente.
- Sin cambio/rebuild del VPK: aún no se conecta replay a la carga ni al combate. Detalle en [ITERATION166.md](ITERATION166.md).

## Iteración 2.68: decoder original ejecutado sobre todo el replay
- Se añadió el oráculo Unicorn `tools/x86_replay_input_probe.py` y se ejecutó la `0x42a410` original sobre las tres secuencias del replay compatible. Con `this+0xf0=3`, las 16.910 llamadas consumen dos words cada una; máscara baja, seis flags del primer word y agotamiento final coinciden con el modelo estático.
- Esto verifica decoder/cursor bajo flags activos, pero no la cadence del loop ni el valor natural de los flags por ronda. El runtime y VPK siguen sin cambios; playback funcional sigue pendiente. Reporte local `artifacts/x86-replay-input-oracle.json`; detalle en [ITERATION168.md](ITERATION168.md).

## Iteración 2.69: el modo de dos slots depende de punteros activos
- `0x42d6b0` escribe `f0 = 2*(input_state[0x44] != 0) + (input_state[0x24] != 0)` sobre el estado global `0x860288`; tiene llamada directa desde `0x4281a2`. Los bits reflejan presencia de dos fuentes de input, no una constante del formato. Falta verificar sus valores y orden en una ronda replay real.
- `0x47ee10` y `0x481040` son dos rutas con llamadas a `0x42a410` en modo 2. La relación de sus dispatchers con un mismo tick no está resuelta; no conectar el cursor suponiendo una llamada/frame. Ver [ITERATION169.md](ITERATION169.md).

## Iteración 2.70: decoders separados por slot
- `0x43dee0` selecciona backend según `[0x85ec10]`; ramas del PE dejan un slot o dos fuentes activas. `0x42a410` mapea los flags altos solo en slot 0; slot 1 solo toma `word & 0x03ff`.
- Se corrigieron los helpers C/Python y el resumen JSON schema2. El oráculo compara cada pareja del replay completo y todos los callbacks; 16.910/16.910 pasan. Python 93/93; VitaSDK compiló/enlazó el contrato ARM, pero no fue ejecutado. Sin cambios/VPK. Ver [ITERATION170.md](ITERATION170.md).

## Iteración 2.65: IDs de personaje e inputs del replay
- `0x42d560` toma los dos primeros bytes de un registro de `0x50` como selección de los dos combatientes; el replay Sanae produce (15,16), (15,17), (15,0), que concuerda con la tabla roster actual.
- La grabación agrega `[0x85eb58]` al vector `record+0x3c`; el modo replay consulta/consume ese vector y `0x42a410` separa la máscara baja `0x03ff` y seis flags mapeados a IDs de entrada. Parser e inspector exponen esta evidencia sin asignar nombres a los botones ni timings.
- 8 pruebas específicas y la suite Python completa (91/91) pasan; el JSON original fue regenerado. La cadencia exacta, una ejecución step-frame y paridad completa siguen pendientes; sin cambios ni nueva corrida del VPK. Ver [ITERATION165.md](ITERATION165.md).

## Iteración 2.64: ruta del menú al loader de replay
- El manejador de selección en `0x44a0e0` construye la ruta del archivo y llama a `0x42e030`; si el loader acepta el `.rep`, solicita transición `0x28` y escribe `0x848a94=6`. Esto enlaza el loader estructural con la ruta de reproducción seleccionada desde el menú, pero no prueba todavía que el combate reproduzca los registros.
- En el PE original, `0x42e030` lee la cabecera extendida en `objeto+0xe8`, toma el número de registros desde `+0xef`, inicializa la colección en `+0xf4` y decodifica cada elemento con `0x42cd60` en stride `0x50`; guarda `cantidad-1` en `+0x140`. Los significados de los campos del registro y de sus secuencias `uint16` siguen abiertos.
- Evidencia y siguientes xrefs en [ITERATION164.md](ITERATION164.md). No cambió el runtime ni el VPK.

## Iteración 2.63: replay decodificado estructuralmente
- El loader 2009 `0x42e030` y decoder `0x42cd60` fijan un esquema con cabecera extendida y tres registros de stride `0x50` en memoria. El inspector consume el replay Sanae completo: 67,881 bytes, 3 registros y cero sobrantes; seis pruebas sintéticas nuevas.
- Reporte resumido: [replay-layout-original-2009.json](../artifacts/kernel/replay-layout-original-2009.json). Se mantienen sin verificar la semántica de las secuencias y el playback real; no llamarlas frames/inputs todavía.
- VPK y runtime sin cambios respecto a Iteración 2.62. Ver [ITERATION163.md](ITERATION163.md).

## Iteración 2.62: VPK vigente y regresión espejo corregida
- El trail 801 conserva spawn cuantizado y los hitboxes de objetos se espejan una sola vez usando el facing. `fight_contract` ahora verifica el daño 120 HP en orientaciones derecha e izquierda.
- Siete contratos C compilados/ejecutados con GCC/MSYS2 pasaron; suite Python 83/83 pasó. WSL sigue inaccesible (`E_ACCESSDENIED`), por lo que esto no es una corrida CTest.
- [VPK interactivo vigente](../artifacts/Touhou123Vita-latest.vpk): 92,330 bytes, SHA-256 `a84133ecc36ef2ba19505a4bd7e5fe8c577c283d44152538b75e9825768c6c7b`. Vita3K SDL pasó schema46/600 frames, regresiones y contratos de BG33/Remilia/Suwako. Ver [ITERATION162.md](ITERATION162.md).

## Iteración 2.61: pruebas host y replay
- El rebuild fresco en WSL destapó fallos de combate y precisó revisar las coordenadas del objeto antes de interpretar sus asserts. La suite actual se ejecutó con GCC/MSYS2 y Python nativos; ver Iteración 2.62.
- Se confirmó estáticamente que `0x42B4D0` lee cuatro bytes del replay y que el caller `0x42BDD1` compara el DWORD contra el helper `0x43CA50`. Esto verifica el guard inicial, no el parser de frames ni la reproducción.
- El offset SokuLib `0x42EAC0` apunta a otra función en el PE 2009 suministrado; no reutilizar offsets entre builds sin fijar el hash. Ver [ITERATION161.md](ITERATION161.md).

## Iteración 2.60: gate fresco del VPK
- El auto-VPK `Touhou123Vita-remilia-lifecycle-auto.vpk` pasó una corrida nueva de Vita3K SDL: schema46, 600 frames, `status=passed`, regresión general y contratos BG33; se guardaron capturas actuales.
- El `eboot.bin` del VPK interactivo `Touhou123Vita-latest.vpk` tiene el mismo SHA-256 que el probado. La suite host no se ejecutó: `ctest` falta en PATH y `wsl.exe` devuelve `Wsl/EnumerateDistros/Service/E_ACCESSDENIED` en esta sesión. Ver [ITERATION160.md](ITERATION160.md).

## Iteración 2.59: ciclo visual secundario Remilia 801
- El runtime conserva seis trails seq.1 después de retirar el objeto raíz al tick 73. Rutas de objeto, edades y desplazamientos discretizados validados en la compilación de prueba.
- VitaSDK compila limpio; `tests.test_remilia_412_spawn_probe` pasa 5/5; Vita3K SDL schema46/600 frames pasa con `regression_gate=1`.
- VPK interactivo: `artifacts/Touhou123Vita-latest.vpk`, SHA-256 `6b3a137e6edd7e2f90a67e1f89619e705432574147f045ebd9af5194c1add888`. Su eboot coincide con la auto-prueba aprobada, SHA-256 `e08d9412508058c3e8e29e9dd63848207174a781ddf1fdcae9b5d00c2c4f935f`. Ver [ITERATION159.md](ITERATION159.md).

Fecha de esta evaluación: 2026-10-17 (America/Mexico_City).

## Herramienta evaluada: psp2-tooling

[Grarak/psp2-tooling](https://github.com/Grarak/psp2-tooling) puede automatizar validaciones en Vita física (instalación/lanzamiento USB, input, capturas, core dumps y profiling CPU/Razor GPU). No compila nuestro VPK ni interviene en Vita3K o el parser `.rep`; se reserva para M7, cuando haya hardware. Requiere host Linux; el soporte retail se documenta para PCH-2000, 3.65, Ensō/taiHEN y módulos DevKit extraídos por el usuario, con cambios persistentes al modo debug. Probar primero la ruta DevKit disponible y posponer `retail-cp` hasta comprobar compatibilidad y necesidad. Repo GPL-3.0, herramienta host separada.

## Render PAT: alcance de sampler — Iteración 2.97

El barrido completo fijado por hash cuenta 30 callers directos a `0x404ad0`. Inicialización establece WRAP; callbacks SpriteEx y los grupos de escena revisados aplican CLAMP solo en el pase y restauran U/V a WRAP. El draw de jugador no cambia el sampler localmente. Sigue pendiente observar orden dinámico y capturar visualmente los ocho PAT extremos; el intento de inspección UI se detuvo al fallar el runtime Computer Use antes de abrir el juego. Ver [ITERATION197.md](ITERATION197.md).

## Build anterior — 17 octubre 2026

El VPK interactivo vigente es [Touhou123Vita-latest.vpk](../artifacts/Touhou123Vita-latest.vpk), 92,330 bytes, SHA-256 `a84133ecc36ef2ba19505a4bd7e5fe8c577c283d44152538b75e9825768c6c7b`. Vita3K SDL confirmó el propio hash: schema46/600 frames, regresión general, BG33, Suwako 418 y ciclo Remilia. Ver [ITERATION162.md](ITERATION162.md).

El runtime emite 25 trails 801/seq.1 además del objeto raíz; después de retirarse el padre al tick 73, quedan seis secundarios activos con edades y desplazamientos cotejados con la fixture x86. La prueba integral sigue controlada: replay Sanae compatible estáticamente con el ejecutable 2009 (`0x100c8`) pero sin reproducción real; efectos visuales de spell aún simulados; faltan round completo, otras rutas especiales, composición BG33 en combate y mecánicas de todos los escenarios. Los DAT originales siguen externos al VPK. Ver [ITERATION157.md](ITERATION157.md), [ITERATION158.md](ITERATION158.md) e [ITERATION159.md](ITERATION159.md).

La build del runtime Alice de la Iteración 2.26, `artifacts/Touhou123Vita-current.vpk`, sigue en `8368849683ba22301bd69e25d6cc273d4fc056ee9b23d44d04ce744122881340`. La corrida diagnóstica más reciente usa `artifacts/Touhou123Vita-bc-probe-next.vpk` (SHA-256 `0339fb5e6e16c955b31fc22d1295ca1eb3516d84d308291e0cbc5b4c00893e02`): Vita3K SDL pasó schema31/600 frames, conserva PAT/sprites/tarjetas 20/20, BG34 y skills 102/103/104/107. A natural alcanza 20/20; la sonda B registra 15/20 (`0x0EBBBE`) y C 15/20 (`0x0BF9B7`). La orientación relativa correcta del jugador de prueba y la ventana aérea ampliada no cambiaron estos impactos. Esta matriz solo verifica ataques directos u objetos reconocidos por la sonda; no cuenta especiales por motion command ni daño por flags sin cajas PAT. Los resultados B/C siguen siendo diagnósticos, no un gate de paridad. Este VPK contiene solo la demo runtime, sin la instrumentación x86 de análisis.

## Hit-confirm x86 de Suika 521/526 — Iteración 2.30

El resolver de dos jugadores del PE confirma overlap y aplica la respuesta especial de Suika: acción 521/seq.1/frame0 reduce 533 HP desde un PAT de 400; acción 526/seq.0/frame7 reduce 666 HP desde un PAT de 500. Ambas pasan a reacción 74 y retornan sin error. Control Remilia conserva 200 de daño. Los multiplicadores condicionales de los flags PAT de Suika quedaron inicializados a 1.0 en el fixture. El efecto todavía es sintético y la corrida no usa input/replay natural. Suite enfocada 6/6; suite completa pendiente. Sin cambios en runtime/VPK. Ver [ITERATION130.md](ITERATION130.md) y [probe de hit-confirm](../tools/x86_player_pair_hit_probe.py).

## Spawn e impacto x86 de Suika 623C/531 — Iteración 2.31

El constructor completo `PlayerSuika` retorna; acción 531 solicita 821, y el update padre completa 40 ticks. La factory y dispatcher originales cargan 821/seq.0 y PAT de daño 800; el hijo está activo al primer update y se retira tras 27 ticks. Contra Remilia 602/seq.0/frame0, la geometría y fase `0x47ce20` confirman contacto; el PE escribe HP 1000→200 y fija el temporizador de reacción `+0x194=20` (`+0x196` hitstop=0). Sin `Player+0x72c` (`spellBgTextures`), el update de Remilia termina por CRT `0xC000000D`; con deque y handles centinela sintéticos, avanza las ocho poses PAT de 602 durante 50 ticks y solicita el fondo de hechizo 6/timer 2. En tick 50 selecciona acción 0; tick 51 queda sin PAT y termina en EIP nulo. Es evidencia de lógica CPU hasta la transición, sin texturas/render, replay natural o round completo. Reporte `artifacts/x86-suika-action-setter-current.json`; runtime Vita/VPK sin cambios. Ver [ITERATION131.md](ITERATION131.md).

## Dispatch x86 de Suika 623C — Iteración 2.29

La sonda ejecuta el bloque original del handler a partir de `0x60a45c` con el bit 623C inyectado. Confirma selección 531/526/521 al variar niveles y rechazo cuando los tres move-locks devuelven `0xffff`. Una segunda sonda ejecuta setter/initializer/lookup PAT y hasta 40 updates originales: acción 521 alcanza PAT seq.1/pose0 con daño 400 y una caja en tick12, y seq.3/pose0 con daño 600 en tick30. Los casos 526 y 531 paran antes del impacto en la fixture parcial. El constructor especializado tropieza con el registro SEH de Win32 (`FS:[0]`), que Unicorn no modela; el probe de setter registra esos campos parciales como evidencia no completa. La nueva Iteración 2.30 ya valida 521/526 contra el resolver x86 con constructor base controlado. Siguen pendientes input/matcher natural y la ruta 531. Ver [ITERATION129.md](ITERATION129.md), [dispatch probe](../tools/x86_suika_623c_dispatch_probe.py) y [setter/update probe](../tools/x86_suika_action_setter_probe.py).

## Análisis actual — Iteración 2.28

Se resumieron estáticamente los 20 handlers del ejecutable de referencia: 713 callsites de `useSkill` con primer argumento inmediato 400–599, 682 parejas handler/acción y pruebas de bits de input en los 20 CFGs. La firma y el probe x86 confirman que ese primer argumento se entrega a `setAction`, por lo que es el action ID PAT. El análisis no modifica el runtime ni genera VPK. Extracción y pruebas relacionadas de dispatch pasan 9/9. Próximo: ejecutar los gates de Suika 623C y seguir pose/objeto, luego producir el comando con el input original. Ver [ITERATION128.md](ITERATION128.md); el TSV local se genera con [summarize_character_skill_dispatch.py](../tools/summarize_character_skill_dispatch.py).

## Iteración 2.27: orientación y ventana de las sondas B/C

El análisis de `src/vita_main.c` encontró que la prueba de roster movía siempre al jugador 0 con `IN_RIGHT`, incluso cuando cargar un personaje en el slot 0 dejaba su rival real a la izquierda. Se actualizó la aproximación para seguir `face`, se reflejaron las direcciones por ruta, y se amplió de 5 a 11 los offsets de airtime para ataques aéreos. Ahora el rival se mantiene en una posición neutral de combate a distancia fija.

La build fresca aprobó Vita3K SDL schema31/600 frames. B/C quedó igual respecto de los impactos observados (`0x0EBBBE`/`0x0BF9B7`), así que la orientación y el muestreo temporal no explican las rutas restantes. Las 20 carpetas de PAT, sprites y tarjetas continúan disponibles; BG34 y las regresiones de habilidades pasaron. SHA-256: `0339fb5e6e16c955b31fc22d1295ca1eb3516d84d308291e0cbc5b4c00893e02`.

Alcance: estos bits no son la cobertura completa de B/C del juego. El probe intenta acciones con daño/cajas PAT directas u objetos cubiertos; handlers originales tienen además gates de input, nivel de skill, estado y rutas por flags. Por ejemplo, el handler Suika `0x609dc0` separa acciones dash de las ramas de comandos `623B/623C` (`Player+0x7c8`, bits `0x200/0x400`), con gates de nivel. No se debe tratar una ausencia en esta sonda como prueba de que el personaje carece de ataque B/C. La selección exacta 408/418 y las rutas especiales siguen pendientes de ejecutar con layout/input original y contrastar contra replay o juego PC.

## Iteración 2.26: secuencia de objeto Alice 66B y un impacto por actualización

El PE original para Alice 849 confirma la cadena no-loop seq.19→20 y luego seq.21 (secuencia de ataque loop). La seq.20 incluye una pose con caja/daño 150 y seq.21 tiene cajas de 450. El runtime ahora conserva la tabla PAT completa para los objetos, avanza entre secuencias y mantiene vivo el objeto lo suficiente para alcanzar el golpe; al detectar contacto detiene el barrido de las demás cajas para no aplicar dos veces el daño de una misma pose.

La sonda natural de Vita3K registró Alice 66B (408) y 66C (418): B mejoró de 14/20 a 15/20 (`0x0EBBBE`) y C de 15/20 a 16/20 (`0x0BF9BF`) en aquella corrida. Las 45 pruebas Python pasaron; VitaSDK compiló `src/fight.c` y `tests/fight_tests.c` con `-Wall -Wextra -Werror`. El contrato C no se ejecutó como binario host porque CMake/WSL no están disponibles. Hash VPK de esa etapa: `8368849683ba22301bd69e25d6cc273d4fc056ee9b23d44d04ce744122881340`. La Iteración 2.27 corrigió orientación de la sonda y amplió su muestreo aéreo, pero produjo B/C `0x0EBBBE/0x0BF9B7`; no cambió el runtime de combate. Ver [ITERATION126.md](ITERATION126.md) y [ITERATION127.md](ITERATION127.md).

## Iteración 2.25: el resolver de dos Players completa daño y reacción

`tools/x86_player_pair_hit_probe.py` ejecuta el resolver original `0x47c770` con dos Players y geometría PAT Remilia 320/frame3 contra 321/frame0. El PE confirma `CollisionType=1`, aplica 200 de daño (1000→800), solicita el efecto PAT `0xC9` y completa la reacción original del defensor: acción 50, seq.0 y tres poses, sin error de ejecución. La transición requiere enlazar el vtable `PlayerRemilia` (`0x85D284`) y resolver por acción el PAT de reacción; el administrador de efectos permanece simulado y no hay entrada/replay ni render. Pruebas enfocadas: 6/6 para el probe de dos Players y regresiones Remilia 412. La suite host completa no se pudo iniciar en este entorno porque `cmake` no está en PATH. Ver [ITERATION125.md](ITERATION125.md).

## Iteración 2.24: hit-confirm repetible entre dos Players

El probe `tools/x86_player_pair_hit_probe.py` reproduce geometría PAT de Remilia 320/frame3 contra 321/frame0, `CollisionType=1`, incremento de combo, petición de efecto `0xC9` y pérdida real de 200 HP (1000→800 en `Player+0x184`). La condición necesaria era enlazar los bloques de ataque/defensa leídos por `0x463f50`; sin ellos, el daño calculado era cero. La respuesta posterior todavía termina en `EIP=0` durante la transición/limpieza; la fixture de efecto es sintética y no conduce input/replay. El contador contextual `+0x7c+team*4` no cambia. Suites: Remilia 412 5/5 y combate de dos Players 1/1. Sin cambios al VPK/runtime. Ver [ITERATION123.md](ITERATION123.md) y [ITERATION124.md](ITERATION124.md).

## Iteración 2.08: callsite Remilia 412 → objeto 801

- **Iteración 2.14:** `0x47b660` ejecutada después del overlap PAT resta el daño real 120 (HP 1000→880) y fija cooldown 9; después el callback global de presentación termina en nulo. Prueba separada opt-in; pair dispatch manager y guardia/hitstop siguen pendientes. Ver [ITERATION114.md](ITERATION114.md).
- **Iteración 2.15:** `0x47ce20` alcanza `0x47ca70/0x47c990` con listas controladas y flags PAT. El neutral real del fixture (`frameFlags=0x31`) no recibe daño; al forzar `frameFlags|0x40` y `object+0x1ac=1`, el resolver original alcanza geometría y daño 120 antes del callback nulo. La apertura es sintética; estado vulnerable auténtico y `+0x1ac` siguen pendientes. Ver [ITERATION115.md](ITERATION115.md).
- **Iteración 2.16:** constructor base original `0x46b7f0` se ejecuta para el defensor y produce `object+0x1ac=1`; la limpieza `0x46b9a0` lo pone a cero. Con ese estado legítimo y frame PAT neutral `0x31` el resolver no daña; al abrir únicamente bit `frameFlags&0x40`, el PE calcula 120. Falta hallar la pose PAT vulnerable auténtica. Ver [ITERATION116.md](ITERATION116.md).
- **Iteración 2.17:** el escaneo de Remilia PAT encuentra 762 poses con hurtboxes y `frameFlags&0x40`; acción602/seq0/frame0 es neutral de pie (`0x3041`). Al cargar esa pose PAT auténtica en objeto creado por el constructor original, `0x47ce20` aplica 120 de daño (1000→880) sin override. Sigue como fixture la selección del frame y su posición; falta llegar ahí por la actualización natural, callback visual y reacción/hitstop. Ver [ITERATION117.md](ITERATION117.md).
- **Iteración 2.18:** acción602 del defensor llega mediante setter `0x464930`, initializer `0x59aaa0` y pose selector `0x464ae0`; el frame PAT se selecciona dentro del PE y `0x47ce20` aplica 120 sin modificar flags ni descriptor. El setter sigue siendo llamado directamente desde harness; faltan input/update end-to-end, callback visual, reacción/hitstop. Ver [ITERATION118.md](ITERATION118.md).
- En la fixture x86 se completó el layout PAT posterior a los 40 bytes de traits: byte reservado + `frameFlags` + `attackFlags`. Remilia 801 seq.0 publica `0x01000000/0x0041040e`; ahora el fixture escribe esos campos en `CharacterFrameData+0x4c/+0x50`, que son filtros del pair dispatcher. La metadata y la prueba de daño contrastan estos valores; ejecutar `0x47ce20` con manager/listas válidas sigue siendo el paso inmediato.
- **Iteración 2.13:** el dispatcher `0x7879da` de 801 seq.0 genera otro 801 cada tres frames por `vtable+0x44`; 19 requests salen del padre inicial durante sus 55 ticks y seis secundarios siguen activos tras su retiro. Se fijaron las firmas y la traza dinámica en tests. Sigue pendiente pair dispatch y daño. Ver [ITERATION113.md](ITERATION113.md).
- **Iteración 2.12:** corregida la interfaz secundaria del manager (`LIST-4`). El update indirecto por slot4 corre 55 ticks desde el objeto recién creado, llega a `+0x34c=0` y elimina su nodo; quedan seis otros 801 activos y se observaron 19 retornos adicionales de factory. El crecimiento de objetos y el daño de parejas aún requieren explicación. Ver [ITERATION112.md](ITERATION112.md).
- **Iteración 2.11 (supersedida):** al poner la factory sobre `LIST` en lugar de `LIST-4`, el iterador recorría la lista incorrecta y despachaba `ESI=1` en el tick18. La corrección está demostrada en Iteración 2.12. Ver [ITERATION111.md](ITERATION111.md).
- **Iteración 2.10:** el hijo 801 de la factory original y una hurtbox neutral Remilia se pasan al helper x86 `0x47a5b0`; hay contacto a distancias 0/40/60 y no a 70/71/100/200. Transformaciones de caja corren desde PE, pero callback, fase completa del manager y daño siguen fuera. Ver [ITERATION110.md](ITERATION110.md).
- **Iteración 2.09:** la factory original crea 801/seq.0 con 20 poses en `(403,360)`; sync publica una hitbox PAT y el update original corre 60 ticks sin error. Sigue vivo al tick 60. Callback/servicios externos, pareja, colisión y daño aún sin verificar. Ver [ITERATION109.md](ITERATION109.md).

- Probe x86 ejecuta setter/initializer y temporizador PAT originales: `0x438c60` avanza subframe y `0x464b70` cambia pose cada 4 ticks; el handler llega a pose4 y pide 801 en el tick 16. Ambas orientaciones dan spawn `(403,360)`/`(237,360)`. Callback/manager externos y gates previos siguen en fixture; no prueba colisión ni daño. Suite Python 40/40. Ver [ITERATION108.md](ITERATION108.md).

## Iteración 2.07: CRT y siguiente enlace Remilia 412 → 801
- El probe permite hasta 18 updates originales de Remilia 801 en el fixture controlado; `+0x34c=0`, seq.0 sincroniza una caja PAT y seq.1 no tiene caja.
- El callsite desensamblado calcula el spawn 801 desde posición/facing del owner; `0x464980` indexa `object+0x164[EBX]`. Falta capturar esos valores al ejecutar el estado `+0x140==4` y probar callback, colisión y daño. Ver [ITERATION107.md](ITERATION107.md).

- Se ejecuta el inicializador CRT original `0x824bfa` con contratos de host controlados para TLS/FLS y heap; el índice inválido `0xffffffff` y la terminación CRT desaparecen.
- El factory crea action 801/seq.1 con dos poses. El dispatcher original completa 18 ticks hasta `+0x34c=0`; seq.0 sincroniza una caja ofensiva y seq.1 ninguna. No se demuestra manager cleanup ni impacto. Ver [ITERATION106.md](ITERATION106.md).
- Suwako 808 conserva ocho ticks y la suite Python pasa 39/39. Próximo: alimentar el setup real de Remilia 412 y seguir el primer contacto.

## Iteración 2.05: imports del CRT y fixture del objeto 801

- La primera hipótesis atribuyó la terminación a inicialización CRT y un stub experimental de contenedor; el seguimiento posterior corrigió ambos puntos. Ver [ITERATION105.md](ITERATION105.md).

## Iteración 2.04: factory x86 del objeto Remilia 801

- Factory e initializer originales crean action 801/seq.1; `0x465e10` publica una hitbox al seleccionar seq.0 y ninguna en seq.1. El update avanza tres ticks; el cuarto intenta `KERNEL32!TlsGetValue` por IAT `0x857190`, cuyo puntero sin resolver (`0x8a896c0d`) provoca la excepción. Ciclo de vida/daño aún no verificados.
- Se generalizó el harness y la regresión Suwako 808 completa ocho ticks. Falta preparar los servicios del tick 4 y alimentar el setup/seq que usa Remilia 412. Sin cambio Vita/VPK. Ver [ITERATION104.md](ITERATION104.md).

## Iteración 2.03: acción y hitboxes del objeto 801

- El ID 801 resuelve por las tablas originales a initializer `0x7991a5` y update `0x7879da` (grupo 1 en ambos mapas). El PAT efectivo de Remilia define 801: seq.0 tiene 20 poses con daño 120 y caja ofensiva en todas; seq.1 no daña; seq.2 tiene 20 poses con daño 100 y caja ofensiva en todas.
- 801 ya es un atacante confirmado por datos; queda probar su factory/update/ciclo de vida y si sus contactos explican el 2C 412/750. Sin runtime/VPK nuevo. Ver [ITERATION103.md](ITERATION103.md).

## Iteración 2.02: contrato del objeto 801

- La llamada `0x46eb30` desde el handler especial de action 412 es el wrapper de `Player::createObject`: solicita el objeto 801 con coordenadas derivadas del jugador/facing. Después se invoca el callback indexado `0x464980`.
- El vínculo de ese objeto con los 750 de daño de la pose PAT aún no se ha probado. Sigue el initializer/update/collision de 801 hasta un primer impacto comparable. Sin cambios de runtime ni VPK. Ver [ITERATION102.md](ITERATION102.md).

## Iteración 2.01: corrección del dispatch de Remilia 412

- Corrección importante: la Iteración 1.95 no siguió la rama previa para acciones >300. El dispatcher real envía action 412 por tabla especial a `0x58cce7`, no al update genérico `0x483f40`.
- En el subestado `+0x140 == 4`, el handler configura datos y solicita el objeto ID 801 mediante `0x46eb30`, después invoca un callback indexado. Es un candidato concreto para explicar el ataque PAT 750, todavía sin vínculo dinámico probado con el daño.
- Próximo: identificar ese callback y ejecutar la secuencia natural hasta el primer contacto; no hay runtime/VPK nuevo. Evidencia y límites: [ITERATION101.md](ITERATION101.md).

## Iteración 2.00: gate diferencial de Remilia 2C

- Dos corridas x86 desde `0x59dd97`: con lock 0/BX 0 entra a 412 y selecciona PAT seq.0 (12 poses); con lock 0/BX 1 rechaza 412, consulta fallback 410 y no alcanza setter 412.
- La sonda ejecuta `0x489610` y el setter/reset/init cuando aplica; PAT/pose siguen controlados y gates anteriores se omiten. Reporte ignorado: `artifacts/kernel/remilia-412-input-gate.json`. Ver [ITERATION100.md](ITERATION100.md).

## Iteración 1.99: moveLock(412) y setter desde handler

- La sonda entra en `0x59dd97`, ejecuta el lookup original `0x489610`, registra la clave 412 y el retorno de lock 0; la rama alcanza el setter, reset PAT e initializer original. Resultado: action 412, seq.0, pose 0, 12 poses.
- PAT lookup y callback pose/render son controlados; los gates previos del handler se saltan. No es todavía una entrada natural ni combate. Reporte ignorado: `artifacts/kernel/remilia-412-input-gate.json`.
- Siguiente: probar rechazo por lock/recurso y rastrear update/factories/daño. Ver [ITERATION99.md](ITERATION99.md).

## Iteración 1.98: setter de Remilia 2C hasta PAT seq.0

- La ruta de input `0x59dd59–0x59ddb1` consulta moveLock(412) y, si los gates pasan, usa el setter virtual `0x464930`. La sonda ejecuta `0x464930 → 0x438ca0 → 0x465370 → 0x59aaa0 → 0x59ad64 → 0x4636b0`.
- Resultado: acción 412, seq.0, pose 0, 12 poses PAT; reset de estado/contadores. La búsqueda PAT y la callback de pose/render son controladas; la prueba inicia después de los gates de input y no es combate. Reporte ignorado: `artifacts/kernel/remilia-412-action-setter.json`.
- Siguiente: ejecutar el gate de moveLock y el update x86 completo de forma instrumentada para encontrar el productor de contacto/daño. Ver [ITERATION98.md](ITERATION98.md).

## Iteración 1.97: dispatch dinámico de action 412

- La sonda ahora ejecuta el selector original `0x59ab40` con action 412; un hook confirma el salto a `0x59ad64` por el mapa/jump table. `0x4636b0` y el cuerpo también corren desde el PE; todos los campos centinela esperados quedan en cero.
- Reporte ignorado actualizado: `artifacts/kernel/remilia-412-initializer.json`. Aún falta el caller de input/setter, update completo, factories y primer impacto. Ver [ITERATION97.md](ITERATION97.md).

## Iteración 1.96: ejecución del initializer Remilia 412

- Se añadió `tools/x86_remilia_412_initializer_probe.py`: el mapa/jump table original resuelve action 412 a grupo 15 y `0x59ad64`; Unicorn ejecuta el cuerpo y `0x4636b0` del PE.
- La sonda comprueba resets de `+0x190`, `+0x7D0/+0x7D2/+0x7D6/+0x7D8` y floats `+0xF4..+0x100`. Reporte ignorado: `artifacts/kernel/remilia-412-initializer.json`.
- El initializer solo limpia estado/counters y movimiento, sin daño ni spawn visible. Falta ejecutar el caller/entrada a 412 y rastrear el origen real del contacto. Ver [ITERATION96.md](ITERATION96.md).

## Iteración 1.95: dispatcher común de Remilia y action 412

- El update `0x5879a0` enruta acciones mayores que 226 al método genérico `0x483f40`. Este último solo despacha explícitamente actions 50–181; 412 termina en el epílogo por defecto `0x484be3`.
- El tramo común no muestra rama directa para 412 ni llamada directa a los callbacks `0x4649b0` de secuencias 2/3. Esto es evidencia estática, no excluye vtables, objetos secundarios ni otros managers.
- Exportaciones locales ignoradas: `artifacts/kernel/remilia-update-full.tsv`, `remilia-update-dispatch-tail.tsv`, `remilia-generic-action-update.tsv`, `remilia-generic-action-default.tsv`. Siguiente: trazar setup/update desde initializer 412 `0x59ad64` e identificar spawn/callback runtime. Ver [ITERATION95.md](ITERATION95.md).

## Iteración 1.94: PAT Remilia 412 sincronizado por x86 original

- `tools/x86_remilia_412_box_sync_probe.py` instala pose5 `attackBa002.bmp` desde th123c.dat y ejecuta `0x465e10` seguido del helper de pares `0x47a5b0` en Unicorn sobre el PE fijado por hash.
- Resultado: daño 750/duración 3; 1 collision box, 4 hurt boxes, 0 attack boxes; el sync publica hit 0/hurt 4 y un puntero collision. Con cuatro hurtboxes en el defensor, `0x47a5b0` retorna 0 contacto. Las conversiones geométricas se interceptan como copias; no es match nativo ni prueba de aplicación del daño.
- Reporte ignorado: `artifacts/kernel/remilia-412-box-sync.json`. Siguiente: rastrear el emisor/callback que aplica el daño o crea geometría ofensiva adicional durante el update de Remilia 412. Ver [ITERATION94.md](ITERATION94.md).

## Iteración 1.93: callbacks de Remilia fuera de 412/seq.0

- Las llamadas a `0x4649b0` en `0x591f6b/0x591ff9` y `0x59243f/0x592498` están en rutinas que guardan secuencias 2 o 3; no coinciden con Remilia 412 seq.0 pose5/750.
- Sus funciones `0x591c24` y `0x5920d8` aparecen dentro de un bloque tipo tabla en `0x59a2c8` (corregido desde `0x5992c8`). El barrido del PE no halló referencia absoluta a ese bloque; consumidor y asociación action→índice faltan. No afirmar que sea tabla de action 412.
- Siguiente: buscar referencia computada/consumidor y contrastar la ruta 412 en x86. Sin cambio de runtime/VPK. Ver [ITERATION93.md](ITERATION93.md).

## Iteración 1.92: candidato de callback de daño en Remilia

- Se localizaron cinco callsites directos de `0x4799b0`; cuatro están en el flujo de colisión/respuesta. `0x47b1d0` también se invoca desde el wrapper `0x4649b0` (`0x4649d2`), que recibe personaje, rival y parámetros de daño.
- Hay 25 referencias directas a `0x4649b0`, incluidas cuatro en rutinas de Remilia (`0x591f6b`, `0x591ff9`, `0x59243f`, `0x592498`). Son candidatas a ruta especial, pero todavía no se relacionan con action 412; los ejemplos muestran estados/temporizadores y daños distintos a los 750 de PAT.
- Se añadieron `0x4649b0` y `0x47b1d0` a `ExportKernel.java`. Próximo: determinar si alguna condición/callback es alcanzable desde 412 y comparar frame/daño con PAT. Sin cambios de runtime/VPK. Ver [ITERATION92.md](ITERATION92.md).

## Iteración 1.91: respuesta de pares y límite de Remilia 2C

- `0x47c770` llama a `0x47a040` para grab (`attackFlags & 0x80`) o `0x47a5b0` para hit-vs-hurt normal; solo después de un contacto geométrico evalúa `0x47b5d0`, `0x47b490`, `0x47c590` y `0x47aa50`.
- La cadena posterior consulta flags/estado y termina procesando daño del frame, pero no produce hit boxes. Remilia 412 tiene flags `0x00204002`, `attackBoxes` vacío; esta ruta sigue sin explicar los 750 del PAT.
- Desensamblado ampliado fijado al hash del PE en `artifacts/kernel/remilia-damage-route-followup.tsv` (ignorado). Se añadieron las cuatro rutinas posteriores a los objetivos de `ExportKernel.java`.
- Siguiente: hallar el productor/callback alterno o la ruta real del descriptor 412; no portar una caja supuesta. Sin cambio de runtime/VPK ni nueva corrida Vita3K. Ver [ITERATION91.md](ITERATION91.md).

## Iteración 1.90: geometría PAT de Remilia 2C

- La pose dañina 412/seq.0/pose5 declara 750 de daño, flags `0x00204002`, cero `attack_boxes` y una `collision_box` `[-20,-155,20,-1]` en el PAT efectivo de th123c.dat.
- Vtable: `initializeAction` 412 → `0x59ad64` (resetea estado/counters, sin spawn); `update` `0x5879a0` no tiene rama directa 412; no se atribuye todavía semántica ofensiva a `collision_box`.
- `0x465e10` lee `CharacterFrameData+0x54`, transforma la caja con `0x4640b0`, la guarda en `object+0x310` y publica `object+0x348`. La semántica posterior de ese puntero sigue sin identificar.
- El resolutor `0x47c770` usa `object+0x348` en la rama `grab` (bit `0x80`) y `0x47a5b0` para hit-vs-hurt en la ruta normal. Remilia 412 tiene byte bajo `0x02`; su vector `attackBoxes` sigue vacío, por lo que falta explicar el daño registrado.
- `ExportKernel.java` añade `0x4640b0/0x464200`, `0x47c770` y `0x47a040`. Siguiente: rastrear el productor de attackBoxes/camino alterno de Remilia 412 y validar el primer impacto. Sin cambio de runtime/VPK.
- Ver [ITERATION90.md](ITERATION90.md).

## Iteración 1.89: handler x86 de Remilia 2C

- Regeneré CFG de los 20 handlers desde el PE fijado, span `0x8000`; Remilia `0x0059c010` consulta lock 412 y despacha 2C. La salida analítica permanece local/ignorada.
- El desensamblador ahora resuelve Capstone desde `local/python-deps`. La búsqueda bruta por `[reg+0x50]` no identifica por sí misma lectores de `CharacterFrameData::attackFlags`; no se interpretó el flag ni se cambió runtime.
- Siguiente: callback de update de 412 y ejecución de `0x465e10` con su descriptor PAT real en Unicorn, luego resolver la respuesta de combate.
- Ver [ITERATION89.md](ITERATION89.md).

## Iteración 1.88: exportación reproducible de sincronización PAT

- Se añadió `tools/disassemble_pe_windows.py`, fijado al SHA-256 del ejecutable original. El desensamblado local de `0x465e10`, `0x47a5b0` y `0x47a740` confirma que `frameFlags` (`+0x4c`) controla la publicación de buffers transformados; no interpreta `attackFlags` (`+0x50`).
- `ExportKernel.java` incluye esas rutinas como objetivos Ghidra. La evidencia está en `artifacts/ghidra/attack-flag-pipeline-disassembly.tsv`, ignorada por Git.
- Siguiente: reconstruir el productor de CharacterFrameData para Remilia 412 y probar vector/colisión mediante el harness x86; aún sin cambio de runtime/VPK.
- Ver [ITERATION88.md](ITERATION88.md).

## Iteración 1.87: inventario PAT de `attack_flags`

- Agregué un resumen reproducible de poses con daño y flags de ataque no nulos. En el roster aparecen 1,987 combinaciones personaje/acción/índice/flags con cajas explícitas (7,129 poses), 1,442 sin cajas (4,891 poses) y 164 valores raw sin caja.
- Remilia 412:0 tiene 750 de daño y flags `0x00204002`; 416:0/1 tienen 800 y `0x0000240a`. Alice 418:0 tiene `0x00088404` sin caja en el PAT del jugador, coherente con la ruta de objeto 849. El reporte no interpreta los bits.
- `tools/summarize_pat_attack_flags.py` y la prueba sintética pasan con Python estándar. Reporte: [PAT_ATTACK_FLAGS.md](PAT_ATTACK_FLAGS.md).
- No se encontró `analyzeHeadless.bat` para ejecutar Ghidra; solicité la ruta de instalación. No cambié la simulación de colisión hasta recuperar las reglas x86 de los flags.

Ver [ITERATION87.md](ITERATION87.md).

## Iteración 1.86: medición natural B/C por personaje

- La sonda ahora intenta acciones B/C terrestres, aéreas y dash desde el spawn normal, con cinco distancias y ventanas de salto; valida daño contra la pose PAT directa o el objeto dueño. Los objetos también incrementan el contador B/C de la acción que los generó. El inventario detecta variantes PAT dañinas, pero el selector provisional del runtime sigue limitado a dash 408/418; otros selectores faltan.
- Vita3K SDL schema31 pasó 600 frames; siguen verdes BG34, PAT/sprites/tarjetas 20/20 y A natural 20/20. B natural conectó 14/20 (`0x0EBBB6`); C conectó 15/20 (`0x0BF9B7`). Estas máscaras son telemetría, no gates de completitud.
- B pendiente: Reimu, Alice, Remilia, Udonge, Tenshi y Cirno. C pendiente: Alice, Remilia, Suika, Udonge y Utsuho. Remilia 412/416 y varios otros ataques conservan daño PAT expresado en flags sin cajas explícitas; Alice 418 usa el objeto 849 y aún no conecta con la aproximación probada.
- VPK: [Touhou123Vita-bc-natural-final.vpk](../artifacts/Touhou123Vita-bc-natural-final.vpk), 98,275 bytes, SHA-256 `493f2294ca58ae21357ab6349091119d1e81ce12e6a2afbbe912de6854943a47`. Diagnóstico: [roster-bc-natural.tsv](../artifacts/roster-bc-natural.tsv); corrida: [vita3k-result.json](../artifacts/vita3k-result.json).
- Siguiente: recuperar selección real de variantes y colisiones `attack_flags` desde el ejecutable x86, empezando por Remilia 412, y validar una pelea con IA/guardia y trazas comparables.

Ver [ITERATION86.md](ITERATION86.md).

## Iteración 1.85: ataque A natural para todo el roster

- El auto-test schema30 ejecuta cada PAT desde el spawn normal `(190,450)` contra Cirno quieto: aproxima al jugador con 130 updates de `IN_RIGHT`, intenta las entradas A terrestres disponibles y espera a que conecte usando únicamente `fight_step`, PAT y sus hitboxes/hurtboxes. No acomoda manualmente las coordenadas para esta medición.
- Los 20 personajes conectaron al menos una ruta y el daño coincide con la pose de impacto: `roster_a_natural_attack_mask=1048575` (`0xFFFFF`). Se mantienen también los 20/20 casos de geometría controlada. La prueba principal de 600 frames registra `a_hits=1`, B=1 y C=2; el gate y runner exigen ambas máscaras completas y el hit A del combate.
- VitaSDK recompiló el VPK y Vita3K SDL aislado pasó schema30/600 frames. Paquete: 96,291 bytes, SHA-256 `1a1461e7197ac65694ce45f01f45f3460288301bd7029c27a1b072300372fd08`. Evidencia visual: [fight-natural-a.bmp](../artifacts/screenshots/fight-natural-a.bmp).
- Límite: cada luchador se enfrenta a Cirno inmóvil en la sonda, por lo que no prueba 400 matchups, IA, defensa ni paridad temporal con TH123. La pelea mostrada sigue siendo prototipo; faltan skills/objetos para el roster, sistemas globales y los otros escenarios. Siguiente: medir B/C y entradas de dash por personaje, luego matchups y guardia con trazas comparables al original.

Ver [ITERATION85.md](ITERATION85.md).

## Iteración 1.84: impacto A con aproximación normal

- Ajusté la secuencia de autoprueba para recorrer distancia con `IN_RIGHT`, dejar la CPU inmóvil y pulsar A con `IN_MELEE`; el combate no recoloca a los luchadores para ese impacto. La ejecución de `fight_step` registró `a_hits=1`. El runner y el gate Vita ahora exigen ese hit.
- Vita3K SDL aislado pasó 600 frames con las regresiones actuales y la máscara PAT A 20/20 (`0xFFFFF`). Se guardó [fight-natural-a.bmp](../artifacts/screenshots/fight-natural-a.bmp), capturada durante el intercambio, con el rival en reacción y su barra de vida reducida.
- VPK: `artifacts/Touhou123Vita-natural-a-auto.vpk`, 96,273 bytes, SHA-256 `ef4ca60440f5ab7d5607e182884517dac4299578b15a0349bd93ec1e87ac27f8`.
- Límite: la aproximación se prueba contra CPU inmóvil, con un solo matchup Marisa/Cirno y controles deterministas. No valida IA, guardia, paridad de timing PC, la respuesta completa de hit, ni el roster en combates naturales. Siguiente: variar matchups y entradas sin recolocación, medir el daño A frame a frame contra PC y recuperar estados de guardia/cancelación.

Ver [ITERATION84.md](ITERATION84.md).

## Iteración 1.83: gate de ataque A con PAT de todo el roster

- Agregué un probe al auto-test que recorre los 20 PAT cargados y prueba entradas de ataque terrestre A (acciones 300/302/303/304/330). Usa sus cajas PAT de ataque y hurt, deja que `fight_step` recorra la animación y solo cuenta la ruta si el combate registra un impacto A y el daño coincide con el valor de la pose que golpeó.
- La corrida fresca Vita3K SDL schema29 pasó 600 frames con `roster_a_attack_mask=1048575` (`0xFFFFF`), es decir 20/20. El build y el runner ahora exigen esa máscara completa. VPK: 96,162 bytes, SHA-256 `c4fb9924259113e14ba0cdb9f39691c2fa03dc6398b16c335f7cee1523936605`.
- Límite importante: el probe coloca los luchadores según la geometría PAT para garantizar la intersección; demuestra que cada PAT ofrece al menos una ruta A seleccionable que aplica su daño, pero no demuestra que el jugador conecte naturalmente en una partida. En la pelea principal del escenario automatizado `a_hits` sigue en 0 mientras B/C dan 1/1. Guard, cancelación, timing original y paridad por personaje siguen abiertos.
- Se conservan 20/20 PAT/sprites/tarjetas, cero fallos de textura, 148 texturas y la regresión BG34. El siguiente trabajo es medir y corregir encuentros A/B/C naturales con spacing y tiempo de animación trazados, luego extender la misma comprobación a ataques aéreos, skills y objetos del roster.

Ver [ITERATION83.md](ITERATION83.md).

## Iteración 1.82: rebuild fresco y regresión Vita3K

- `tools/build-vita-native.ps1 -Output artifacts/Touhou123Vita-current-auto.vpk -AutoTest` compiló desde las fuentes actuales con VitaSDK. VPK: 95,972 bytes, SHA-256 `d361adfe700db32c6789d8eb2288d4c39d723c8d020bc3a4b92ed9b22b830318`.
- `tools/vita3k-test.ps1` ejecutó ese hash en Vita3K SDL aislado, con evidencia nueva de 600 frames y schema 28. Pasaron menú/galería/práctica/combate, prueba de salto, dash, rutas de objetos y skills 560/540/565/505. El roster reportó 20/20 PAT, sprites y tarjetas, máscaras completas y cero fallos de textura; se decodificaron 148 texturas. BG34 cargó 30+30 tiles, cuatro assets estáticos y 30 objetos animados.
- La captura de combate muestra dos sprites y HUD funcionales. Esto valida una regresión del prototipo; no demuestra el combate completo ni la paridad con el original. La prueba es automatizada, solo cubre BG34, reportó `a_hits=0`, y los 20/20 representan carga de recursos, no 20 personajes jugables. Sigue pendiente integrar DAT de forma distribuible, roster/mecánicas completos, los otros 23 escenarios y su lógica. No incluye recursos comerciales en el VPK.
- Artefactos locales ignorados por Git: `artifacts/Touhou123Vita-current-auto.vpk`, `artifacts/vita3k-result.json`, capturas en `artifacts/screenshots/`. La iteración 808 de análisis x86 no se añadió al runtime.
- Siguiente: hacer que la galería cubra todas las secuencias/poses por personaje, y reconstruir por separado el pipeline de escenario desde DAT→layout→transformación→colisión; mantener el combate validado como baseline mientras se captura la respuesta de hit/daño original.

Ver [ITERATION82.md](ITERATION82.md).

## Iteración 1.80: sincronización original de bounds 808

- Se corrigió el layout: `BoxInfo` tiene conteo hit en `+0x1cb` y hurt en `+0x1cc` (no `+0x1ce/+0x1cf`); hurt array `+0x1d0`, hit array `+0x220`. El PE confirma que `setPose` solo selecciona descriptor PAT; la sincronización está en `0x465e10`, invocada por el manager en `0x47d1a7`.
- Factory original + frame vectors derivados del PAT bajo Unicorn: seq.0 queda con hurt/hit 1/1, bounds `[-44,-44,44,44]` y `[-32,-32,32,32]`; seq.1 con daño PAT 150 queda sin collision/hurt/hit boxes activas. La sonda vuelve a seq.1 antes del fade de 32 ticks.
- `0x465e10` publica cajas PAT en el objeto 808; la ejecución nativa alcanzó dos veces `0x4640b0` y convirtió los bounds locales a mundo. La llamada en `0x47d1a7` pertenece a una ruta del manager cuyo papel de colisión no está establecido. No es aún prueba de colisión ni daño. Las pruebas enfocadas de esta iteración pasan; no cambia runtime ni VPK. Próximo: seguir CFG/traza hasta resolver el cálculo del impacto/lifecycle. Ver [ITERATION80.md](ITERATION80.md).

## Iteración 1.81: consumidores del pipeline de cajas

- Se trazó el manager desde `0x47d5c9/0x47d5d0` a las fases `0x47cb70` y `0x47ce20`. El helper `0x47a5b0` recorre el conteo hit `+0x1cb` y el array `+0x220` contra el conteo hurt `+0x1cc` y array `+0x1d0`; usa pruebas de cajas rotadas `0x47a110` o AABB `0x479e10`. `0x47a740` recorre hurt contra hurt.
- La fase de pares de personajes despacha a `0x47ca70/0x47c990`; la evidencia estática no demuestra todavía qué ruta del action 808 ejecuta primero ni el detalle del daño/guard/hitstop. Contratos de bytes del PE fijados en `tools/analyze_object_motion.py` y prueba Python correspondiente.
- Siguiente: ejecutar un par controlado con dos objetos y PAT 808 bajo Unicorn, registrar la llamada al detector/respuesta y localizar el handler que consume `seq.1` sin PAT boxes. El runtime Vita y VPK no cambiaron.

## Iteración 1.79: cierre limpio del probe y corrección de gate de acción

- El probe 808 ahora detiene el dispatcher cuando `+0x34c` llega a cero. Reproducido con EXE/DAT locales: 32 callbacks, alpha 7, campo terminal 0 y sin subdesbordamiento artificial. No afirma retiro dinámico: el campo `manager_removed_object` queda explícitamente `null` porque esta sonda todavía no invoca la lista del manager.
- El helper `0x48ce90` llamado desde seq.0 quedó reclasificado: no consulta geometría/hitbox. Comprueba el action del owner; para el rango `0x32..0x95` emite efectos `0xc8/0xc9` según los dos contadores y devuelve true, suprimiendo el split. La llamada 808 es `(0,0,3)`, por lo que puede emitir tres efectos `0xc9`. El helper de suelo es aparte, `0x4397f0`.
- Analizador y tests fijan esta lectura contra bytes del PE. Suite completa: 37/37. Sin cambio de runtime/VPK; sigue como baseline la Iteración 1.77. Próximo: preparar manager/lista/handle map válidos para verificar el retiro dinámicamente y localizar la ruta real de hitbox/impacto de seq.1.

## Iteración 1.78: consumidor del campo de terminación 808

- La vtable `0x85f28c`, slot 4, despacha al manager `0x633ce0`. Si el estado del oponente permite actualizar, llama al iterador `0x633c10` con el callback común `0x4ae380`; este ejecuta el virtual del objeto en `vtable+0x28` y después lee `object+0x34c`.
- Cuando el campo queda en cero, el iterador obtiene `object+0x350`, retira el handle con `0x45ed10`, desenlaza/libera el nodo de lista y decrementa el tamaño. El campo es por tanto una señal de retiro del manager, no la vida útil ni el HP del proyectil.
- El contrato está fijado por bytes del EXE de hash conocido y cubierto por el analizador y sus tests. La pasada dinámica integrada todavía está pendiente: el harness no debe llamar otra vez al handler tras el cero ni declarar válida una corrida con lista/handles inválidos. Sin cambios de runtime, el VPK baseline de la Iteración 1.77 sigue vigente.
- Próximo: lograr la inicialización pool/handles del manager y el factory bajo el mismo estado, invocar el slot 4 a través de una lista válida y registrar que el tick que reduce `+0x34c` a cero también retira el nodo. Después medir qué bounds/cajas recibe la colisión en seq.1 y avanzar a daño.

## Retoma y baseline reproducible (2026-10-16)

- Revisión del chat **Configurar Touhou75Vita**: aportó una plantilla de inventario de instrucciones/CFG, cobertura cuantitativa, contratos ABI y diagnósticos explícitos. Su smoke test fue sintético y no compiló un VPK validado; no reutilizar su runtime, renderer, imports ni offsets para TH123. La instrumentación de corridas frescas ya vive en el runner TH123.
- Suite Python actual: 37/37 aprobada. El probe `tools/x86_suwako_808_factory_probe.py` volvió a ejecutar el constructor/lista, factory 808 y dispatcher sobre el EXE fijado por hash y DAT local; factory completado, objeto en `(300,400)`, acción 808, seq.1, alpha 255 y `+0x34c=1`. Los servicios de heap, trigonometría, RNG, render y colisión/suelo siguen controlados por el harness; no es una traza de combate nativa.
- VPK auto-test recién recompilado desde las fuentes actuales: [Touhou123Vita-TH75-review-current.vpk](../artifacts/Touhou123Vita-TH75-review-current.vpk), 95,972 bytes, SHA-256 `c360c89d923e554bcff0cccf7c7ecb94164d3825f84958bcf7314e30daae9129`. Vita3K SDL aislado schema28 pasó 600 frames: lucha, recursos PAT/tarjetas 20/20, BG34 (30+30 tiles, 4 assets estáticos, 30 objetos), dash y hits A/B/C, skills 560/540/565 y fases de 505; 148 texturas y cero fallos del roster.
- Próximo gate de reconstrucción: inicializar e iterar el manager original bajo Unicorn, encontrar dónde consume `object+0x34c`, y probar con esa capa el retiro/reuso; después seguir bounds/cajas e impacto de los hijos 808. No portar una mecánica nueva hasta cerrar esos contratos. La prueba Vita3K es el baseline de regresión y no incluye aún esa ruta 808.

## Auditoría del objeto Suwako 808 y reutilización TH75

**Iteración 1.76 (corregida por 1.79):** el CFG del handler 808 (219 instrucciones alcanzables desde `0x788d3e`) incluye el helper de estado del owner `0x48ce90` y la consulta de suelo `0x4397f0`, pero no el adaptador geométrico `0x438fc0`. El primero comprueba rango de action y puede emitir efectos `0xc8/0xc9`; no detecta colisión geométrica. El campo raw `+0x34c` baja a cero con el fade; la Iteración 1.78 localizó su consumidor estático en el manager. El hijo seq.1 no trae cajas PAT explícitas; sigue pendiente localizar su hitbox/impacto. Ver [ITERATION76.md](ITERATION76.md) y [ITERATION79.md](ITERATION79.md).

La comparación con Touhou75Vita reforzó el uso de contratos, límites de cobertura y pruebas por evidencia; no se copió runtime genérico. Al revisar el despacho real del PE 12.3 se corrigió `tools/analyze_object_motion.py`: el action update 808 es `0x00788d3e` (grupo 5), no `0x00789f9d`; el update 989 es `0x00797884` (grupo 46). El objeto 808 inicia velocidades en cero y resta 0.2 de `vy`; seq0 suma 0.075 a `object+0x11c`, seq1 suma 0.005 al mismo escalar auxiliar. El oracle Unicorn ejecuta el handler original, captura split en dos hijos, custom data angular/radial y guards sin split. El initializer pasa ángulo/magnitud a una tabla trigonométrica y la secuencia 1 consume una componente X controlada coherente con `sin(ángulo)*magnitud`. Falta conectar la llamada factory con el estado inicial de los hijos, seguir constructor/update/terminación y contrastar una traza nativa antes de corregir runtime (`vx=4`, vida 90 siguen provisionales). Ver [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md), [ITERATION65.md](ITERATION65.md) y [ITERATION66.md](ITERATION66.md).

## Iteración 1.64: offsets PAT de spawn de Suwako 418

- La auditoría del constructor confirma que el descriptor PAT de `0xa8` bytes se pone a cero; el loader `004679e0` carga `ox/oy` en `+0x3c/+0x40`, no escribe `+0x98/+0x9c`, y el constructor de copia preserva esos dos campos en cero. El spawn 808 original usa offsets cero; corregí el modelo Vita y el fixture, con aserción de posición. Esto separa el anclaje variable del sprite (p. ej. pose 10 `ox/oy=38/178`) de la posición del objeto. Oracle x86 2/2, extractor de 23 poses y VPK auto-test Vita3K SDL schema28/600 frames pasan; se vieron 10 spawns, objetos 5/5, roster 20/20 y BG34. VPK: [suwako-418-zero-origin-v2.vpk](../artifacts/suwako-418-zero-origin-v2.vpk), SHA-256 `2b16ce9e6b340015ce2a556ab79c4cd54caf3e4381a9a05cfbb9f914894ee732`. Falta una captura dinámica end-to-end del juego original; trayectoria, ciclo de vida y daño siguen pendientes. Ver [ITERATION64.md](ITERATION64.md).

## Iteración 1.60: fórmula x86 de spawn de Suwako 418

- El PE fijo confirma que `0076f3b4` crea el objeto 808 y calcula `x=Player.x + facing*s32(record+0x98)`, `y=Player.y-s32(record+0x9c)`, con el registro apuntado por `Player+0x158`. El productor y los valores activos de ese registro aún no están identificados; por tanto, el spawn Vita continúa provisional y los `ox/oy` PAT del sprite no se usan como sustituto.
- El analizador ahora fija con firmas los loads, arithmetic y llamada de creación. Suite Python 23/23. Ver [ITERATION60.md](ITERATION60.md).

## Iteración 1.61: spawn Suwako 418 ejecutado en oracle x86

- Un harness ejecuta `0076f3b4` y captura el objeto 808 con valores controlados en `Player+0x158`; prueba ambas orientaciones y offsets negativos. El resultado confirma la fórmula, pero los offsets naturales de la acción siguen pendientes. Suite Python 25/25. Ver [ITERATION61.md](ITERATION61.md).

## Iteración 1.62: descriptor de pose enlazado a Player+0x158

- `00464ae0` selecciona la pose actual desde `[Player+0x15c]+4` con índice `Player+0x140`, stride `0xa8`, y escribe el descriptor en `+0x158`. Ya está resuelto el origen del puntero; falta mapear los campos del PAT que llegan a descriptor `+0x98/+0x9c`. El analizador fija esas instrucciones y el reporte registra el límite. Ver [ITERATION62.md](ITERATION62.md).

## Iteración 1.63: auditoría inicial del parser de pose PAT

- El pseudocódigo Ghidra de `004679e0` no muestra escrituras directas a `+0x98/+0x9c`; la auditoría posterior de constructor, parser y copia resolvió que permanecen en cero para las poses PAT cargadas. Ver [ITERATION63.md](ITERATION63.md) y [ITERATION64.md](ITERATION64.md).

## Iteración 1.58: variantes temporales de Reimu 505

- El handler x86 `0049985C` cambia `Player+0x7D6` al superar la edad de acción 20 y 60; el creador emite respectivamente 3, 4 y 5 proyectiles 811 con patrones de velocidad distintos. El modelo de combate ahora conserva `action_ticks` y selecciona esos tres patrones. Una prueba de regresión ejecuta el PE fijado en ambas orientaciones (6 combinaciones) y verifica cantidad, velocidades e inversión de posición. Las pruebas Vita3K prueban las tres cantidades y todas las velocidades (`skill_104_phase_mask=7`) y además conservan la ruta intermedia: 104→505, 4 objetos, sprite disponible y dos impactos PAT (1100 total).
- VPK auto-test [reimu-card104-505-phases.vpk](../artifacts/reimu-card104-505-phases.vpk), SHA-256 `a291e8ff479f2670350335e8d6990d3e3351eb456023729363c61cd3ddb7f85e`; Vita3K SDL schema28/600 frames pasó con roster 20/20, BG34, dash/B/C y skills 102/103/107 previas. El probe fuerza seq.2/pose.2 para comprobar la emisión; falta todavía una traza original end-to-end para confirmar las transiciones naturales y su reloj. Los tests C pasan comprobación de sintaxis ARMv7 con `-Wall -Wextra -Werror`; no se pudieron ejecutar como binario host porque este Windows no tiene CMake ni compilador host.

## Iteración 1.57: Reimu carta 104/acción 505 con salva PAT 811

- El VPK [reimu-card104-505-verified.vpk](../artifacts/reimu-card104-505-verified.vpk), SHA-256 `fdc48f713f0f353f24d905eb9b75b7b15762d281288976b39392619c285c6089`, compila con VitaSDK y pasa Vita3K SDL schema28/600 frames. El probe confirma activación 104→505, cuatro objetos 811 en seq.2/pose.2, sprite disponible y 1100 de daño total en la posición de prueba (dos impactos de 550). Se conservan roster 20/20, BG34, dash/B/C y las pruebas 102→540 y 107→565.
- El oracle x86 demuestra que el estado interno `Player+0x7D6` selecciona variantes de 3/4/5 proyectiles; su valor 1 produce la salva de cuatro que portamos. El probe Vita coloca directamente la animación en seq.2, por lo que todavía falta comparar por frame cuándo cambian las fases y observar una ejecución natural completa en el original. Revisión y límites en [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md).

## Iteración 1.56: Reimu 107 → 565 con impacto PAT

- La carta 107 activa acción 565; Vita3K entra a seq.1/imagen47 y aplica 450 de daño al concluir seq.0, cuyo PAT suma 64 frames. Reporte fresco schema27/600 frames exige la imagen, acción, secuencia, daño y timing; 63 ticks adicionales más el update de activación. VPK [reimu-card107-565.vpk](../artifacts/reimu-card107-565.vpk), SHA-256 `d80d3172b0cf4650ffa304c2d8efc6c590a2a673acca434846d8fd110610c38c`. Se mantienen 102→540 y 103→560 y las regresiones de roster/escenario/dash/B/C. Falta traza PC real y sistema completo de cartas/efectos. Ver [ITERATION59.md](ITERATION59.md).

## Iteración 1.55: límite temporal PAT de Reimu 540

- El probe cuenta 47 updates después de la llamada de activación (48 incluyendo esa actualización) hasta el primer hit de acción 540. La suma PAT es seq0 22 + seq1 5 + seq2 21 = 48; coincide con Vita3K SDL schema26/600 frames. Hit en seq.3/imagen39, daño 1100. VPK [reimu-skill540-timing.vpk](../artifacts/reimu-skill540-timing.vpk), SHA-256 `e527bd8b088c5915c7b0782efdee9c434c388e2d2adf28ef1dcfbeb7693f1539`. Es consistencia con los datos PAT y los helpers de animación x86 ya ejecutados, no aún una traza de una partida PC end-to-end. Ver [ITERATION58.md](ITERATION58.md).

## Iteración 1.54: impacto PAT de Reimu carta 102/acción 540

- Vita3K recorrió acción 540 desde seq. 0 hasta el hit de seq. 3, imagen 39; aplicó exactamente 1100 de daño y pasó el runner schema25/600 frames. Se eligió la variante ofensiva por contenido PAT y se posicionó el rival dentro de su caja. VPK [reimu-skill540-hit.vpk](../artifacts/reimu-skill540-hit.vpk), SHA-256 `d5607f984c60b0ce1c2959c1a0f42259d1234db4e6a8a2b8a58bbd147ca47507`. Carta 103/560 conserva vuelo/aterrizaje y el resto de regresiones (roster 20/20, BG34, dash/B/C). Timing x86 comparativo, objetos/efectos y otras rutas siguen pendientes. Ver [ITERATION57.md](ITERATION57.md).

## Iteración 1.53: selección terrestre de las 12 skills de Reimu

- El selector terrestre usa la tabla de cartas 100–111 del `handleInputs` original. Carta 102 activa acción PAT 540; el siguiente probe valida impacto real en 540 (Iteración 1.54). Carta 103 → 560 conserva startup, impacto, vuelo horizontal en ambos sentidos y aterrizaje. Las rutas aéreas, mano/costo/consumo y efectos siguen pendientes. Ver [ITERATION57.md](ITERATION57.md) y [ITERATION54.md](ITERATION54.md).

## Iteración 1.52: guard de movimiento horizontal por estado de escenario

- Desensamblé completa `00463550`: `Player+0x571` selecciona entre integración directa sin clamp y una rama con velocidad extra `+0x744`, límites x86 40..1240 y helpers `004393B0/004393F0`. Los gates `+0x196` y `opponent+0x4A8` suspenden la integración. El oracle confirma la rama directa fuera de límites y ambos early-return; Python 22/22. El clamp local 35..605 queda como escala visual aproximada, pendiente de mapear al mundo x86. Ver [ITERATION56.md](ITERATION56.md).

## Iteración 1.50: trayectoria vertical de Reimu 560

## Iteración 1.51: desplazamiento horizontal de Reimu 560

- Se identificó y ejecutó bajo Unicorn el integrador x86 `00463550`: suma la velocidad del personaje y la suplementaria del oponente con `direction` y `speedPower`. El port integra el vx=4.5 de Reimu 560 hacia ambos lados; se agregaron casos C y reporte Vita schema22. Suite Python 20/20 y build VitaSDK pasan. VPK [reimu-air-motion.vpk](../artifacts/reimu-air-motion.vpk), SHA-256 `b2c990c80676ad739c9d2f01db1b9fb8cb9cb546a180b2b4bae90da2bde5a2b6`. Vita3K SDL validó reporte fresco schema22/600 frames: desplazamiento +175, dirección inversa, touchdown seq. 3, roster 20/20, BG34, 30 tiles y objetos. El frontend Qt terminó con -1 antes de arrancar, así que SDL queda como default del runner. Falta speedPower/modificadores y colisiones completas. Ver [ITERATION55.md](ITERATION55.md) y [vita3k-result.json](../artifacts/vita3k-result.json).

- El handler x86 `004A0772` inicializa `vy=14.0` y gravedad `0.75` al entrar a seq. 1/pose 0; el runtime aplica esos valores en cuartos de unidad y recorre el vuelo hasta el touchdown real de la arena. VPK recompilado y Vita3K SDL schema21/600 frames pasa con `skill_air_launch_ok=1`, `skill_landing_ok=1`, seq. 3, roster 20/20 y BG34. SHA-256 `2d4df513bee85c2747fa8c97d3bc8849beb391216974912270e84241e5c78dfd`. La velocidad horizontal x86 `+0xF4=4.5`, orientación, física completa y prueba C host aún faltan. Ver [ITERATION54.md](ITERATION54.md).

## Iteración 1.49: touchdown Reimu 560 portado y validado

- El runtime conserva action 560 cuando Reimu toca el suelo descendiendo y selecciona PAT seq. 3 (dashStop). La condición x86 se probó primero en una sonda con estado sintético y luego la Iteración 1.50 integró el impulso vertical natural. VPK de esta etapa: SHA-256 `d6fd804fe1a1eb46fdc84c3fa4c9c2eebb6bd484219683258c35e4b1acfa95f8`. Ver [ITERATION53.md](ITERATION53.md).

## Iteración 1.48: límite externo de secuencias en bucle

- El puente `00438C60` conecta slot 8 (`nextPose`) con slot 5 (`nextSequence`) solo al recibir fin. Se localizó el dispatcher `action 560` en `00490490 -> 004A0639`: al tocar suelo durante el descenso, `00487EA0` da true y la rama `0049295D` pide `setSequence(3)`. Unicorn ejecuta la mecánica aérea y rama x86 en cuatro casos de contacto/aire/velocidad/flag; suite Python 19/19. `004AC600 -> 0048B000` inicializa muchos campos; el scan de offsets genéricos se descartó por ambigüedad.
- Touhou75Vita: límites, archivo de reportes y timeout ya los cubre el runner Vita3K de 12.3. Su smoke test semántico no se copia; los oráculos x86 del PE 12.3 siguen siendo la autoridad. Ver [ITERATION52.md](ITERATION52.md) y [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md).

## Iteración 1.47: selección de secuencias x86

- Extendí el oráculo para ejecutar `setSequence` (`004652a0`) en los cuatro nodos PAT de Reimu 560. Índices, punteros y conteos de poses coinciden con el fixture (4/7/2/3); Python 17/17. Esto prueba selección explícita, pero no el gate que lleva del loop seq. 2 al recovery seq. 3. No cambia el runtime/VPK. Ver [ITERATION51.md](ITERATION51.md) y `artifacts/x86-skill-sequence-oracle.json`.

## Iteración 1.46: contrato x86 del loop PAT y corrida fresca

- La inspección x86 de `00464b70`/`00464bf0` confirma que una secuencia loop no avanza por tiempo; Reimu 560 necesita una transición externa de seq. 2 a seq. 3. La corrida actual no determina aún qué input/gate realiza esa transición. Se reconstruyó y pasó en Vita3K el probe schema21 (600 frames); Python 16/16. VPK: [Touhou123Vita-skill-sequence-probe.vpk](../artifacts/Touhou123Vita-skill-sequence-probe.vpk), SHA-256 `84983f9df10577f70889d0326a49f2b4b899afc24158d9e40e142c584b0ad37e`. Ver [ITERATION50.md](ITERATION50.md).

## Iteración 1.45: transición secuencial de la skill Reimu 560

- La acción 560 empieza en PAT 0; los primeros 11 updates no causan impacto y el update 12 entra a PAT 1 y golpea con sus cajas/datos de daño. El subtest usa un `Fight` aislado y no altera la regresión normal. El oracle x86 pasó cinco niveles (0–4), todos restablecen la secuencia 0. Python 16/16, build VitaSDK y Vita3K SDL 600 frames schema21 pasan; 20/20 personajes, BG34 y regresiones de dash/B/C se mantienen. VPK automático: [Touhou123Vita-skill-sequence-probe.vpk](../artifacts/Touhou123Vita-skill-sequence-probe.vpk), SHA-256 `54e4c58c34dd8a5be8416afcedba6187f6d8c94605bb76638ef2d5997905ffc2`. VPK interactivo: [Touhou123Vita-skill-demo.vpk](../artifacts/Touhou123Vita-skill-demo.vpk), SHA-256 `35162bf1dbc601887d7245e36c37ea27f87cb368a9d08c33fcc5891831ccf54d`; compilado, sin corrida interactiva separada. La salida de la secuencia en bucle, cancelaciones, costo/mano y el resto de skills continúan pendientes. Ver [ITERATION49.md](ITERATION49.md).

## Revisión de Touhou75Vita

- El checkout local `Vita_Touhou75\Touhou75Vita` está en la iteración 96: selección visible en Vita física; `GetTimeZoneInformation` todavía pendiente de prueba física; combate y renderer GXM no demostrados. Se documentó lo reutilizable como método/instrumentación y WinVita como experimento separado, no como solución de combate 12.3. Ver [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md) y [PORT_REFERENCES.md](PORT_REFERENCES.md).
- En el chat de configuración del repo `Botarguirix/Touhou75Vita`, el smoke test del runtime semántico pasó solo con estado x86 sintético; el VPK documentado inspecciona PE y no ejecuta el juego, y su build VitaSDK quedó sin validar por HTTP 403. Su informe inicial cubre 229,772/699,357 instrucciones enteras/control (32.81%). Transferimos ideas de análisis CFG/cobertura, límites por función y diagnóstico fail-loud; no copiamos el runtime ni sustituimos los oráculos basados en `th123.exe`. Ver [ITERATION54.md](ITERATION54.md) y [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md).

## Iteración 1.44: primera skill Reimu conectada al combate Vita

- Reimu card slot de prueba 103 activa PAT 560; runtime elige su variante ofensiva PAT índice 1. Vita3K SDL schema20, 600 frames: acción 560, imagen 81 y un impacto con cajas PAT. VPK auto: [Touhou123Vita-skill-probe.vpk](../artifacts/Touhou123Vita-skill-probe.vpk), SHA-256 `85fa80fd88f7df8f3addc067d6e5eb413e3139750b28588382658ee78ffcdecf`. VPK interactivo de aquella iteración: SHA-256 `2a9b7967d2ad0c1b022f695deb84e527a531e15b8d8275e0de467ea325647a52` (reconstruido en Iteración 49); Reimu, `L + Circle`. Es una ruta experimental: no están portados mano/costo/descarte/mejora, gates completos, aire ni objetos de las otras skills. CTest host no disponible (`cmake` ausente; WSL con acceso denegado); build VitaSDK y prueba funcional Vita3K pasan. Ver [ITERATION48.md](ITERATION48.md).

## Iteración 1.43: despachos x86 de skills de Reimu ejecutados

- Unicorn ejecutó los switches originales tierra/aire de `handleInputs`: 12 rutas terrestres y ocho aéreas alcanzaron `useSkill` con acción y `actionLock` esperados; evento, mejora y retorno de pila verificados. Ver [ITERATION47.md](ITERATION47.md) y `artifacts/x86-skill-handler-dispatch.json`.

## Iteración 1.42: gate de activación de skills

- Reimu requiere frame cancellable, `actionLock < 51`, spellcard actual/bufferizada, sin confusion ni stopwatch, collisionType permitido, skill card en la mano y costo pagable. `00468e80` x86 pasó ocho casos de mano/costo/weather; el inventario de rutas incluye offsets con hashes SokuLib. Suite Python 15/15. El byte Player `+0x836` sigue sin identificar; runtime/VPK sin cambios. Ver [ITERATION46.md](ITERATION46.md), [ITERATION44.md](ITERATION44.md) y `artifacts/x86-card-activation-oracle.json`.

## Iteración 1.41: contrato x86 de onSkillUpgrade

- Ejecuté `00489660` original con Unicorn para las 12 cartas skill de Reimu: incrementa `skilledSkillLevel` hasta 4, invalida las variantes del mismo slot, consume carta `(0,0,60)`, y crea objetos `0x47`/`0x82+nivel`. Cinco límites de nivel pasaron junto con 12 cartas y stack balanceado. Helpers externos están stubbed. Suite Python 14/14; sin cambio de runtime/VPK. Ver [ITERATION45.md](ITERATION45.md) y `artifacts/x86-skill-upgrade-oracle.json`.

## Iteración 1.40: rutas aérea/terrestre de carta skill de Reimu

- El switch terrestre del handler Reimu mapea las cartas de skill 100–111 a las acciones PAT 500–570; el switch aéreo tiene ocho rutas y distingue qué cartas cambian de acción. Se cruzaron slots, deck inicial y poses/daño directo. Tests Python 13/13 pasan. Guards dinámicos y runtime siguen pendientes; no se generó VPK. Ver [ITERATION44.md](ITERATION44.md) y `artifacts/reimu-skill-card-routes.json`.

## Iteración 1.39: referencia actualizada de Touhou75Vita

- Revisé su chat y documenté `vdpm` como opción para gestionar VitaSDK con un cliente aislado y canales firmados. Su VPK sigue siendo diagnóstico PE y el bootstrap/VPK no fue validado en el entorno por HTTP 403. No se transfirió código; cualquier estructura o semántica se vuelve a demostrar contra `th123.exe`. Ver [ITERATION43.md](ITERATION43.md) y [PORT_REFERENCES.md](PORT_REFERENCES.md).

## Iteración 1.38: helper de skills ejecutado contra x86

- El helper común `00487ba0` se ejecutó bajo Unicorn en cinco contratos; `0046d950` verificó 144 combinaciones de ejes/botones y el seed de capacidad 90. El reporte está en `artifacts/x86-skill-use-oracle.json`. Skills 500+ aún no están activadas por el runtime; faltan selección por cartas, cancelaciones y efectos. Ver [ITERATION42.md](ITERATION42.md).

## Iteración 1.37: inventario de instrucciones de handlers

- Añadí resumen reproducible de mnemonics para los 20 `handleInputs` fijados al hash del PE: 44,899 instrucciones alcanzables y 40 mnemonics en la pasada CFG acotada. No es cobertura del ejecutable ni soporte semántico de un recompilador. Las pruebas Python pasan 10/10. Ver [ITERATION41.md](ITERATION41.md).

## Iteración 1.36: ráfaga de Suwako 418

- Porté el gate de contador de 808: seed al cruzar pose 10, diez spawns en los valores impares 1–19. El VPK [Touhou123Vita-suwako-burst-auto.vpk](../artifacts/Touhou123Vita-suwako-burst-auto.vpk) pasó Vita3K SDL schema19 y reportó `suwako_418_burst_spawns=10`, 600 frames, roster/PAT/tarjetas 20/20, BG34 y 145 texturas.
- El seed de secuencia0/subframe0 sigue supuesto hasta confirmar `DI` con una traza PC. Coordenadas, trayectoria, vida y daño están pendientes. Ver [ITERATION40.md](ITERATION40.md).

## Iteración 1.35: ventana y contador de ráfaga Suwako 418

- El port siembra el contador al entrar a pose 10 y emite objetos 808 en los valores impares 1–19. Vita3K schema19 comprueba diez creaciones: 600 frames, roster/PAT/tarjetas 20/20, BG34 y 145 texturas decodificadas. VPK: [Touhou123Vita-suwako-burst-auto.vpk](../artifacts/Touhou123Vita-suwako-burst-auto.vpk), SHA-256 `4477b6173f5ac4bae6d2807fd56f2afa5c25112e1366c4958c289bcfb53476bc`. El sentinel DI, posición/altura, velocidad y daño siguen pendientes de traza PC. Ver [ITERATION39.md](ITERATION39.md).
- Touhou75Vita continúa aportando método de análisis y pruebas por unidad; su runtime no se copió. Ver [ITERATION25.md](ITERATION25.md) y [ITERATION26.md](ITERATION26.md).

## Iteración 1.34: offsets PAT de Suwako 418 cotejados entre DAT

- Un extractor local confirma que el PAT prioritario de `th123c.dat` tiene 10 frames en 808/seq. 0, todos con `ox=64`, `oy=58`; A coincide y B no contiene ese PAT. El descriptor x86 usa los campos correspondientes a `ox/oy`, pero aún falta conectar con certeza qué actor/frame suministra el descriptor y mapear el espacio de `object+0x37c`; el spawn del port continúa provisional. Ver [ITERATION38.md](ITERATION38.md).
- `tools/extract_pat_pose_metadata.py` lee solo la entrada solicitada de los DAT locales y reporta su prioridad y hash.

## Iteración 1.33: geometría de Suwako 418 rastreada hasta metadatos

- El análisis del PE fijado ubica el setter `00406d30`, el adaptador `00438fc0` y las dos llamadas de Suwako 808. `stage+0x98` sale de `s16(metadata+0x0e)` y `stage+0x9c` de `s16(metadata+0x0c) - object.y`. Aún falta localizar/cargar el registro concreto y validar la semántica de `object.y`; los valores de movimiento Vita siguen provisionales.
- Revisé qué transfiere Touhou75Vita: inventarios y CFG/reachability, lifting acotado, métricas de cobertura y harnesses fail-loud. Su smoke test Linux es mínimo, su VPK solo diagnostica PE y el bootstrap de VitaSDK falló por proxy; no se importó código ni se mezclaron direcciones. Ver [ITERATION37.md](ITERATION37.md) y [PORT_REFERENCES.md](PORT_REFERENCES.md).

## Iteración 1.32: transforms de spawn sustentados por el PE

- El analizador con hash fijo confirma dispatches y coordenadas: Alice 408 y 418, Suwako 408; el port aplica offsets de creación y dos casos de seguimiento. Cinco spawns, cuatro variantes con hitbox y dos anclajes pasan en Vita3K SDL.
- Suwako 418 ya tiene las expresiones de geometría rastreadas, pero faltan los datos concretos y la paridad completa de ciclo de vida/daño por frame. Ver [ITERATION37.md](ITERATION37.md) y [ITERATION36.md](ITERATION36.md).

## Iteración 1.31: objetos PAT visibles de Alice y Suwako

- Pool de 16 objetos con avance PAT, movimiento/vida provisionales, colisión ofensiva y dibujo de imágenes PAT. El probe valida cinco spawns, cuatro variantes ofensivas y decodificación de la imagen.
- VitaSDK + Vita3K SDL pasan autotest schema 17, con captura `object-probe.bmp`; Qt cae al arrancar con lectura nula. Falta comparar trayectorias/daño por frame con el ejecutable original. CTest host sigue pendiente. Ver [ITERATION35.md](ITERATION35.md).

## Iteración 1.30: dash de Alice y Suwako delega a objetos PAT

- El flujo del PE fijado por hash confirma llamadas a `Player::createObject` para Alice 408/418 y Suwako 408/418. Los IDs son Alice 849 en ambas acciones, Suwako 989 en 408 y 808 en 418.
- Las secuencias quedaron identificadas por `customData[2]` leído en los inicializadores: Alice 408 → move 849/seq. 19 (sin caja), Alice 418 → 849/21 o 23 (cajas), Suwako 408 → 989/5 (cajas) y Suwako 418 → 808/0 (cajas). Se confirmó en los PAT/XML locales. Falta portar update, trayectoria, colisión y daño efectivo del objeto.
- El análisis Ghidra completo se reutilizó, pero su script Java no compiló por acceso denegado a JAR del Ghidra compartido. El rastro Capstone se hizo sobre el mismo PE y quedó bajo `artifacts/ghidra/object-analysis/capstone/` (ignorado por Git).
- Detalles y direcciones: [ITERATION34.md](ITERATION34.md). La demo Vita no incluye aún estos impactos; no se cuenta como combate completado.

## Iteración 1.29: payload auxiliar de pose preservado

- `T123Pose` conserva los 30 bytes auxiliares que el parser PAT antes descartaba. El fixture C verifica bytes conocidos, aunque no pudo ejecutarse porque CMake/compilador host no están disponibles; el build VitaSDK y el test Vita3K pasaron con el decoder ampliado.
- VPK actualizado: [Touhou123Vita-roster-hits.vpk](../artifacts/Touhou123Vita-roster-hits.vpk), SHA-256 `1a8836b9d040c162800bbbf956d422b770bb12c934a1186026062a3407c9d3b4`.
- Evidencia y límite de la prueba en [ITERATION33.md](ITERATION33.md).

## Iteración 1.28: daño directo PAT del dash y actualización de referencias

- VPK nuevo aprobado en Vita3K: [Touhou123Vita-roster-hits.vpk](../artifacts/Touhou123Vita-roster-hits.vpk), SHA-256 `1a8836b9d040c162800bbbf956d422b770bb12c934a1186026062a3407c9d3b4`.
- De 38 variantes 408/418 (19 personajes), 35 aplicaron daño PAT tras un contacto directo; 3 variantes no tienen caja ofensiva directa. El gate reporta ambos contadores y exige que sumen 38. Las rutas de objetos/efectos siguen pendientes.
- La auditoría XML clasifica los casos: Alice 408 no declara daño; Alice 418 declara daño 1000/efecto 7 sin caja ofensiva; Suwako 418 no declara daño y usa poses `dashBack`/`shotCd`. No se cuentan como impactos cubiertos ni como objetos confirmados.
- Vita3K: 600 frames, roster/PAT 20/20, 137 texturas, escenario BG34 y cero fallos de textura. Tests Python: 8/8; `git diff --check` limpio.
- Touhou75Vita revisado: prototipo de lifting/runtime smoke host y VPK diagnóstico PE; build VitaSDK no validado por HTTP 403. Adoptar metodología, no código; la licencia del checkout revisado no estaba declarada. Ver [ITERATION32.md](ITERATION32.md) y [PORT_REFERENCES.md](PORT_REFERENCES.md).

## Iteración 1.27: rutas dash y locks por variante

- Mapeé los 20 `handleInputs` desde el slot 20 de sus vtables para el PE fijado. Capstone recorrió los bloques alcanzables; el resumen estático encontró IDs candidatos 408/418 en 19 handlers y 412/2C como ruta dedicada de Remilia. Los resultados reproducibles están en `tools/disassemble_character_handlers.py`, `tools/summarize_character_handlers.py` y los artefactos locales ignorados bajo `artifacts/kernel/<sha>/character-input/`.
- Corregí el combate nativo para consultar el `moveLock` de la variante ofensiva seleccionada, en vez de leer siempre el índice 0. El fixture sintético con locks 1/3/6 ahora prueba variante seleccionada en frame 6 y rechazo en frame 7.
- La autoprueba Vita3K carga los 20 PAT: para 19 comprueba el borde inclusivo de 408 y 418; para Remilia comprueba la selección 2C/412 y ausencia de 408/418. Build VitaSDK y Vita3K SDL: 600 frames, 20/20 recursos, 137 texturas, BG34, cero fallos de textura; `dash_gate_probe=1`.
- VPK automático: [Touhou123Vita-roster-dash.vpk](../artifacts/Touhou123Vita-roster-dash.vpk), SHA-256 `8344d35f5d63a6d5c907b326c59f6116ccedf2ab076697ba5c1db3d142b7b2d0`. Todas las pruebas Python: 8/8 aprobadas. Esto no verifica guards exactos ni paridad de daño contra el PC original; Remilia aún necesita su ruta de impacto/objeto y el combate completo sigue pendiente.

## Iteración 1.26: cobertura PAT de dash por roster

- Generé [DASH_DISPATCH_COVERAGE.md](DASH_DISPATCH_COVERAGE.md) desde `artifacts/pat-detail.tsv`, con acciones 200/408/418, índices, `move_lock`/`action_lock` y poses dañinas para los 20 PAT jugables.
- Resultado: 20/20 definen 200; 19/20 definen explícitamente 408 y 418. Remilia no contiene 408/418 y requiere ruta específica. El `move_lock` de 408 cambia por personaje/variante (Yuyuko 20, Alice 40, la mayoría 50); hay variantes 418 con lock distinto a índice 0. Se evita extrapolar el handler compartido de Reimu/Cirno al roster entero.
- Agregué el generador `tools/summarize_dash_dispatch.py` y su prueba unitaria; `python -m unittest tests/test_dash_dispatch_summary.py` pasó. La prueba Vita3K con PAT reales de Reimu/Cirno para 408/418 sigue aprobada en [Touhou123Vita-real-locks.vpk](../artifacts/Touhou123Vita-real-locks.vpk).

## Iteración 1.25: ventana de cancelación de dash por moveLock

- El análisis Ghidra de los handlers Reimu `004ae670` y Cirno `006fb8b0` compara el frame actual con `getMoveLock(0x198/0x1a2)` antes de cambiar de dash frontal 200 a 66B/66C. `fight.c` ahora aplica el `move_lock` del PAT destino para aceptar 408/418; supera la ventana, rechaza la cancelación.
- El probe ARM sintético comprueba el borde inclusivo y el rechazo al tick siguiente; un segundo probe repite ambos lados usando los `move_lock` decodificados de las PAT reales de Reimu y Cirno para 408 y 418. Build VitaSDK y Vita3K SDL pasaron: 600 frames, `dash_gate_probe=1`, B/C=1/1, roster 20/20 y cero fallos de textura.
- VPK: [Touhou123Vita-real-locks.vpk](../artifacts/Touhou123Vita-real-locks.vpk), SHA-256 `cbc8c8c098f55f2d892ad48158dad7724c15c784c260471d4497831ac383633b`. El selector de variante sigue heurístico y la suite host continúa pendiente por falta de toolchain host/WSL.

## Iteración 1.24: variantes PAT de dash por cobertura de hitbox

- El selector `408`/`418` ahora consulta `t123_pattern_best_attack` en vez de asumir que el primer índice es el ataque. El helper elige por cobertura de daño/hitbox del PAT; es un fallback de demo, pues falta recuperar del motor original el selector real de índices/objetos.
- Un probe ARM sintético de combate con tres índices 408 confirma que se ignora el placeholder, se selecciona el índice 2 (daño 250) y se aplican las cajas contra el rival. La compilación VitaSDK y la regresión Vita3K SDL pasaron 600 frames, `dash_gate_probe=1`, roster PAT/tarjetas 20/20 y cero fallos de textura.
- VPK: [Touhou123Vita-attack-variant.vpk](../artifacts/Touhou123Vita-attack-variant.vpk), SHA-256 `7bf586ab0bfd246220a16fd83fc4316c6245cec2ab369154338c249726448ce7`. Reporte: `artifacts/vita3k-result.json`.
- La suite host `fight_tests` no pudo ejecutarse: cmake/gcc host no están disponibles y WSL sigue devolviendo `E_ACCESSDENIED`. Se compiló y ejecutó el probe equivalente dentro del VPK Vita.

## Iteración 1.23: productor de entrada fuente-base

- `0046d5d0` cierra el formato observado del word de input: direcciones `0x01/02/04/08`, A-D `0x10/20/40/80`, change-card `0x100` y spellcard `0x200`. El empaquetador de combate ya refleja esos bits.
- El probe integrado verifica las combinaciones `0x019` y `0x3e6`. El diferencial sigue en 401/401; VPK automático y Vita3K pasan 600 frames, con `dash_gate_probe=1`, tres dashes, B/C=1/1 y las 20 entradas de roster cargadas.
- VPK de esta iteración: [Touhou123Vita-input-producer.vpk](../artifacts/Touhou123Vita-input-producer.vpk), SHA-256 `a808bc56cc95b9e2e61a6dc477275edd9c3ca195871d2c9eeffd14828d57ddfc`. Reporte fresco: `artifacts/vita3k-result.json`.
- El otro chat de Touhou75Vita se revisó: smoke test Linux del runtime semántico mínimo sí pasó; no se pudo instalar VitaSDK en su entorno cloud por HTTP 403 y su VPK continúa siendo diagnóstico PE. Se transfieren métodos de análisis y pruebas, no código fuente.

## Iteración 1.22: matcher ARM integrado al dash

- El buffer y matcher de input C ya alimentan `fight.c`: el dash se reconoce mediante `NRNR`/`NLNL` en un ring de 90 muestras sembrado al reset.
- Diferencial x86/ARMv7 bajo Unicorn: 401/401 casos (17 contractuales, 128 positivos generados y 256 determinísticos); también pasó el contrato del ring/wrap. Runner: [test_input_arm_oracle.py](../tools/test_input_arm_oracle.py); detalles: [ITERATION26.md](ITERATION26.md).
- VPK automático `artifacts/Touhou123Vita-matcher.vpk`, SHA-256 `e9be67a7dff4b3400a0bb52752589ad66bdbe356bde02a87df701e64f0ea0361`. Vita3K SDL pasó 600 frames y el probe del matcher: 3 dashes, B/C=1/1, DAT=31, texturas=137, roster PAT/tarjetas=20/20 y escenario BG34 completo.
- Los límites del dash cambian a 12 muestras neutrales aceptadas y 13 rechazadas dentro de la búsqueda de 15 muestras. Productor de input real, bindings, replay, comparación con PC y paridad del motor completo continúan pendientes.

## Iteración 1.21: revisión de Touhou75Vita y helper C inicial

- Localicé y revisé el chat **Configurar Touhou75Vita**. Su trabajo es un prototipo de análisis estático y runtime semántico mínimo; su VPK sigue siendo diagnóstico de PE32. Registré las prácticas transferibles y el límite de no copiar código por licencia no aclarada en [ITERATION25.md](ITERATION25.md) y [PORT_REFERENCES.md](PORT_REFERENCES.md).
- Añadí un buffer circular C de 90 muestras y matcher aislado, junto con contratos para las secuencias verificadas y X/A/B/C/D. El código y tests compilan con VitaSDK (`-Wall -Wextra -Werror`); aún no se conectan al combate porque falta comparación diferencial completa. No se generó VPK.
- Actualicé el oráculo a 17/17 vectores x86, incluyendo X con cada botón.

## Iteración 1.20: matcher x86 aislado y referencias de recompilación

- Se ejecutó directamente `0046cc90` del PE 1.10a en Unicorn, con SHA fijado y un deque sintético de 90 muestras. Pasaron los vectores de aceptación/rechazo para NRNR/NLNL/DD, N09/N07/N08, orientación espejo, `2N2A` y X/A/B/C/D. Evidencia local: `artifacts/x86-motion-vectors.json`; generador: [x86_motion_oracle.py](../tools/x86_motion_oracle.py); interpretación y límites: [ITERATION24.md](ITERATION24.md).
- Esta prueba valida el matcher x86 aislado, no el productor/neutralización real, bindings configurados, runtime Vita ni paridad de combate. El gate Vita no se cambió y no hay VPK nuevo.
- Se revisaron D2Vita, repentogxm y Touhou75Vita; las prácticas transferibles y los límites/licencias están en [PORT_REFERENCES.md](PORT_REFERENCES.md). Próximo trabajo inmediato: helper C contrastado contra esos vectores y contra muestras del productor/replays; luego VPK/Vita3K.

## Iteración 1.19: siembra de 90 muestras del estado actual

- La inicialización del jugador llama `0046d950`; esta empaqueta dirección/botones y solicita a `0046d890` reconfigurar `Player+0x7b0` con `0x5a` (90) copias. El update por tick mantiene esa ventana al añadir una muestra y expulsar la más antigua.
- El byte bajo que `0046d950` resiembra queda decodificado: A/B/C/D en `0x10/0x20/0x40/0x80`, ejes de dirección en el nibble bajo. `0046d5d0` añade change-card/spellcard en bits 8/9. Falta cerrar neutral/diagonales/orientación y ramas completas del matcher; el gate Vita de dash sigue aproximado.
- Sin cambios de runtime/VPK. Evidencia: [ITERATION23.md](ITERATION23.md) y [player-input-window-seed.capstone.txt](../artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/input-state/player-input-window-seed.capstone.txt).

## Iteración 1.18: retención de ventana fija y corrección del xref aparente

> La búsqueda del precargado, que en esta iteración seguía abierta, quedó resuelta parcialmente en la iteración 1.19.

- Append seguido de avanzar head/decrementar conserva el tamaño preexistente: N muestras siguen siendo N y se expulsa la más antigua. Una cola vacía sigue vacía; falta localizar dónde se precarga o refresca al iniciar el combate.
- `0046d939` pertenece al cuerpo de edición de rangos que termina en `0046d944`, no es un caller externo; las filas del barrido Capstone son candidatos, no xrefs auditados. El constructor `0046c330` pone a cero los campos `+0x7b4..+0x7c0`, sin que esta iteración identifique una carga posterior.
- Sin cambios de runtime/VPK. Evidencia y siguiente secuencia: [ITERATION22.md](ITERATION22.md), [ITERATION21.md](ITERATION21.md) e [INPUT_STATE.md](INPUT_STATE.md).

## Iteración 1.17: ruta de update y semántica del conteo

- `0046d5d0` es el update que arma y registra la muestra; `0046d050` es una rutina genérica del deque. Tras el append, el update avanza el índice y reduce el tamaño; si el tamaño inicial era 0, vuelve a quedar en 0, por lo que falta identificar el seeding/refill que alimenta el matcher.
- Dump actualizado: [player-input-update.capstone.txt](../artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/input-state/player-input-update.capstone.txt). Hallazgos y siguiente análisis: [ITERATION21.md](ITERATION21.md) y [INPUT_STATE.md](INPUT_STATE.md).
- Sin cambios de runtime ni VPK nuevo en esta iteración.

## Iteración 1.16: orientación del selector de patrones

- SokuLib identifica `this+0x104` como `AnimationObject::direction`; el byte con signo elige entre las dos tablas de tokens, que reflejan 4/6 y diagonales según el lado. `Player.hpp` también confirma el deque de comandos en `0x7b0` y las máscaras de movimiento/comando en `0x7c4`/`0x7c8`.
- Fuentes de estructura y alcance de evidencia: [ITERATION20.md](ITERATION20.md), [INPUT_STATE.md](INPUT_STATE.md). El matcher Vita sigue siendo aproximado; no hubo cambio de runtime ni VPK nuevo.

## Iteración 1.15: productor y bloques del historial de input

- Se recuperó el productor del ring: `0042cf90` añade una muestra de 16 bits; la asignación usa bloques de 16 bytes con 8 muestras, y `0046d78f` es la ruta que registra el estado del jugador antes de avanzar el cursor circular.
- El estado se construye desde flags del jugador en `0046d5f0–0046d69b`; el matcher mira los bits de dirección/botón. Aún falta cerrar cómo se mantiene el conteo al envejecer y cómo se inicializa para escribir un matcher fiel.
- Evidencia y siguiente análisis: [ITERATION19.md](ITERATION19.md), [ring-writer.capstone.txt](../artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/input-state/ring-writer.capstone.txt) y [INPUT_STATE.md](INPUT_STATE.md). No hubo cambios de runtime ni un VPK nuevo; se conserva como último probado el de [Iteración 1.14](ITERATION18.md).

## Iteración 1.14: helper de secuencias y orientación espejo

- El desensamblado completo de `0046cc90` confirma dos tablas de traducción de secuencias y cotejo sobre el ring de entradas empaquetadas (`this+0x7b0`, cursor `this+0x7bc`). Se guardó el dump Capstone con el PE 1.10a fijado; no se etiqueta como pseudocódigo Ghidra.
- El gate Vita ahora prueba `N-L-N-L` desde el lado derecho del rival y verifica la ruta frontal a `408:index 1`, además de los casos previos. Vita3K SDL pasó 600 frames con `dash_gate_probe=1`, 20/20 personajes y tarjetas y cero fallos de textura.
- VPK interactivo [Touhou123Vita-input-ring-probe.vpk](../artifacts/Touhou123Vita-input-ring-probe.vpk), SHA-256 `0af9a368d44670693179d49a8df70dba6f72a6f63de7f43c5f3e470f2ae26983`. Automático probado [Touhou123Vita-input-ring-probe-auto.vpk](../artifacts/Touhou123Vita-input-ring-probe-auto.vpk), SHA-256 `66f6f0e4e559251b5367fab19fdd3d885a2dcf60966c037ad0ef5ecffa899d6d`; reporte [vita3k-result.json](../artifacts/vita3k-result.json).
- El matcher real aún no está portado: faltan el formato/cadencia del ring, la semántica de neutral y flags de botones, move locks y cancelaciones. La suite host sigue pendiente por el bloqueo de WSL; evidencia y siguiente trabajo en [ITERATION18.md](ITERATION18.md).

## Iteración 1.13: doble toque con ventana recuperada

- El dump de `00487020` confirma `NRNR`/`NLNL` con límite de historial 15, longitud 4 y bits `0x7c4` máscara `1`/`2`; `0048a220` usa esos bits y la orientación para el dash frontal. Ver [INPUT_STATE.md](INPUT_STATE.md) y [dump Capstone](../artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/input-state/00487020.capstone.txt).
- La demo ahora refleja la ventana de 15 ticks. El guest comprueba borde 15 aceptado/16 rechazado, neutral B/C rechazado y dash→66B/66C permitido. Vita3K SDL pasó 600 frames con `dash_gate_probe=1`, 3 dashes, A/B/C=1/1/1, roster y tarjetas 20/20 y sin fallos de textura.
- VPK interactivo [Touhou123Vita-dash-15tick.vpk](../artifacts/Touhou123Vita-dash-15tick.vpk), SHA-256 `749cefed223c7ae23b466b5a2c2c087cc78da41c2fcea9996a4b6a14ef3c4e87`; reporte [vita3k-result.json](../artifacts/vita3k-result.json). Move locks, duración del dash, cancelaciones y prueba host siguen pendientes; WSL devolvió `E_ACCESSDENIED`.
- Detalles y alcance de evidencia: [ITERATION17.md](ITERATION17.md).

## Iteración 1.12: dash frontal como requisito de 66B/66C

- La implementación de combate no permite ya entrar a `408`/`418` desde neutral con adelante+B/C; exige doble toque hacia el rival, acción `200` activa y dirección hacia delante. El límite de 15 ticks se recuperó del desensamblado de `00487020`; el sondeo guest de Vita verifica 15 aceptado/16 rechazado, los bloqueos desde neutral y las rutas positivas `408:index 1`/`418:index 0`. `fight_reset` restablece el historial de input. Duración de dash, move locks y cancelaciones aún no igualan el motor original.
- Ghidra confirma estado y dirección para Reimu/Cirno en `004ae670.c`/`006fb8b0.c` y la ruta de dash en `0048a220.c`. Las pruebas incluyen bloqueo fuera de dash y activación desde 200.
- Build VitaSDK + Vita3K SDL fresco aprobado (600 frames): `dash_gate_probe=1`, 3 dashes, A/B/C=1/1/1, roster 20/20, 0 errores de textura. VPK interactivo [Touhou123Vita-dash-gated.vpk](../artifacts/Touhou123Vita-dash-gated.vpk), SHA-256 `ab76e8a7a8915a80469755ba80494da24deadbebdf5681091c36a5c5133f3e2c`; reporte [vita3k-result.json](../artifacts/vita3k-result.json). Suite host no ejecutada porque WSL falló con `E_ACCESSDENIED`.
- Limitaciones, evidencia y siguiente investigación: [ITERATION17.md](ITERATION17.md) y [INPUT_STATE.md](INPUT_STATE.md).

## Iteración 1.11: mapa de colocación BG34

- El visor encaja las dos rejillas BG34 dentro del panel con tiles limitados a celdas de 256 unidades y expone las cuatro posiciones estáticas recuperadas. La proyección final continúa provisional.
- VPK interactivo listo: [Touhou123Vita-bg34-layout.vpk](../artifacts/Touhou123Vita-bg34-layout.vpk), SHA-256 `044262752b6c761b0b38554063b4f3439baf3f841575d91fff5452be87f6ee06`.
- VPK automático validado en Vita3K SDL durante 600 frames: rejillas 30+30, bitmaps 4/4, frames 30/30, roster/tarjetas 20/20, sin fallos de textura, práctica y combate B/C aprobados. Ver [reporte](../artifacts/vita3k-result.json) y [captura](../artifacts/screenshots/stage-layout.bmp).
- Detalle y limitaciones: [ITERATION15.md](ITERATION15.md). Cámara/proyección, parallax, colisiones, mecánicas y los otros escenarios siguen pendientes.

## Iteración 1.10: ciclo animado de objetos BG34 decompilado

- Se siguió la referencia desde el constructor a vtable `0085afa4`. Ghidra decompiló seis slots; `00473f40` incrementa `+0x64` y `00473fc0` elige `objectFa((tick % 60)/2)`: 30 frames, dos ticks cada uno, ciclo de 60 ticks. Exportes: `stage-layout/bg34-vtable.tsv`, `bg34-constructor-references.tsv` y pseudocódigos `00473f40.c`/`00473fc0.c`.
- La galería del VPK ahora anima la selección a esa cadencia y resalta el frame activo. Gate automático Vita3K SDL aprobado, 600 frames: tick 47/frame 23, tiles 30+30, bitmaps 4/4, sprites 30/30, roster 20/20 y cero fallos de textura. Captura [stage-assets.bmp](../artifacts/screenshots/stage-assets.bmp); reporte [vita3k-result.json](../artifacts/vita3k-result.json).
- VPK automático: `artifacts/Touhou123Vita-stage-animation-auto.vpk`, 80,782 bytes, SHA-256 `0d2449b8d8eefdc98026e35e25745243230f0c57ae500a08b32283fe46fefb35`. Posición/cámara, condiciones de dibujo, colisiones, lógica y los otros 23 escenarios siguen pendientes.

## Iteración 1.9: recursos auxiliares de BG34 verificados en Vita3K

- Ghidra (`00474f70`) confirma 4 bitmaps estáticos `0001`–`0004`, 30 sprites `objectFa000`–`objectFa029` y las dos rejillas. La demo añade una tercera vista de inspección; no afirma haber reconstruido el controlador temporal ni el layout dinámico de esos objetos.
- Autoprueba fresca Vita3K SDL aprobada, 600 frames: 30/30 tiles en cada rejilla, 4/4 bitmaps y 30/30 sprites objeto decodificados, roster y tarjetas 20/20, cero fallos de textura. Evidencia en [vita3k-result.json](../artifacts/vita3k-result.json) y captura revisada [stage-assets.bmp](../artifacts/screenshots/stage-assets.bmp).
- VPK automático reproducible: `artifacts/Touhou123Vita-stage-assets-auto.vpk`, 80,227 bytes, SHA-256 `5bdd62132545170611293f1e83127133f7c1e44d4a2d5f2083c4912ea54268ec`. Faltan animación/posicionamiento de objetos en el mundo, cámara, colisiones y los otros escenarios.

## Iteración 1.8: dispatch y rejilla de BG34 validados en Vita3K

- Ghidra, sobre el PE 1.10a con SHA verificado, exportó selección y dispatch (`00424280`, `00470e40`), loader genérico (`0046fe40`) y loaders concretos. Sus pseudocódigos y callers están bajo `artifacts/kernel/<sha>/stage-layout/`; se corrigió una variable duplicada que impedía compilar los scripts Java del paquete.
- La referencia confirma 24 IDs/carpetas entre DAT 10.5 y 12.3, rejilla 6×5 con orden x invertido, y dos rejillas en BG34 (prefijos `0000`/`0001`) con desplazamiento vertical de 1200 unidades. El visor muestra la cuadrícula de `0000` y la vista compuesta con ambos planos y el offset relativo recuperado.
- Autoprueba fresca Vita3K SDL aprobada, 600 frames: `stage=bg34`, `stage_layer=1`, 30/30 tiles en cada plano; galería, roster 20/20, práctica/pelea y B=2/C=2 también pasan. Evidencia: [vita3k-result.json](../artifacts/vita3k-result.json), captura guest inspeccionada [stage.bmp](../artifacts/screenshots/stage.bmp).
- VPK automático: `artifacts/Touhou123Vita-stage-auto.vpk`, SHA-256 `3aad88ba732fd3672b8bc91bbf7aeef4cab18dd1325a0c6c462aff9213265bbd`. La vista compuesta integra orden y offset relativos de BG34; cámara/scroll, bitmaps estáticos, objetos animados, colisiones y mecánicas siguen pendientes.
- VPK interactivo abierto en la Vita3K local: `artifacts/Touhou123Vita-stage.vpk`, SHA-256 `babb3663b46746d182cff0da0ef117a63935fc89dfe8befdf6522b785e8dbce0` (78,858 bytes), proceso 432.

## Iteración 1.7: visor inicial de tiles de escenario

- El visor anterior recorría las 14 carpetas de `th123a/b/c.dat` y servía como catálogo de recursos; su primera cuadrícula estaba basada en supuestos sobre los nombres. La iteración 1.8 corrigió su cobertura y geometría a partir del loader x86.

## Iteración 1.6: galería PAT de roster validada en Vita3K

- El menú permite entrar a una galería de recursos PAT para recorrer los 20 candidatos del roster, sus acciones y poses. Se muestra la imagen CV2 junto con datos disponibles de acción/pose, duración, daño y cajas; `Circle` vuelve al menú. La galería usa los mismos DAT externos del juego.
- La autoprueba fresca en Vita3K SDL pasó 600 frames: galería y textura detectadas; navegación por personaje, acción y pose confirmada; 20/20 tarjetas y assets PAT, cero fallos de textura del roster, 31 archivos DAT, 148 texturas; combate experimental registró B=2 y C=2, CPU 7600/10000 HP; salida guest 0. Evidencia: [vita3k-result.json](../artifacts/vita3k-result.json) y capturas guest en `artifacts/screenshots/`.
- VPK automático de validación: `artifacts/Touhou123Vita-gallery-auto.vpk`, SHA-256 `b1b2ff9eef89962c5c5d25fe9672e740e45eb966a237f350bc4df15b597fd887`. VPK interactivo para revisión manual: `artifacts/Touhou123Vita-gallery.vpk`, SHA-256 `30f115610f47a11ebab68102f94cb6cb8b49961af24e7417d64a8a2937743abd` (76,666 bytes); Vita3K local se abrió con el paquete instalado.
- El gate verifica disponibilidad y navegación del contenido PAT, no que cada transición/ataque sea idéntico al original. La iteración 1.8 ya añade el visor y la geometría inicial de BG34; composición completa, paridad de combate y comprobación visual amplia siguen pendientes.

## Iteración 1.5: auditoría de decodificación PAT implementada

- `resource_probe --pat-image-decode` selecciona los PAT según la prioridad runtime y decodifica cada entrada usando el kernel ARM real. Corrida en app temporal de Vita3K SDL, VPK `artifacts/Touhou123Vita-pat-image-audit.vpk`, SHA-256 `71050b240a7dcedf6d5e0b996c27f00761c7479ffceb66ad02988d704f648634`; guest exit 0. Examinó 22 PAT y 13,210 entradas: 12,444 imágenes referenciadas decodificadas, 765 entradas sin uso por poses y 1 referencia faltante, sin fallos de paleta ni CV2 no soportada. Reporte: [PAT_IMAGE_DECODE.md](PAT_IMAGE_DECODE.md), TSV local ignorado por Git en `artifacts/pat-image-decode.tsv`.
- Las 20 carpetas candidatas del roster no tienen referencias de imagen ausentes ni errores de decodificación, incluidas las imágenes que aparecen en poses ofensivas. La única falta es `common/000 hikakuyou.bmp`, con 31 referencias no ofensivas; aún requiere rastrear su consumidor/recurso en otra versión. No confundir el resultado con paridad de animación o alcanzabilidad de movimientos.
- `tools/run-pat-image-audit-vita.ps1` reconstruye y ejecuta el probe en Vita3K aislada; el resumidor `tools/summarize_pat_image_decode.py` genera la tabla por personaje. El compilador host/WSL deja de ser bloqueo para esta auditoría.
- Próximo paso: rastrear el recurso común faltante; resolver layout y selección de escenario desde la referencia y comparar muestras del visor con el juego de PC.

## Iteración 1.4: reconstrucción 66B/66C repetida en Vita3K

- Recompilé el código actual con VitaSDK y volví a ejecutar el gate en la Vita3K SDL aislada. `artifacts/Touhou123Vita-bc-reconstruction.vpk` (75,216 bytes, SHA-256 `00aba145b30b5ca94d2f6cc4107ea42257613aac6bd06f028cd9e766523012f0`) terminó 600 frames con `status=passed`, recorrido menú/práctica/pelea/salto, `A=1`, `B=2`, `C=1`, CPU 8300/10000, 31 archivos DAT externos, 128 texturas y PAT/tarjetas/recursos de roster 20/20. Reporte autoritativo: [vita3k-result.json](../artifacts/vita3k-result.json).
- La corrida reproduce el gate experimental ya observado; no valida doble toque, move locks, cancelaciones ni equivalencia temporal con PC. Los recursos de ataques se encuentran indexados, pero la auditoría 2,963 variantes solo prueba disponibilidad en los DAT, no decodificación ni reproducción de todas sus poses.
- Intenté ejecutar la suite host: en esta sesión no se encuentra CMake ni compilador host; WSL devuelve `E_ACCESSDENIED`. No cuento binarios host preexistentes como una ejecución fresca. El build VitaSDK y el test Vita3K sí se ejecutaron en esta iteración.
- Recompilé y reabrí la demostración interactiva en la Vita3K aislada: `artifacts/Touhou123Vita-bc-demo.vpk`, 75,050 bytes, SHA-256 `6ae13c7af57499536fa89172e9e7eb7caac9302238145a583b5963adacc1e348`. El proceso local de revisión se inició como PID 24308. Esta demo omite el marcador automático; el VPK de arriba es el artefacto de gate.

## Iteración 1.3: rutas experimentales 66B/66C

- La lectura de la referencia 1.10a identificó `00489610` como `getMoveLock(action)` y los slots virtuales 20/21 como `handleInputs`/`checkAllMotionInputs` para Reimu y Cirno. Sus handlers seleccionan `408` (66B) y `418` (66C) desde dash frontal `200`; los PAT de ambos personajes usan variantes dañinas `408:1` y `418:0`.
- `src/fight.c` ahora conserva el índice de variante de acción y enruta forward+B/C a `408`/`418`; selecciona una variante posterior solo si la variante base no tiene poses dañinas. Esto permite probar las cajas de ataque reales PAT. Aún omite el doble toque/move lock que debe producir y autorizar el dash `200`.
- Primera ejecución del gate automático para ese código. La recompilación fresca con hash actual queda registrada en iteración 1.4.
- Primer VPK interactivo de la iteración 1.3, sustituido por la recompilación de iteración 1.4.
- Siguiente: reconstruir detección del doble toque desde `checkAllMotionInputs`, transición a acción `200`, ventana `getMoveLock`, y luego comparar por frame. El resto del roster, objetos, cartas, escenarios y sistemas permanece pendiente.

## Iteración 1.2: DAT heredados de 10.5 y cobertura idle 20/20

- Se comprobó con el índice DAT que los 74 nombres idle que faltaban en nueve PAT de 12.3 sí están en `th105a.dat` de la instalación local de Touhou 10.5. El cruce por personaje da 6/6 Sakuya, 8/8 Youmu, 8/8 Remilia, 10/10 Yuyuko, 9/9 Udonge, 8/8 Aya, 8/8 Komachi, 9/9 Iku y 8/8 Tenshi.
- `src/resources.c` ahora monta hasta cinco DAT y busca primero en los archivos más específicos: `th123c > th123b > th123a > th105b > th105a`. Los tres DAT de 12.3 siguen siendo el requisito base; `th105a.dat`/`th105b.dat` completan los sprites heredados.
- VPK interactivo para revisión: `artifacts/Touhou123Vita-th105.vpk`, SHA-256 `35b918b83433d31c47b77a892e863445c11fbe1923494052eb55050597647451` (74,665 bytes). Build nativo Windows con VitaSDK: `tools/build-vita-native.ps1`; no depende de WSL ni CMake.
- Diagnóstico Vita3K de ese mismo VPK: 600 frames, menú/práctica/combate/salto detectados; cinco DAT (`external_dat=31`), 111 texturas, PAT 20/20, tarjetas 20/20, sprites idle 20/20, `A=3`, `B=0`, `C=0`, CPU 9600/10000 HP, guest exit 0 y digest `2562787365`. La gate estricta falla por B/C. Esto prueba disponibilidad y renderizado de la pose idle, no el conjunto completo de animaciones, ataques, escenarios o mecánicas.
- VPK diagnóstico con `auto-test.txt`: `artifacts/Touhou123Vita-th105-diagnostic.vpk`, SHA-256 `95af9d0a91718df86c2443cd49eed143b7e59c2062177c214721bd623c5e262c`. Reporte del VPK interactivo recién repetido: `artifacts/vita3k-result.json`; capturas guest: `artifacts/screenshots/{menu,practice,fight}.bmp`.
- DAT comerciales usados en la prueba permanecen fuera del VPK, en el VitaFS local de pruebas. Para otra instalación deben copiarse desde copias propias del usuario. No se modificó la instalación Vita3K compartida.

## Investigación en curso: despacho de B/C

- Build automático coherente con el runtime actual: `artifacts/Touhou123Vita-current-diagnostic.vpk`, SHA-256 `65203eb93f6f1326a901944443edb9d6d1c11697650276e94bb617f25715a4ae`. Vita3K ejecutó 600 frames sin crash: menú/práctica/pelea/salto, 5 DAT, 119 texturas, roster y idle 20/20; combate `A=1, B=0, C=0`, CPU 9900/10000. El test estricto falla por B/C.
- Corrección de la hipótesis anterior: SokuLib identifica `00489610` como `Player::getMoveLock(action)`, no como consulta al historial de input. En la referencia local, busca el ID de acción en un árbol/mapa de `this+0x160`; `0043f2f0` es la búsqueda y no el writer. Los handlers `00489e90`, `0048a220`, `0048a380`, `0048a470` y `0048a560` consultan move locks para `D0–D2`, `C8–CB` y `D6` mientras procesan saltos, dashes y vuelo. `00487990`/`00487ab0` filtran estado/orientación y despachan `DC–E2`. El mapeo físico de B/C sigue sin reconstruirse.
- La inspección x86 encontró el constructor y destructor del mapa (`00411714–0041171f`, `00411760–004117c1`) y llamadas a la búsqueda desde `00489610`, `00483aa2` y `00483b85`. `tools/find_pe_callers.py` fija el SHA 1.10a y emite candidatos Capstone en `artifacts/move-lock-callers.tsv`; por el barrido lineal, aún se deben confirmar individualmente antes de atribuirles semántica.
- `src/pattern.c` expone conteo de variantes por acción y una consulta analítica de variantes con pose dañina/cajas. Se retiró del runtime la regla heurística de elegir la variante más fuerte porque no mejoró B/C y no está respaldada por la ruta de input de PC; la API se conserva separada del dispatcher.
- `tools/summarize_pat_resource_coverage.ps1` cruzó 76,357 poses contra los manifiestos de cinco DAT: 12,883 poses con daño/caja o flag, 2,963 variantes personaje/acción/índice en 20 personajes, y cero imágenes dañinas ausentes. Ver [PAT_RESOURCE_COVERAGE.md](PAT_RESOURCE_COVERAGE.md). Esto prioriza reconstruir estado/buffer/input y no buscar DAT adicionales para esos ataques.
- La búsqueda de variante PAT fue compilada y probada en varias secuencias Vita3K. Resultado estable del build final de esa sonda: 600 frames, idle 20/20, cinco DAT, 119 texturas y `A=1, B=0, C=0`; digest `2662334619`. El build intermedio de secuencia corta quedó en 0 impactos y no se usa como resultado representativo.
- VPK de sonda experimental: `artifacts/Touhou123Vita-bc-probe.vpk`, SHA-256 `1c59d1807addf98774c4adc03b55ae43206fb6e3bc8f39c1da25d37adb1f90b4`. No sustituye al interactivo 1.2 y su autoprueba falla; por eso no se marca M4 avanzado a combate funcional.
- La autoprueba de 600 frames actual no es evidencia suficiente para comandos originales: genera inputs directos, sin cargar BE ni buffer de movimientos. Próximo paso: reconstruir el buffer/comandos y el umbral de carga desde sus callers/campos, y contrastarlo con secuencia PC antes de retirar la barrera estricta.
- `tools/ghidra/ExportKernel.java` ahora registra referencias de instrucciones a los campos usados por ambos handlers y exporta sus funciones contenedoras. La exportación dirigida escribe en `artifacts/kernel/<sha>/input-state/` para no mezclar este barrido con pseudocódigos anteriores. Falta ejecutarlo con Ghidra/JDK y revisar manualmente cada referencia por dirección.

## Seguimiento del loader Ghidra: 2026-10-15 (evidencia anterior a iteración 1.2)

- `00408cf0` busca variantes `nombre_N.bmp` de `DAT_00896b84` hasta 1 y luego el nombre base; el EXE inicializa ese límite en `0`, así que no prueba sufijos en su configuración base. En modo paquete cambia la extensión a `.cv2`.
- `00409b50` calcula CRC32 del nombre plegando ASCII a mayúsculas; `0041c530` busca el hash en un árbol balanceado y `0041c080` resuelve colisiones con comparación insensible a mayúsculas/minúsculas antes de recuperar archivo, offset y tamaño.
- `0041bb50` abre y descifra el índice DAT; `0041bdd0` inserta cada entrada en el árbol. La estructura coincide con la que consume `src/resources.c`.
- `pat-archive-idle.tsv` cruzado con `resource-manifest.tsv`: 74 nombres idle distintos de 9 personajes faltan en los tres índices. No parece un fallo de hash, capitalización o sufijos; queda rastrear PAT de otras revisiones y atlas/archivos externos.
- Exportación Ghidra de solo lectura verificada en `artifacts/kernel/<sha>/resource-loader/`, incluidos lector, inserción, hash e inicializadores hallados por referencias a globals.
- VPK de iteración 1.1: `artifacts/Touhou123Vita-para-probar.vpk`, copia idéntica a iter11 (SHA-256 `282eb8d9149673ba909c925c82a0843ad822aa500030a3399f1751b0f4566309`). Esa prueba alcanzó menú/práctica/combate, 93 texturas y 11/20 sprites; B/C seguían pendientes.
- En ese punto WSL devolvía `E_ACCESSDENIED` y el pipeline Windows todavía no empaquetaba; la iteración 1.2 resolvió el build directo con `tools/build-vita-native.ps1`.
## Iteración 1.1: auditoría de PAT y nuevo VPK

- `resource_probe --pat-archive-idle` compara por separado cada PAT de A/C con las rutas de imagen CV2 exactas en los tres DAT. El resultado reproducible está en `artifacts/pat-archive-idle.tsv`: 42 versiones PAT y 446 poses idle; 18 revisiones no encuentran ningún archivo idle referenciado, 4 encuentran solo parte y 19 encuentran todos los frames de idle.
- Se confirmó que nombres con espacio antes de `.cv2` aparecen literalmente en el índice DAT; no se deben normalizar. Un contrato lo protege.
- Suite host: 8/8 aprobada. VPK interactivo: `artifacts/Touhou123Vita-iter11.vpk`, SHA-256 `282eb8d9149673ba909c925c82a0843ad822aa500030a3399f1751b0f4566309`.
- Vita3K aislado: 600 frames y recorrido de menú/práctica/pelea/salto completados; 20/20 PAT y tarjetas, 11/20 sprites idle, 93 texturas, `A=3`, `B=0`, `C=0`, CPU 9600/10000 HP, guest exit 0, digest `2562787365`. La gate integral continúa fallando.
- La duplicación A/C no explica por sí sola los sprites ausentes: ambas revisiones de nueve personajes declaran rutas idle que no están en los DAT. Siguiente paso: analizar con Ghidra el loader real y su lookup/atlas compartido. Ver [ITERATION11.md](ITERATION11.md).

## Iteración 1.0: arte original para selector de los 20 personajes

- `data/stand/<slug>.cv2` está presente para los 20 candidatos y cada textura se decodifica a 640×480 (RGBA). Se añadió una caché de dos atlas para mostrar el arte original del roster en menú/práctica y una máscara separada de PAT/cobertura de sprite de combate.
- El runner ahora guarda reporte y capturas guest aun cuando la aceptación estricta falla. Capturas recientes de la corrida iter10: `artifacts/screenshots/{menu,practice,fight}.bmp`; revisadas visualmente, las tarjetas de Reimu, Cirno y Yuyuko se renderizan desde los DAT originales.
- VPK diagnóstico: `artifacts/Touhou123Vita-iter10-diagnostic.vpk`, SHA256 `3cdfc9f4cd5028d1289fd589608478223e1cc5cf6f3cada446375ddfd00539a9`.
- Vita3K 600 frames, menú/práctica/pelea/salto, 20/20 PAT, 20/20 tarjetas, 11/20 sprites de pose idle, 93 texturas de pose, `A=3`, `B=0`, `C=0`, CPU 9600/10000 HP, 7 DAT, guest code 0, digest `2562787365`. La corrida es reproducible, pero la gate integral sigue fallando por sprites de combate faltantes y B/C.
- Se regeneró `artifacts/pat-detail.tsv` con rectángulos `tx/ty/tw/th` (76,357 poses, 7,975,746 bytes). Los idle de Sakuya indican seis archivos `standNNN.bmp`, cada recorte 64×128 en origen (0,0); `data/stand/sakuya.cv2` es una ilustración completa 640×480 y no se debe confundir con ese set de frames.
- Próxima fase: resolver la asociación de imágenes PAT/CV2 para los nueve combat sprites pendientes y analizar el loader original con Ghidra; después mapear inputs B/C. Ver [ITERATION10.md](ITERATION10.md).

## Iteración 0.9: selector de roster y diagnóstico fresco, cobertura todavía parcial

- Build host limpia con GNU C: 8/8 contratos aprobados, incluidos los oráculos x86 1.01 y 1.10a. El build temporal ARM genera ELF/SELF; VitaSDK requiere compilar desde ruta Linux sin espacios para empaquetar VPK.
- VPK de diagnóstico: `artifacts/Touhou123Vita-iter09-diagnostic.vpk`, SHA256 `79070659b1fa8c144f68af7abe141fefccfcc465aa66e369f2617a1a45a0f5bc`.
- Corrida nueva en Vita3K aislado: 600 frames; menú, práctica, pelea y salto detectados; 7 DAT internos, 93 texturas decodificadas, 20/20 PAT cargados; 11/20 imágenes de preview de roster encontradas. `A=3`, `B=0`, `C=0`; CPU 9600/10000 HP; el proceso guest salió con código 0. El gate integral falla por cobertura incompleta y B/C.
- Evidencia fresca: `artifacts/vitafs/ux0/data/touhou123vita-smoke.json`, `artifacts/vitafs/ux0/data/touhou123vita-roster.tsv` y capturas en `artifacts/screenshots/{menu,practice,fight}.bmp`.
- Hashes verificados byte a byte contra `F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law`: `th123a.dat` `389fb969ff161f49f909f27d22a244e5327cc413e31991ba24cd6b612825aa09`; `th123b.dat` `7ac17fc04ba087b50eab52a65751833a7b0b6e00c11601964cf66576201a4413`; `th123c.dat` `9189de6e2d01bb696d3f2393c441e14716784b7fdaa33f77c69ac602c0605939`. La discrepancia de nueve previews es de lookup/referencias, no de DAT distintos.
- `tools/ghidra/ExportKernel.java` incluye objetivos para helpers de input y movimiento, pero Ghidra/WSL no se pudo iniciar en esta sesión. Hay pseudocódigo previo de `004ac670`, `004ae670`, `006fa260` y `006fb8b0`; no hay exportación de los helpers `00487990`/`00487ab0` en el snapshot. Ver [ITERATION09.md](ITERATION09.md).

## Iteración 0.6: demo A recuperada, análisis B/C pendiente

- Objetivo activo: reconstruir todos los personajes y recursos, escenarios completos y mecánicas, validar funcionalidad progresivamente en Vita3K y optimizar FPS después en hardware real.
- El manifiesto de los tres DAT locales cuenta 11,283 entradas (1,088,266,746 bytes sin comprimir), 22 carpetas PAT de personaje y 14 carpetas `background`. Se generó catálogo PAT para las 22 carpetas; se estima un roster de 20 carpetas jugables candidatas más `namazu` y `common`, pendiente confirmación desde selección/guion.
- La primera autoprueba instrumentada B/C **falló** correctamente: 600 frames, DAT y texturas cargados, salida guest 0, pero `a_hits=4`, `b_hits=0`, `c_hits=0`. 400/500 no son ataques dañinos en los PAT; ver [ITERATION04.md](ITERATION04.md).
- Iter06 interactiva: `artifacts/Touhou123Vita-iter06.vpk`, SHA256 `8130299143940dfadb7a9911684738349f8182f0d2d1d1601ceb197fb5d53a11`. Está abierta en Vita3K local. Autotest: 600 frames, 7 DAT, 77 texturas, `a_hits=4`, `b_hits=0`, `c_hits=0`, salida invitado 0; la barrera estricta B/C falla como debe.
- Iter05 intentó recorrer índices PAT en secuencia y se retiró al observar cero impactos en Vita3K. El XML muestra variantes por índice con bucles y bloqueos distintos. Informes: [ITERATION05.md](ITERATION05.md) y [ITERATION06.md](ITERATION06.md).
- Artefactos de inventario: [RESOURCE_INVENTORY.md](RESOURCE_INVENTORY.md) y [PAT_COVERAGE.md](PAT_COVERAGE.md). El VPK no contiene DAT comerciales.
- Nueva matriz [ATTACK_COVERAGE.md](ATTACK_COVERAGE.md): disponibilidad de variantes con daño en los 22 PAT. Enum SokuLib confirma 408=`66B` y 418=`66C`; el catálogo local muestra índices dañinos para ambos personajes. Esto acota el análisis, pero no demuestra aún cómo se activan.
- Corrección de análisis: `00487ba0` es `Player::useSkill`; los helpers compartidos de entrada identificados son `00487990` y `00487ab0`. Se ampliaron los objetivos de exportación Ghidra para incluir esos helpers y dash/flight; ver [KERNEL.md](KERNEL.md).
- Iteración 0.7: `resource_probe --pat-detail` generó 76,357 poses de los 22 PAT. [DASH_ATTACK_REFERENCE.md](DASH_ATTACK_REFERENCE.md) compara 117 variantes 66B/j4B/66C por personaje; host 8/8. No cambia la VPK ni supera aún el gate B/C. Ver [ITERATION07.md](ITERATION07.md).

## Iteración de combate 0.3: 2026-10-15

- Incorporados estados PAT base y selección de ataques A direccionales para Reimu y Cirno; una cadena hit-confirm puede avanzar 5A→5AA→5AAA→5AAAA si el PAT incluye esos bloques.
- Suite host: 8/8 aprobada. Los contratos prueban locomoción, salto, agacharse, aterrizaje, ataques aéreos y la cadena con cajas PAT sintéticas.
- VitaSDK generó el VPK interactivo `artifacts/Touhou123Vita-combat-iter.vpk` (SHA256 `8d0b28411f4be4440a650166547731d31b6ece77619b51ea7bb21301830041b2`) y el VPK automático `artifacts/Touhou123Vita-auto-combat-iter.vpk` (SHA256 `82f8acbeb7c3dcc342223214a1ce73932d85c142d10f1d8d8ed933483d4bee4b`).
- Cinco instalaciones frescas del VPK automático pasaron en Vita3K SDL: 600 frames cada una, 11 impactos, CPU 8250/10000 HP, 7 DAT, 71 texturas, digest `3845639945` idéntico y salida guest 0.
- Esta versión ya sirve para probar como demo interactiva. No es aún el juego completo: proyectiles/B/C, specials, física de referencia, cancelaciones, rounds y comparación con entradas PC siguen pendientes. Ver [ITERATION03.md](ITERATION03.md).

## Actualización Vita3K aislado: 2026-10-15

- Se creó `local/vita3k-isolated` como copia local independiente de `G:\Vita3k`, usando la modalidad portátil de Vita3K. Su configuración y logs viven en `local/vita3k-isolated/portable`; un junction apunta el VitaFS portátil al VitaFS de pruebas propio del proyecto en `artifacts/vitafs`.
- Una primera serie de cinco pruebas fue retractada: el runner cerraba el ZIP después de validarlo y antes de extraerlo, así que pudo arrancar el eboot que ya estaba instalado. Se corrigió para validar y extraer dentro de la misma apertura del ZIP.
- Con el runner corregido, cinco instalaciones frescas de `Touhou123Vita-auto-combat-iter.vpk` pasaron: 600 frames, 11 impactos, CPU con 8250/10000 HP, 7 DAT, 71 texturas y digest `3845639945` en cada una. Hash VPK: `82f8acbeb7c3dcc342223214a1ce73932d85c142d10f1d8d8ed933483d4bee4b`.
- Se generaron capturas guest nuevas en `artifacts/screenshots/{menu,practice,fight}.bmp`; el juego cerró con código 0. Controles manuales, replay `.rep`, V2/V3 y sesiones largas siguen pendientes.
- La instancia local conserva modo portátil, config/logs propios y VitaFS de prueba separado de la instalación compartida.

## Actualización de compilación: 2026-10-15

- Build limpio host y VitaSDK completados desde una copia temporal Linux para evitar que VitaSDK dividiera la ruta de Windows con espacios al empaquetar el VPK.
- Contratos host: 8/8 aprobados, incluidos los oráculos x86 de animación 1.01 y 1.10a.
- VPK interactivo recién generado: `artifacts/Touhou123Vita-resume.vpk`, SHA256 `adfdaebaf3a54b232218e03865233c3b9bd9a65bf44b360acffdbb4cd95f4044`. VPK automático: `artifacts/Touhou123Vita-auto-resume.vpk`, SHA256 `6629f7c0641b1f347aee07c81d64fcf0420bb2019c7f8b811c8e968dfc7ecb05`.
- El VPK interactivo contiene `sce_sys/param.sfo`, `eboot.bin` y `assets/font.rgba`; ambos paquetes fueron creados por VitaSDK.
- El primer intento con una copia renombrada falló al iniciar; quedó superado al usar el modo portátil oficial con el nombre ejecutable original. La instancia principal no fue cerrada ni modificada.
- El replay `090815_2219_sanae_story.rep` todavía no se reproduce en la demo: el runtime no tiene parser `.rep`. Su formato y compatibilidad con la referencia están pendientes.

## Verificado

**Línea base histórica: iteración 0.3.** El estado vigente es iteración 1.2, descrita al inicio de este archivo; las secciones siguientes conservan referencias y resultados históricos.

- Inventario local generado con SHA256 y metadatos PE.
- Ejecutable aportado: 4,816,896 bytes, SHA256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.
- Ghidra identifica `x86:LE:32:default`; importaciones incluyen Direct3D 9, D3DX9, WinMM y Winsock.
- Se exportaron 30 funciones iniciales a pseudocódigo local. La primera coincide en dirección con la referencia de comienzo de render de SokuLib; el comportamiento requiere análisis adicional.
- El análisis automático alcanzó el límite de 600 segundos. El post-script, guardado e importación finalizaron correctamente; no se da por terminado el análisis del motor.
- Extracción de `th123a.dat`, conversión local de sprites/paletas y recursos de escenario.
- Pruebas host `core_contract`, `fight_contract` y `tools_contract`: 3/3 aprobadas.
- Compilación ARM/SELF/VPK del prototipo interactivo y de la variante automática completada.

## Validación Vita3K completada

- Escenario automático de 600 frames: menú, práctica, pelea y salto alcanzados; 13 impactos del jugador; CPU termina con 267 HP; ambos sprites cargados.
- Digest determinista del escenario: `2362081707`.
- Pipeline completo `tools/run-all.ps1` ejecutado y aprobado, incluyendo build host/ARM y autoprueba Vita3K.
- VPK automático de la última ejecución: SHA256 `8377f7ab4f416ab7c260e3f8807d6eef8c1a842fd22d304f51c41508c6f9f952`.
- VPK interactivo entregado: SHA256 `58749d39cf60f776e338457c94c38002e5a9c29f57fed488935f198d23d9a522`.
- Vita3K `0.2.1 4170-7e152b66`, frontend SDL, Vulkan, entorno aislado con copia del firmware local. Se usó una copia de la versión instalada en `windows-latest`; la versión `4103-e6ac4272` de la carpeta indicada inicialmente no completó el arranque automático Qt.
- El cierre inicial provocaba un acceso inválido al liberar el framebuffer aún en uso. Corregido conservando los buffers hasta la salida del proceso. Última ejecución: salida 0 y sin error crítico de runtime.
- Capturas del framebuffer generadas por el guest dentro de Vita3K: menú, configuración de práctica y pelea; revisadas visualmente. No son capturas de la ventana del host.
- Controles manuales de teclado aún pendientes: el usuario detuvo Computer Use con Escape. No se reanudó ese control ni se afirma que entradas físicas estén verificadas.
- Repositorio privado creado y código subido a [Botarguirix/Touhou123Vita](https://github.com/Botarguirix/Touhou123Vita), tras confirmar cuenta/destino y verificar el payload sin archivos comerciales.

## Pendiente del port original

El kernel de animación sí está recuperado y contrastado con x86; los DAT/PAT y 5A aportan poses, cajas y daño originales. La física, resolución completa de combate, decks, clima, audio, historia, netplay y paridad de replays siguen pendientes. PS Vita física no probada.

Los resultados locales completos están bajo `artifacts/`; no se publican recursos comerciales ni pseudocódigo bruto.

- VPK interactivo recompilado y abierto en Vita3K local: `artifacts/Touhou123Vita-gallery.vpk`, SHA-256 `30f115610f47a11ebab68102f94cb6cb8b49961af24e7417d64a8a2937743abd` (76,666 bytes). Proceso de revisión iniciado como PID 20148.

## Iteración 1.67: split 808 encadenado en Unicorn

El oracle encadena el handler original del padre, ambos custom data, initializer original y ocho ticks de update por hijo con secuencia 1 explícita. Con RNG [10,2,20,4], hijos [-20,12] y [-30,14] parten con velocidades radiales (-4.104,11.276) y (-7,12.124); al tick 8 llegan a (267.166,483.010) y (244,489.795). Suite enfocada 7/7. El factory virtual aún no prueba que arg4=1 seleccione object+0x13e=1; estado de frame/colisión/vida/terminación persisten como límites, así que no se modificó el placeholder Vita ni se creó un VPK. Ver [ITERATION67.md](ITERATION67.md) y `artifacts/x86-suwako-808-child-trajectories.json`.

## Iteración 1.68: regresión integral Vita3K

El checkout actual compiló un VPK auto-test y pasó una corrida fresca Vita3K aislada de 600 frames (schema28), SHA-256 11d0c4df4f35a27edd275ef0bb96ed4f8751df26ba9a68c3576700ad385873c3. Reportó roster PAT/combate/cartas 20/20, DAT 31, 148 texturas, BG34 capas/tiles/objetos, rutas dash, Suwako 418 diez spawns y skills Reimu 540/565/505 con los daños esperados por los probes. Es una regresión de la versión integrada; no incluye el cambio de oracle 808, que aún no está portado. Reporte artifacts/vita3k-result.json; capturas artifacts/screenshots/. Ver [ITERATION68.md](ITERATION68.md).

## Iteración 1.69: cadence corregido del objeto Suwako 808

La revisión del handler seq.1 mostró que solo integra posición al alcanzar subframe 8; cada callback aplica gravedad 0.2 y suma 0.005 a +0x11c/+0x120. Se corrigió el harness para conservar ese escalar y el reloj externo; la trayectoria previa de ITERATION67 queda supersedida. Con secuencia 1 explícita, 24 callbacks dan (287.6873,428.4290) y (279,430.9731) para ambos custom data. Prueba enfocada 7/7. Factory real, secuencia natural, colisión y vida siguen sin resolver; no se alteró el motor ni el VPK. Ver [ITERATION69.md](ITERATION69.md).

## Iteración 1.70: secuencia radial del objeto 808

El selector de secuencia viene de customData[2] (contrato de initializeAction 0799000 documentado en ITERATION34), no del arg4 independiente de la fábrica. Los custom data del split terminan en 1; la ejecución Unicorn del initializer original confirma +0x13e=1 y el vector radial. La traza 24 callbacks se regeneró. El reloj externo, factory virtual, colisión/ciclo de vida siguen controlados/no probados end-to-end. Suite enfocada 7/7; el VPK sigue sin cambio. Ver [ITERATION70.md](ITERATION70.md).

## Iteración 1.71: alpha gobierna la integración del objeto 808

SokuLib ubica RenderInfo RGBA en AnimationObject+0x110; object+0x113 es alpha. El handler seq.1 lo reduce 8 por callback y detiene la integración posicional cuando alpha<8; no es un reloj externo. El oráculo conserva alpha 0xff controlado por falta de factory; reproduce avance 31 callbacks y freeze desde el 32. Trayectorias previas por reloj/subframe quedan supersedidas. Sin cambios Vita. Ver [ITERATION71.md](ITERATION71.md).
## Actualización de alcance (2026-10-16)

La revisión de Touhou75Vita queda en [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md): aprovechamos método de instrumentación, contratos ABI, watchdog y métricas; no se importa su runtime genérico ni sus offsets/imports/renderer al proyecto TH123. El checkout/código TH075 se revisó en solo lectura. La prueba Linux del chat de onboarding es sintética y no constituye un VPK de ese juego.

Corrección del modelo Suwako 808: `object+0x113` es alpha, pero `0xff` sigue siendo valor controlado del harness; no hay demostración del alpha inicial en el constructor TH123. `0x799000` no lo escribe y `0x438bb0` tampoco escribe ese byte. El factory completo aún no se ejecuta porque depende de inicialización del manager/lista y recursos PAT. No usar las trayectorias alpha-255 como resultado natural hasta resolver esa inicialización. Ver [ITERATION71.md](ITERATION71.md).

## Seguimiento Iteración 1.72

El factory `784020` obtiene un objeto de `783de0/783ba0`, ejecuta el constructor de Suwako `783a70`, copia custom data y llega por `setAction` a `799000→setSequence 4652a0`. El constructor del objeto no escribe `RenderInfo`; tampoco el initializer 808. Por eso todavía no hay evidencia del alpha observado al tomar una ranura del pool. Además, el initializer directo del harness omitía la selección PAT que hace `4652a0`. El PAT local declara seq.0 con diez frames de 100 y seq.1 con un frame de 150; el split pasa customData[2]=1. Siguiente: ejecutar constructor+cadena de acción con frame data auténtico/sintético y después resolver inicialización/reuso del pool. Ver [ITERATION72.md](ITERATION72.md).

### Corrida del initializer PAT 808 (Iteración 1.72)

Se ejecutó la cadena x86 original `setAction→setSequence→setPose→initializeAction` con el mapa de acción/seq y dos poses sintéticos. TH123 selecciona action 808, secuencia 1 y su nodo de frame 0, y calcula velocidad radial `(-4.10424, 11.27631)`. Los inicializadores conservan el color: con un centinela RGBA `d4c3b2a1`, incluido alpha `0xa1`, permanece idéntico; desde almacenamiento limpio queda alpha 0. Esto prueba que el valor inicial depende del almacenamiento/pool y no del initializer. Factory, allocator, renderer, daño/colisión y vida aún no están ejecutados. Oracle reproducible: `tools/x86_suwako_808_action_probe.py`, reporte local `artifacts/x86-suwako-808-action-probe.json`, regresiones `tests/test_suwako_808_action_probe.py`. Ver [ITERATION72.md](ITERATION72.md).

Corrección de Iteración 1.72: la ejecución con ctor real `0x783a70` pasó y reveló una escritura transitiva que el barrido superficial no capturó. La inicialización del sprite `438bb0` establece color `0xffffffff` (alpha 255) antes de `setAction`; el initializer no lo cambia. El harness ya ejecuta ese constructor y su allocator cdecl de nodos (dos bloques de 12 bytes controlados), y se regeneró el JSON. No confundir esta confirmación del ctor con el factory completo: aún faltan manager/handles y el loop de actualización/colisión/vida. Ver [ITERATION72.md](ITERATION72.md).

## Iteración 2.53: respuesta medida de Remilia 801 (corregida en 2.55)

El hit x86 resta 120 HP y escribe en el proyectil `+0x194=3` desde su prioridad 4, copia `PAT hitstop=0` a su `+0x196` y marca `+0x190=9`. El defensor ya tenía `+0x194=20`; no lo escribe esta respuesta. Ver la traza exacta y la aclaración de orientación en [ITERATION153.md](ITERATION153.md).

## Iteración 2.54: campo del defensor observado en update derivado

El campo `+0x194=20` del defensor se observó antes y después de 50 llamadas directas al update; no era un temporizador confirmado por el impacto. La respuesta de 801 escribe `+0x194=3` en el proyectil. Ver [ITERATION154.md](ITERATION154.md) y la corrección [ITERATION153.md](ITERATION153.md).

## Iteración 2.55: Remilia 801 continúa tras conectar

La respuesta de `0x47b660` fija campos del proyectil (prioridad de reacción 3, hitstop PAT 0 y estado `+0x190=9`), no el `+0x194=20` que ya tenía el defensor. El objeto sigue activo (`+0x34c=1`) al salir de la respuesta. En Vita el 801 conserva su instancia, avanza PAT y no repite daño; el gate ahora comprueba un impacto de 120 HP y la animación en el cuadro siguiente con recursos reales. Probes x86 6/6; VitaSDK compila el fixture; Vita3K SDL pasa 600 frames/schema46, regresión y BG33. Build de Vita usa `-Os` por defecto porque `-O3` falló en empaquetado SELF; FPS aún no comparados. VPK SHA-256 `158166ff94bdd7eec3ceb10d7646578aef009a8a2d80c687ba6cf4f9eec1c031`. Manager x86 posterior al hit y ciclo completo aún pendientes. Ver [ITERATION155.md](ITERATION155.md).

## Iteración 2.85: objetivo vertical derivado del zoom actual

Se portó el target Y de `FUN_00428e20` como función explícita de altura y zoom actual, incluyendo ramas `minY>270` y límite inferior `-420`. El VPK pasó Vita3K 600 cuadros/schema46 con gates en 1; suite 108/108. No equivale al easing vertical ni a integración de cámara en la pelea. VPK y fórmula: [ITERATION185.md](ITERATION185.md).

## Corrección de cámara vertical — Iteración 2.84

La fórmula vertical `max(420,minY)` reportada en Iteración 2.81 y repetida en el resumen 2.83 provenía de un estado artificial de zoom, no del constructor. Se ejecutó `FUN_00429560` completo: target Y y cámara Y dependen del zoom inicial, la doble evaluación de target y el update. El helper stateless ya no expone `center_y`. Oracle constructor con tres fixtures, suite 107/107 y VPK auto-test 600 cuadros/schema46 aprobados. Detalle/corrección: [ITERATION184.md](ITERATION184.md).

## Iteración 2.83: easing horizontal de cámara

`FUN_00429040` se contrastó con movimiento horizontal `delta/30 ± 5`, snap al objetivo y límites `[320/zoom,1280-320/zoom]` usando el zoom nuevo del cuadro. El helper X se agregó al core y al gate; Vita3K pasó 600 cuadros/schema46 y regresión integral, suite 106/106. Sigue pendiente eje Y, constructor completo e integración en el render de pelea. VPK y evidencia en [ITERATION183.md](ITERATION183.md).

## Iteración 2.82: easing asimétrico de zoom

`FUN_00429040` confirma pasos de zoom `/5 - 0.002` al alejar y `/80 + 0.002` al acercar, con snap al objetivo y piso 0.5. El helper está en el core y Vita3K SDL pasó 600 cuadros con gate general y de cámara en 1; suite 105/105. El estado de la cámara aún no está conectado a la pelea; interpolación X/Y y overrides siguen pendientes. Ver [ITERATION182.md](ITERATION182.md).

## Iteración 2.81: centro automático de cámara derivado del PE

El oracle captura los campos de salida de `FUN_00428e20` y confirma centro X `clamp((x0+x1)/2, 320/zoom, 960)`, Y `max(420,min(y0,y1))` en modo automático. Se portaron centro y zoom al helper y el autotest pasó Vita3K a 600 cuadros/schema46 con gate general y de cámara en 1. La suite Python pasó 104/104. Los overrides manuales y la transición temporal `FUN_00429040` se midieron parcialmente pero no están portados; el helper todavía no está integrado en el combate. VPKs y hashes: [ITERATION181.md](ITERATION181.md).

## Iteración 2.80: zoom automático derivado de la cámara original

Un oracle Unicorn ejecuta `FUN_00428e20` del PE fijado por hash y confirma, con cinco pares controlados, la regla de zoom `max(0.5, 640 / sqrt(max(640, abs(dx)+80)^2 + (abs(dy)*1.5)^2))`. Se implementó `t123_stage_camera_pair_target`; las pruebas enfocadas pasaron 4/4. VPK auto-test schema46 completó 600 cuadros en Vita3K SDL con `regression_gate=1` y `stage_camera_pair_contract=1`. El interactivo comparte exactamente el mismo eboot con el probado. No está resuelto ni conectado el centro de cámara, el easing/modo manual ni el encuadre de combate. Detalle y hashes en [ITERATION180.md](ITERATION180.md).

## Iteración 2.67: replay verificado contra el ejecutable original
- `inspect_replay_layout.py` consume los 67.881 bytes del replay suministrado usando su ejecutable compatible; se documentan hash/perfil, tres registros y tamaños de vectores. El ejecutable `original/th123.exe` del checkout no es compatible con ese replay y no debe usarse para esa prueba.
- Es evidencia del loader/estructura, no playback por frame. La cadence/semántica del vector y su conexión al combate quedan sin probar; no se modifica runtime ni VPK.
- Se documenta `psp2-tooling` como candidato de la fase M7 para Vita física, sujeto a Linux, hardware, firmware y módulos necesarios; no aporta al loop Vita3K actual.
- Ver [ITERATION167.md](ITERATION167.md).
