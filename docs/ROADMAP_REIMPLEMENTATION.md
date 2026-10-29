# Roadmap: reconstrucción integral de Touhou 12.3

## Estado global y siguientes hitos — actualizado el 18 de octubre de 2026 (CDMX)

Última entrega: [Iteración 2.199](ITERATION299.md), cajas PAT ordinarias en unidades completas y registro de contacto en el frame del comando, contrastados con el PE. Pruebas nativas de arena/colisión y 27 pruebas Python focales aprobadas; Vita3K pasó 600 frames, con contratos separados para Udonge 408 y 409. Próximo: migrar offsets y velocidades de objetos que aún usan media escala (Remilia 801), revisar empuje y comparar visualmente con PC. La captura del escritorio y el fixture C de Suika siguen pendientes; global 27%.

**Avance estimado: 27%** del objetivo final (27.1% por suma ponderada, redondeado). Es una estimación ponderada por entregables, no por número de iteraciones: se cuenta como terminado solo aquello que tiene evidencia en fuente, pruebas, VPK o ejecución. El porcentaje puede variar unos puntos al cerrar criterios más precisos; no significa que el juego esté cerca de estar completo. Última evidencia integrada: Iteración 2.199. BG36 se elige en preparación, la cuadrícula sigue el orden PE y Vita3K confirma el scroll de nubes y registra la cámara del frame de captura; falta cotejar cámara y composición con el juego original, así que no se cuenta como escenario terminado.

| Área del objetivo | Peso | Avance del área | Aporte global | Evidencia y brecha principal |
|---|---:|---:|---:|---|
| Toolchain, formatos e inventario/carga de recursos | 20% | 70% | 14.0% | VitaSDK, lector e inventarios y recursos visuales probados; faltan cerrar cobertura y validación de recursos en el juego integrado. |
| Roster: recursos, estados y acciones de los 20 personajes | 25% | 25% | 6.25% | PAT/poses y rutas de ataque avanzan; B/C aún tiene cobertura parcial y faltan estados, habilidades y pruebas completas por personaje. |
| Motor de combate y sistemas compartidos | 25% | 15% | 3.75% | Prototipo jugable y fundamentos de colisión/ataques; faltan paridad de estados, objetos, cartas, clima y flujo completo de combate. |
| 25 escenarios: composición, animación y mecánicas | 20% | 8% | 1.6% | BG33 dibuja su capa base en combate; BG36 es elegible y dibuja 25/25 tiles y cuatro auxiliares con orden PE. Faltan proyección/cámara visualmente correctas, comparación PC y reconstruir los otros escenarios. |
| Story, replay y audio | 5% | 10% | 0.5% | CSV y rutas Story se están trazando; faltan campaña jugable, reproducción de replay y audio funcional. |
| Validación final, paridad y rendimiento en hardware | 5% | 20% | 1.0% | VPK limpio y gate de 600 frames en Vita3K; no hay aún comparación sistemática contra PC ni medición en PS Vita física. |
| **Total ponderado** | **100%** |  | **27.1% ≈ 27%** | El prototipo actual demuestra una base técnica; todavía no equivale a una reconstrucción completa. |

### Próximos hitos

**Prioridad de presentación solicitada por el usuario:** comparar reposo, suelo, escala, cámara y capas contra el mismo escenario del PC antes de declarar fidelidad visual. La revisión y sus criterios están en [PRESENTATION_REVIEW.md](PRESENTATION_REVIEW.md). El intento de captura del original volvió a fallar; las 12 pruebas focales de reset/cámara pasan, pero no sustituyen esa comparación. BG33 tiene una referencia potencial en el replay Sanae; BG36 requiere su propia escena equivalente.

1. **Cerrar BG36 visualmente:** el selector de preparación alterna BG33/BG36 y el gate automatizado recorre la selección hasta la pelea. Los 25 tiles, con slots/nombres PE en orden, y cuatro auxiliares se dibujan con las pasadas cielo→nubes→tiles→torii. Vita3K también comprueba el scroll de ambas nubes a partir de los ticks de combate y registra cámara `(392,0,1)` en el frame automatizado. Obtener una captura PC del mismo replay/frame y comparar origen/escala/cámara/composición con el renderer x86; ajustar y repetir esa comparación.
2. **Cobertura de escenarios:** integrar las capas y animaciones restantes y registrar, para cada uno de los 25 IDs, recursos, constructor, renderer, mecánicas y prueba jugable. BG33 cuenta como capa base, no como escenario terminado.
3. **Cobertura del roster:** cerrar la matriz por personaje de poses/estados y acciones A/B/C/habilidades, objetos y pruebas de combate; no marcar un personaje completo por cargar sus sprites.
4. **Paridad del combate:** completar colisiones, daño, recuperación, cartas, clima y ciclo de ronda, comparando trazas/replays representativos con el original.
5. **Modos y salida final:** completar Story/replay/audio, repetir el gate Vita3K con escenarios y personajes representativos, y después perfilar en hardware PS Vita.

**Criterio de salida:** VPK instalable con combates completos, cobertura verificable de los 20 personajes y 25 escenarios, modos/recursos requeridos, regresión Vita3K reproducible y una pasada de rendimiento en hardware. La Iteración 2.191 valida el orden de capas BG36 según el PE; faltan interacción/cámara y paridad PC, por lo que no se cuenta como escenario terminado. [ITERATION291.md](ITERATION291.md). El historial por iteración que sigue documenta evidencia y limitaciones de cada avance.

### Revalidación del estado y siguiente bloqueo — 18 de octubre de 2026 (CDMX)

La revisión previa verificó hashes/Vita3K y fijó como siguiente entrega la selección interactiva de BG36. Esa brecha ya está cerrada por la Iteración 2.192; permanece sin cerrar la paridad de cámara/composición con PC. El 27% se conserva porque la selección por sí sola no completa un escenario ni una de las áreas principales del alcance.

### Selector de escenario conectado al combate — Iteración 2.192

La preparación de práctica ahora alterna BG33/BG36 con arriba/abajo; al confirmar, la pelea carga el escenario elegido. El autotest sigue esa misma secuencia, exige `battle_stage_selected_interactively=1`, mide ambos renderers y vuelve a BG33 para conservar el gate existente. Vita3K SDL aprobó schema46/600 y `regression_gate=1`; el reporte incluye BG36 con 25 tiles y cuatro auxiliares, además de BG33 con 24. La captura fresca confirma BG36 en combate y también deja visible que su encuadre/composición no coincide todavía con la referencia. El VPK no se considera una escena terminada; el 27% global se mantiene. Evidencia: [ITERATION292.md](ITERATION292.md).


### Cámara de la captura BG36 registrada — Iteración 2.195

El JSON Vita3K conserva cámara x/y/zoom exactamente en el frame de captura y el runner valida números/rango. VPK auto pasó schema46/600 con cámara (392,0,1), nubes −401.5/−301.0, 25 tiles y cuatro auxiliares; replay Story local compatible en formato con el EXE, escenario aún por identificar. No hay paridad visual probada; 27%. [ITERATION295.md](ITERATION295.md).

### Scroll de nubes BG36 contrastado durante combate — Iteración 2.194

El runner verifica posiciones de clowd_l/s contra el número de updates BG36 y la rutina PE (−400/−300, velocidades 1.5/1.0, wrap −1200/−800 a 800). Vita3K SDL pasó schema46/600: un update reportó −401.5/−301.0, 25 tiles y cuatro auxiliares; tests focales 7/7 y ambos VPK pasan validación estructural. La composición visual y cámara frente al juego original siguen abiertas; global 27%. [ITERATION294.md](ITERATION294.md).

### Orientación de las filas BG36 corregida — Iteración 2.193

El constructor PE carga `[01][01]` en el slot 0 y filas ascendentes; el port invertía las filas. Corregido, el patrón de 25 tiles presentes es `0x3ffff79c`, coincidente con los cinco recursos ausentes. Vita3K SDL pasó 600 frames con selector BG36, BG33/BG36 y auxiliares validados; la captura ya no presenta el corte vertical de la retícula. Falta confirmar composición/cámara con un replay sincronizado en PC; global 27%. [ITERATION293.md](ITERATION293.md).

### Orden de capas BG36 contrastado con el renderer x86 — Iteración 2.191

La secuencia PE es nubes, retícula base y torii; el port ahora usa ese orden. Vita3K SDL pasó 600 frames con hash coincidente, 25 tiles y cuatro auxiliares; la captura confirma el nuevo solapamiento. Unittest BG36 3/3 y BG37/BG38 4/4; ambos VPK pasan validación estructural. Sigue pendiente captura equivalente en PC y selector/cámara completos; global 27%. [ITERATION291.md](ITERATION291.md).

### Cielo base del renderer BG36 — Iteración 2.190

Se añadió el color de cielo base del PE (RGB 126,206,244) debajo de tiles BG36; ahora coincide con el fondo opaco de la nube. Vita3K SDL pasó 600 frames con hash coincidente, 25 tiles y cuatro auxiliares; unittest BG36 3/3 y BG37/BG38 4/4, ambos VPK pasan verificación estructural. Tintes/capas dinámicas, selección interactiva y paridad PC siguen pendientes; avance global 27%. [ITERATION290.md](ITERATION290.md).

### BG36 ya no hereda BG10 bajo sus capas — Iteración 2.189

El render de combate dibuja el fondo BG10 solo como reserva cuando BG33/BG36 no están listos; antes lo pintaba incondicionalmente bajo el escenario cargado. Los VPK auto e interactivo fueron reconstruidos; Vita3K SDL pasó 600 frames con hash exacto, 25 tiles BG36 y cuatro auxiliares. La captura muestra BG36, pero el rectángulo azul de la nube y la paridad con PC siguen abiertos; sin aumento de porcentaje. Contratos unittest BG36 3/3 y BG37/BG38 4/4 pasan; pytest global no disponible en el Python local y WSL denegó acceso. [ITERATION289.md](ITERATION289.md).

### BG36: retícula base integrada y validada — Iteración 2.188

El código carga/dibuja 25 de las 30 posiciones PE, preserva los cinco huecos y dibuja los cuatro auxiliares. Vita3K SDL pasó 600 frames con hash coincidente, gate BG36 25/25 y captura confirmada; 139 pruebas Python pasan. La captura aún muestra BG33 bajo BG36; faltan orden/composición, paridad PC y selector interactivo. [ITERATION288.md](ITERATION288.md).

### BG33 dibuja su capa base en el combate — Iteración 2.186

El render x86 de 30 slots y el ciclo de 1024 ticks ahora corren en la pelea con los 24 tiles BG33 y la cámara viva. Vita3K SDL pasó schema46/600: 24 tiles, 420 updates, 12,600 draws, máscara completa; VPK hash `fbd76df9…`, 139 pruebas Python. Esto integra la matriz base de un escenario; aún faltan sus auxiliares/mecánicas y los otros stages en combate. Siguiente: llevar BG36 del visor al combate y continuar los renderers por stage. [ITERATION286.md](ITERATION286.md).

### `Player+0x884` sigue sin explicar la recuperación natural de Suika — Iteración 2.185

La búsqueda global del PE separa la rama action97 de Suika del contador de cartas observado en diez otros updates de personajes: Suika solo muestra el reset directo y la lectura de action97. El call graph y el harness aún no incluyen todo el manager ni dispatch indirecto, así que la recuperación continúa abierta. Próximo: vigilar el campo en una trayectoria action97 con manager de combate completo y localizar el origen real del setter 96; no basar el port en la rama forzada. [ITERATION285.md](ITERATION285.md).

### VPK instalable con LiveArea y gate fresco — Iteración 2.184

El build ahora empaqueta `icon0.png`, `bg.png`, `startup.png` y `template.xml` indexados. Ambos VPK recién hechos pasan `check_vpk.py` sin advertencias y comparten eboot; el auto VPK pasó Vita3K SDL schema46/600 con hash coincidente. Suite Python 137/137 y prueba del generador 1/1. Esto corrige el empaquetado/instalación; no completa la paridad del juego. [ITERATION284.md](ITERATION284.md).

### BG35 no aparece en los seis DAT locales indexados — Iteración 2.183

Los manifiestos 10.5 y 12.3 cubren sus archivos DAT `a/b/c`; no hay entradas bajo `data/background/bg35/` en ninguno de los seis. El PE usa el loader genérico y omite el dibujo si el lookup devuelve nulo. Esto confirma ausencia en esta instalación, no en todas las distribuciones ni la apariencia intencional del stage. Prueba ampliada para exigir cobertura de manifiesto completa; sin runtime/VPK. [ITERATION283.md](ITERATION283.md).

### BG36 omite de forma segura cinco tiles ausentes — Iteración 2.182

El constructor pide los 30 slots de BG36, pero cinco recursos no figuran en ambos DAT locales. El loader original produce puntero nulo ante un lookup fallido y solo dibuja slots no nulos, por lo que puede continuar sin esos tiles. El patrón de huecos puede corresponder al borde de la escena, aunque falta verificarlo visualmente contra PC; permanecen reportados como ausentes y no se sintetizan. Contrato PE/manifiesto 10/10. [ITERATION282.md](ITERATION282.md).

### Auditor de recursos cuenta los 24 tiles reales de BG33 — Iteración 2.181

El constructor PE `0x473af0` reserva y carga 24 tiles base de cuatro filas por seis; el renderer itera 30 slots, pero no prueba que necesite assets para los seis slots restantes. El auditor ahora usa el constructor y reporta BG33 24/24 más 2/2 auxiliares, evitando seis falsos faltantes. Pruebas focalizadas 13/13; sin runtime/VPK. [ITERATION281.md](ITERATION281.md), [STAGE_RESOURCE_AUDIT.tsv](STAGE_RESOURCE_AUDIT.tsv).

### Los CSV Story se guardan como registros clave/valor con contadores — Iteración 2.180

`0x4330b6` resuelve clave y valor, y `0x4331c2→0x430e20` inserta registros de 24 bytes. `0x42f5e0` compara claves `[+0]`/`[+8]` e incrementa `[+0x0c]`; lo llama `0x468de0` bajo un flag Story. `0x42f680` incrementa `[+0x10]` y tiene dos callers. Esto aclara el almacenamiento/progreso, pero no establece qué campo es el stage activo ni conecta la fila Namazu con la creación del rival. Siguiente: observar el selector de stage y el argumento enviado al factory en ejecución original; después seguir construcción, PAT y combate Namazu. Sin cambio runtime/VPK; test PE estático ampliado. [ITERATION280.md](ITERATION280.md).

### Inventario de las tres campañas Story: Namazu cierra Meiling — Iteración 2.179

Las tablas locales contienen 15 stages: cinco para Cirno, Meiling y Sanae. El único `Namazu` aparece como rival del stage 4 de Meiling (cinco cartas, variante 3). El test fija toda la matriz de rivales y los tres paths DAT. Próximo: seleccionar esa fila en el flujo de stage, conectar el resultado al factory y reproducir el combate. Sin runtime/VPK. [ITERATION279.md](ITERATION279.md).

### El PE recorre y parsea los CSV Story de los 20 personajes — Iteración 2.178

`0x432bb0–0x43332f` forma `data/csv/<nombre>/story.csv`, abre cada tabla con `0x40f370`, procesa filas y resuelve un campo de cadena mediante `0x43f440`; repite hasta ID 19. Esto prueba que `meirin/story.csv` participa en el parser Story, incluida la fila Namazu. Aún falta identificar la estructura almacenada, el stage activo y el puente hasta `0x45ef50`/factory. Test PE y fuente pasa; sin runtime/VPK. [ITERATION278.md](ITERATION278.md).

### Stage 4 de Meiling crea a Namazu como rival Story — Iteración 2.177

`data/csv/meirin/story.csv` registra la etapa 4 con rival `Namazu`, cinco cartas y variante 3. El recurso está indexado en el `th123a.dat` original; SokuLib confirma `CHARACTER_NAMAZU=21`, consistente con el dispatch del factory. El PE enlaza el lookup de nombre con `PlayerInfo.character` y la creación del slot 3 cuando `EBX >= 3`; los tres callers aún no se han asignado de forma concluyente a un modo ni a este CSV. Esto prueba el uso como rival Story, no selección normal ni ejecución dinámica de la ruta concreta. Test estático añadido; sin runtime/VPK. Siguiente: encontrar el enlace entre el lector CSV y los callers `0x46152a`/`0x481c3d`/`0x481cdc`; el contexto `<br>` de `0x46152a` y las claves `win`/`lose` de los otros dos callers apuntan a contenido narrativo, pero no enlazan por sí solos el CSV de etapas. Luego confirmar el factory en combate y mapear recursos/mecánicas. [ITERATION277.md](ITERATION277.md).

### La ruta Story obtiene el personaje desde datos CSV — Iteración 2.176

El helper `0x43f440` busca una cadena/clave en la tabla global CSV y devuelve el valor de la fila. El caller `0x45ef50` copia el resultado a `PlayerInfo.character` y en `0x45f176` solicita creación del slot 3; el binario referencia `story.csv` y rutas `data/csv/`. Esto acota el origen potencial del ID 21 a los datos cargados, pero no demuestra que exista un registro 21 ni asigna definitivamente el modo. Siguiente: inspeccionar CSV originales, mapear fila/evento y verificar el ciclo/recurso de Namazu. Sin runtime/VPK. [ITERATION276.md](ITERATION276.md).

### `SaveDataManager` limita los desbloqueos al roster 0–19 — Iteración 2.175

`0x42ee80` rechaza IDs `>=20` antes de escribir el flag persistente; el factory llama a ese helper después de construir el Player. SokuLib enumera Random=20 y Namazu=21, fuera del arreglo `enabledCharacters[20]`. Namazu puede construirse, pero la evidencia apunta a entidad especial/Story y no prueba selección normal. Regresión nueva añadida; sin runtime/VPK. Siguiente: hallar productores de `PlayerInfo.character=21` en rutas Story/replay. [ITERATION275.md](ITERATION275.md).

### `GameDataManager::createQueue` conecta los registros con PlayerNamazu — Iteración 2.174

El helper `0x46ead0`, el worker `0x46e6e0→0x46e5c0` y el factory `0x46da40` forman la ruta común de creación; el resultado se guarda en `players[4]` de `GameDataManager` en `+0x28`. La jump table del factory despacha ID 21 a PlayerNamazu. Regresión estática focalizada 6/6; falta encontrar qué caller configura ese ID y si corresponde a selección normal o Story. Sin runtime/VPK. [ITERATION274.md](ITERATION274.md).

### Factory de índice interno 21 construye Namazu y comparte el timer — Iteración 2.173

El barrido de `.text` añade un décimo caso a los nueve writers de roster: vtable slot10 `0x85f824` con RTTI `Namazu`, handler `0x7d4400` y seed `0x7d47b2` (`+0x884/+0x886=300`). La entrada 21 (`0x15`) de la jump table central reserva `0x8a0` bytes y llama a su constructor; SokuLib corrobora `CHARACTER_NAMAZU=21`, y el inventario local cuenta 179 imágenes, 731 bloques y 3,276 poses PAT. Falta encontrar quién pide ese índice y confirmar si es seleccionable. Su expiración pide acción común 1201. Herramienta/reporte actualizados; prueba focal 5/5, sin runtime/VPK. [ITERATION273.md](ITERATION273.md).

### Selector de input 2 asociado al lado derecho en `PlayerInfo` — Iteración 2.172

`0x43dec0` configura lado izquierdo (`isRight=0`, `+6=1`) y derecho (`isRight=1`, `+6=2`); el constructor copia `+6` a `Player+0x7cc` y el dispatcher elige la ruta virtual de input. Dos callers están localizados, aunque el enum no debe generalizarse a todos los modos. Regresión PE 5/5, sin cambio/VPK. Esto concreta el guard `+0x7cc==2` de nueve handlers como lado derecho para esta ruta; falta la transición natural de carta→timer y resolver Suika/action96. [ITERATION272.md](ITERATION272.md).

### Jump tables revelan contadores +0x884 de 300 en nueve luchadores — Iteración 2.170

El barrido directo omitía destinos de tablas. Los updates slot10 de Reimu, Marisa, Alice, Patchouli, Cirno, Meiling, Sanae, Suwako y Utsuho asignan `0x12c` a `Player+0x884` en un caso de jump table; el flujo común decrementa y limpia. El escáner reproducible [scan_player_field_884.py](../tools/scan_player_field_884.py) confirma vtables, tablas, límites e inputs deque que van al caso 0: 0..15, 0..11, 0..7 o 0..19 según personaje. Un décimo writer en Namazu se identificó en Iteración 2.173. Suika no tiene store positivo directo en slot10; esto no resuelve su transición 97→96. [ITERATION270.md](ITERATION270.md).

### Action96 ejecutada 1.200 ticks; falta productor real y round manager — Iteración 2.169

`0x8985e8` es `InfoManagerBase::instance`; el método del timer en vtable +0x18 refresca HUD/gauges (`0x47eb70`→`0x47ed40`). Un shim de presentación con limpieza de stack original permite ejecutar 1.200 ticks PE sin fetch inválido. Action96 permanece y `Player+0x884` no cambia. El campo también lo consumen los updates de Alice (`0x5100b0`) y Suwako (`0x765ab0`), con decremento/limpieza pero sin productor positivo. La entrada sigue forzada: rastrear writes calculadas y el caller del round; después restaurar InfoManager/UI auténtico para validación integrada. [ITERATION269.md](ITERATION269.md).

### Callback de timer identificado como dependencia de action96 — Iteración 2.168

El fetch `0x0` tras 181 updates no es un retorno roto del updater: `0x606abe` devuelve al sentinel `0x03000000`. El tick 182 falla antes, dentro del timer `0x46a330`, cuando `0x463b69` llama `object+0x18` del singleton `0x8985e8`; el harness aún no lo construye. Localizar el inicializador/callback, incorporarlo para continuar el timer PE y luego seguir el productor real de `Player+0x884`. Action96 aún no sale ni queda probado el final gameplay. [ITERATION268.md](ITERATION268.md).

### Action96 permanece activa en el tramo PE; salida necesita manager completo — Iteración 2.167

Con PAT singleton real, setter y updater originales, 181 ticks válidos siguen en action96 y el handler pide seq3; no aparecen setters de acción ni escrituras `+0x884`. El siguiente tick alcanza un fetch bajo del fixture por contexto externo incompleto, así que no confirma el final real. Siguiente: integrar manager/caller y stack del combate para cerrar la salida natural. [ITERATION267.md](ITERATION267.md).

### Loader PAT original confirma autociclo singleton action96 — Iteración 2.166

El loader `0x4679e0` crea el primer nodo con `next=0`, `prev=self` (`0x467df2–0x467df9`). Action96 tiene seq0/10 frames solamente, así que seq1/3 sí reutilizan ese payload en la estructura original; corrige la hipótesis de autociclo exclusivo de fixture en Iteración 2.165. Falta su trigger/salida natural en el manager de combate. [ITERATION266.md](ITERATION266.md).

### Hipótesis inicial sobre autociclo action96 (corregida en 2.166)

`setSequence` sigue `+0x1c` n veces; el action96 fixture solo tiene seq0 y se autocicla, de modo que seq3 termina mostrando el payload seq0. El cambio de índice viene del PE, el contenido repetido no verifica recursos reales. Próximo: observar los enlaces construidos por el loader PAT y la ruta natural de acción. [ITERATION265.md](ITERATION265.md).

### Action96/97 comparten handler; PAT96 está incompleto para la ruta — Iteración 2.164

Las tablas PE envían acciones 96 y 97 al mismo update `0x485115`; action96 usa callback default y action97 el consumer `+0x884`. El handler común solicita sequence3 al pasar por seq1 en action96. El PAT efectivo de 96 solo define seq0/10 frames, de modo que falta resolver contenido y trigger natural antes de portarlo. Test de dispatch y evidencia: [ITERATION264.md](ITERATION264.md).

### Call graph Suika reduce `+0x884` a inicialización/reset — Iteración 2.163

Escáner reproducible desde vtable: 392 funciones alcanzables por calls directas, una referencia al campo en `0x48b15a`; `xor eax,eax` confirma borrado a cero vía slot17 `0x608670→0x48b000`. No es el productor positivo de action96. Próximo: rastrear managers y rutas indirectas, manteniendo límites del scan. [ITERATION263.md](ITERATION263.md), [reporte](../artifacts/suika-field-884-callgraph.json).

### CFG de vtable Suika no revela writer directo; action96 PAT parcial — Iteración 2.162

Ninguno de 48 slots ni los callees principales de update/callback/input mostró referencias directas a `+0x884` por ramas directas; managers/helpers y dispatch indirectos no cubiertos. Action96 seq0 tiene diez frames y el PE la ejecuta, pero la fixture luego recorre seq1/3 ausentes del PAT efectivo; no afirmar recuperación natural. Siguiente: recuperar call/xrefs indirectos y manager de combate para conectar la ruta natural. [ITERATION262.md](ITERATION262.md).

### Referencia `+0x884` de Reimu separada de la búsqueda Suika — Iteración 2.161

El writer `0x490795` pertenece al update `0x490490`, vtable Reimu slot 10; Suika usa `0x5ee620` en ese slot. No atribuir al recovery de Suika. Siguiente: seguir writers en update/callback y manager reales de Suika, y ampliar el hook dinámico a otras reacciones. Productor Suika/action96 aún pendientes. [ITERATION261.md](ITERATION261.md).

### Origen de `Player+0x884` sigue pendiente — Iteración 2.160

No hubo escrituras al campo en el resolver→300 ticks ni con ocho botones/abajo+botón mantenidos 24 ticks. Una mutación artificial a 1 justo antes de aterrizar produce `74→97→96` en el callback de entrada; eso acota el consumer, no valida recovery. El barrido lineal ejecutable no clasificó escritores y no se usa para descartarlos por los dispatch indirectos. Siguiente: ejecutar rutas naturales de reacción adicionales en el harness y ampliar la observación al ciclo del manager de pelea antes de mapear cualquier referencia estática. [ITERATION260.md](ITERATION260.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

### Posible salida de action97 vía `Player+0x884` — Iteración 2.159

El segundo dispatcher (`0x6086a0→0x48b85f`) puede pedir action96 si `Player+0x884>0` (`0x48b8cf→0x48b8e4`). En nuestra fixture el campo sigue en cero durante 300 ticks y con diez entradas discretas; se desconoce productor y significado de action96. Rastrear escritura dinámica en combate normal antes de modelarlo como levantamiento. [ITERATION259.md](ITERATION259.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

### Suika aterriza de action74 en action97 — Iteración 2.158

En tick10 el input neutral deja action74. El dispatcher ejecuta el handler PE 74; `0x487ea0` confirma suelo en la fixture y su rama solicita action97 en `0x4846a5`. El paso de caída queda explicado; el disparador para salir del loop circular 97 sigue pendiente. Reconectar stage/manager real y reproducir el levantamiento sin suelo controlado. [ITERATION258.md](ITERATION258.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

### Grafo PAT de action97 es circular — Iteración 2.157

El grafo efectivo enlazado es `0→1→2→3→0`, con loop de frames solo en seq.2; cada nodo tiene `prev` y `next`. Como `0x464bf0` considera terminal únicamente un nodo sin `prev`, el avance local no termina ni solicita action98. El barrido literal `push 0x62` solo encontró el callsite del handler 97; buscar setters calculados o el disparador en el manager de combate. [ITERATION257.md](ITERATION257.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

### Condición de salida de action97→98 identificada en el PE — Iteración 2.156

Action97 consulta `0x438c60` y solicita action98 desde `0x4851f9` solo si los callbacks PAT notifican fin de secuencia. En Suika, `0x464b70` evalúa wrap/loop de pose y `0x464bf0` devuelve terminal según el enlace previo del nodo. El diagnóstico artificial de 120 ticks sin loop en seq.2 recorre PAT nodes hasta el contador 23 y permanece en action97, sin setter; no es gameplay natural. Siguiente: recuperar el grafo efectivo del PAT 97 y enlazar su transición con el manager/estado real de combate. [ITERATION256.md](ITERATION256.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

### Suika 97 permanece en downed loop 300 ticks — Iteración 2.155

Después del impacto PE y reacción 74, `0x46a330` + `handleInputs 0x609dc0` neutral + update `0x5ee620` ejecutan 300 ticks: action97 sigue PAT `0→1→3→0→1→2`, entra en seq.2 loop en tick43 y permanece hasta tick300 (Y=500/vy=0 fixture). El switch `0x483f40` enruta action97 a `0x485115`; su landing gate solicita seq3 desde `0x4851e7` en tick17. En seq2 ya grounded/vy0 no pide otra secuencia; tampoco hay setters desde input neutral. Apagar solo el bit loop en una corrida artificial recorre más nodos PAT y no cambia action97. Falta localizar el callback/estado externo que inicia recuperación. Suite focal 7/7. [ITERATION255.md](ITERATION255.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

### Input, PAT, daño y reacción PE Suika 418 — Iteración 2.154

`0x609d40` construye PlayerSuika; input C+NRNR, matcher, dispatch 200→418, cleanup y 16 updates llegan al frame seq.2/pose.0 (PAT900). Se corrigió el harness para preservar los 40 bytes `combat_traits`: el byte `+0x26=100` produce daño 1200 y selección de reacción action74. Con HP de prueba 2000, el resolver `0x47c770` baja a 800 y deja al defensor en 74/seq0. EffectManager está stub y el estado del round/HP es controlado. El timer PE consume hitstop 10→0; la corrida de 300 ticks documentada en 2.155 muestra que action97 permanece en seq.2 loop mode 1, con suelo aún controlado. Es evidencia de caída y loop persistente, no del levantamiento. Próximo: integrar stage/fight/input managers, cotejar la salida del loop en replay y validar KO. [ITERATION254.md](ITERATION254.md), [reporte](../artifacts/x86-suika-constructed-handler.json).

### Handler completo de Suika alcanza el setter 418 — Iteración 2.148

El mismo harness ejecuta updates PE `0x46d5d0`, matcher `0x487020` y entra desde prólogo `0x609dc0` hasta `0x60be83`. Se corrigió el preestado: action 200 (`BX=0xc8`), no 300. KeyInput `[1,0]` y facing derecha hacen que el handler original solicite 418; el limpiador se alcanza, con cuerpo verificado aparte. Algunos servicios/estado/setAction se controlan; constructor Player, dispositivo, PAT, rival, colisión y replay completos pendientes. [ITERATION248.md](ITERATION248.md), [evidencia](../artifacts/x86-suika-input-matcher.json).

### Input PE y bloque Suika encadenados — Iteración 2.147 (corregida)

El matcher aún confirma N,R,N,R y NRNR. La versión inicial saltaba a un bloque interno con una precondición equivocada (300); no es evidencia de transición. Iteración 2.148 reemplaza ese salto por ejecución desde prólogo y acción previa 200. NRNR no es guard directo de 418. [ITERATION247.md](ITERATION247.md).

### Rama 418 del handler Suika ejecuta setter/limpiador originales — Iteración 2.146

Desde el bloque interno `0x60be34` del handler `0x609dc0`, el PE toma `0x60be83` cuando action=300, suelo verdadero, horizontal hacia delante y vertical actual cero; hace setter virtual 418 y corre `0x46cac0`, que borra buffered input. Seis casos pasan. El move-lock no se consulta dentro de esta rama. Aún falta ejecutar el prólogo/despacho completo, enlazar input matcher con el handler y correr update PAT/impacto contrastado con replay. [ITERATION246.md](ITERATION246.md), [evidencia](../artifacts/x86-suika-418-handler-branch.json).

### Matcher PE confirma NRNR; rama Suika 418 identificada — Iteración 2.145

`Deque<unsigned short>` ABI: proxy/tabla/bloques/offset/size en deque `+0/+4/+8/+0xc/+0x10`; 16 slots de tabla, 12 bloques de 8 words para size 90. Cuatro updates `0x46d5d0` y matcher `0x487020` PE con N,R,N,R producen muestras `0,2,0,2` y activan NRNR en el tick 4. Refresco físico aislado; regresiones focalizadas 4/4. Corrección importante: `0x4b0ac2` es handler de Reimu, no Suika. La rama Suika 418 está en `handleInputs=0x609dc0`, `0x60be83→0x60b721`; requiere acción 300, suelo, KeyInput horizontal relativo a facing y vertical actual cero. El move-lock no se consulta en esa rama. [ITERATION245.md](ITERATION245.md), [traza](../artifacts/x86-suika-input-matcher.json).

### KeyInput x86 alimenta guard 418 (handler de Reimu) — Iteración 2.144

El PE ejecuta `0x46c8e0/0x46d5d0`: horizontal=1 produce actual `[1,0]`/sample `0x02`; horizontal=1+A produce también buffered `[1,0]`, timer9/sample `0x12`. Ambas cadenas pasan el bloque `0x4b0ac2`, que es de Reimu y solicita 418; `0x46cac0` borra el buffer. Diez casos pasan. Device refresh, ring matcher, grounded/move-lock y setter están aislados. [ITERATION244.md](ITERATION244.md), [reporte](../artifacts/x86-suika-418-producer.json).

### Localizado caller PE que solicita la acción 418 — Iteración 2.143

La ruta `0x4b0ac2` ejecutada bajo Unicorn solicita 418 con horizontal actual o buffered hacia facing y vertical actual neutral; los ocho casos confirman rechazo por guards y limpieza original de `bufferedKeyInput`. `+0x778` no es un requisito de este caller. Suelo, move-lock y setter fueron aislados; falta el loop de input/KeyManager y la implementación virtual concreta de Suika. [ITERATION243.md](ITERATION243.md), [reporte](../artifacts/x86-suika-418-producer.json).

### Gate PE de aterrizaje explica transición de Suika 418 seq2→seq5 — Iteración 2.142

El helper `0x487ea0` comprueba límite vertical del stage vía `0x4397f0`, velocidad vertical no positiva y bandera `Player+0x4c4` despejada. En tick27 retorna verdadero y el caller solicita seq5; tick26 aún tiene `vy=0`. Suite Python 119/119. La fixture conserva Y=0 y acción inyectada, por lo que confirma la rama del PE pero no un salto natural. Siguiente: inicializar límite y física reales, cruzar suelo dinámicamente y ubicar el productor de 418 desde input. [ITERATION242.md](ITERATION242.md), [traza](../artifacts/x86-suika-418-sequence.json).

### PE de Suika 418 confirma windup y ventana de ataque en seq2 — Iteración 2.141

Con tabla PAT efectiva, el setter original inicia 418 en seq0; el update pasa a seq1 en tick8 y seq2/pose0 en tick16 (daño 900, una hitbox), activo hasta tick26. En tick27 salta a seq5 y luego el campo llega a 6, por lo que no se debe asumir una animación lineal ni igualar ese campo a índice PAT. Pruebas focalizadas 11/11, suite Python 119/119. El setter está inyectado, sin ruta de input natural. Próximo: observar las escrituras de `Player+0x13e` y guards alrededor de tick27; solo después implementar transiciones en `fight.c`. [ITERATION241.md](ITERATION241.md), [traza](../artifacts/x86-suika-418-sequence.json).

### PAT crudo separado de la definición que usa el decoder — Iteración 2.140

El extractor de secuencias ahora conserva inventarios crudos y ofrece `effective=True` para reproducir la regla de reemplazo de `t123_pattern_decode`; el oracle de parejas usa esta última. Las 118 pruebas Python pasan. Suika 418 baja de 12 registros crudos a seis efectivos, con índice 2 ofensivo; Udonge index 1 y Utsuho index 1. El selector runtime del PE sigue sin recuperarse y estos índices describen PAT, no la elección dinámica. Siguiente: ejecutar setters/updates x86 y comparar índice, tiempo y hitbox para 418 en esos tres personajes antes de cambiar el motor. [ITERATION240.md](ITERATION240.md), [resumen PAT](../artifacts/pat-action-418-effective-summary.json).

### VPK recompilado y gate SDL de 600 frames repetido — Iteración 2.139

El VPK autotest reconstruido del árbol actual pasa Vita3K SDL schema46/600 con evidencia fresca; Python pasa 117/117. Quedó documentada la opción `-BuildDirectory` para ubicar intermedios fuera de `artifacts/`. Esto valida el prototipo y los gates enumerados, no paridad del juego completo. Prioridad de fidelidad: recuperar los selectores PE de variantes PAT por personaje/acción y reemplazar la heurística; después ampliar acciones/cancelaciones y validar con replay temporal. Faltan además roster completo jugable, cartas, mecánicas de todos los escenarios, clima/audio y hardware. [ITERATION239.md](ITERATION239.md).

### Replay Story compara el contador y retorna en mismatch — Iteración 2.138

El `.rep` Sanae y el PE 2009 verificados vuelven a pasar 16,910 parejas Story y 33,820 words de `0x481040`. Se amplió el disassembly de la rutina Story: compara el word actual con `[0x85eb58]`; mismatch retorna por `0x45fe70` sin consumir y equality consume con `0x42a3a0`. Corrige la etiqueta previa de “wait-sync”: es sincronización condicional, no busy wait. Aún falta caller/cadence por tick y playback en vivo; no conectar el cursor a Vita bajo timing supuesto. Evidencia: [ITERATION238.md](ITERATION238.md).

### PE acota la geometría estática de Udonge 418:1 — Iteración 2.137

El probe x86 mide posiciones/facing ejecutando sync, transforms y hit-vs-hurt originales. Udonge 418:1/pose0 vs 400:0/pose0, atacante X=320/facing+1 y defensor facing-1, conecta en X defensor 320–450; bordes finos 318/320 y 458/460. Con facing invertido, X=320 conecta y X=322 no, así que la geometría no es espejo simple. Sigue siendo pose estática con cámara/escenario, stats y tiempo controlados; el resolver sale en `0x0` tras daño. Próximo: recuperar cadence temporal y estados reales del juego/replay para validar el runtime con cajas PE comparables. Evidencia: [ITERATION237.md](ITERATION237.md).

### Oracle x86 ejecuta transform de caja de ataque; falta pareja completa — Iteración 2.136

El PE 2009 fijado ejecuta `0x4640b0` para siete cajas de ataque de Udonge 418:1/pose0, y `0x47a5b0` devuelve contacto ante la hurtbox controlada; el resolver alcanza daño 1133 en la escala del fixture y termina luego en `0x0`. `0x464200` no aparece aún y la hurtbox defensora no está transformada, así que no se infiere alcance natural. En Vita, nueve offsets de dash no producen intersección completa; horizontal y vertical aparecen por separado. B 18/20, C 17/20. Próximo: ejecutar el transform de defensa en el sincronizador y medir ambas cajas bajo posiciones relativas controladas antes de modificar el resolver. [ITERATION236.md](ITERATION236.md).

### Métrica C 418 corregida para ventanas activas — Iteración 2.135

La señal anterior contaba cajas coincidentes en poses sin daño y no demostraba contacto. Ahora exige pose dañina, hitbox y latch disponible; además registra separación central y brecha vertical. Vita3K pasó schema46/600; Reimu conecta 418:0/900, pero los C naturales de Suika, Udonge y Utsuho todavía no conectan. Próximo: medir brecha horizontal de cajas simultánea con vertical y cotejar facing/movimiento con x86 antes de cambiar runtime. Evidencia/VPK: [ITERATION235.md](ITERATION235.md).

### Udonge B aéreo 409 conecta con PAT 1; B natural 18/20 — Iteración 2.134

El diagnóstico halló que el runtime alcanzaba acción 409 con índice PAT 0, que no tiene caja; al seleccionar la variante con ataque `409:1`, Udonge/Tenshi/Cirno conectan. Vita3K exige Udonge acción409/variante1/frame12/400 de daño; la cobertura B natural sube a 18/20. Aún no se ha probado que el selector heurístico sea el mismo del PE. C normales: 17/20. VPK/evidencia: [ITERATION234.md](ITERATION234.md); siguen pendientes selector PE, B de Reimu y C de Udonge/Suika/Utsuho.

### Diagnóstico B/C por roster amplía distancias y registra 623C especial — Iteración 2.133

La prueba ahora barre tres posiciones naturales del rival y registra separación de conexión; Alice conecta 66B/66C por PAT 849. Cobertura observada: B normal 15/20, C normal 17/20; Suika 623C queda inventariado separadamente en base/nivel5/nivel9 (521/1000, 526/500, 531/800). Faltan B para Reimu, Remilia, Udonge, Tenshi y Cirno; C normal para Suika, Udonge y Utsuho. Vita3K SDL schema46/600 pasó con esas aserciones y gates previos. Detalle y VPK: [ITERATION233.md](ITERATION233.md). La prueba no cubre todos los matchups ni la paridad del selector original.

### Suika 623B: ventana de vida y reacción x86 cotejadas — Iteración 2.132

El PAT 821 de 530 conecta en el cuadro de creación y se retira antes de una segunda colisión; en suelo, la reacción conserva acción 50 y timer 20. Vita3K ahora exige una conexión, retiro al siguiente tick y ausencia de daño repetido (route mask 127), además de las verificaciones anteriores. VPK/hashes y limitaciones: [ITERATION232.md](ITERATION232.md). Queda probar con movimiento/replay natural y sincronizar el RNG global; el roster, la progresión de cartas y la paridad de escenarios siguen incompletos.

### Herramienta para la fase de Vita física: psp2-tooling

Evaluada y confirmada como herramienta útil para **M7 (pruebas en Vita física)**, no para el trabajo de reconstrucción que estamos haciendo ahora. El README upstream documenta control USB, instalación/lanzamiento, entrada, captura HDMI, dumps y perfiles CPU/GPU; el host es Linux. Ahora podemos preparar y validar la pelea en Vita3K y continuar el análisis x86; más adelante, con escena integrada, Linux y consola, `devkit/` puede automatizar la prueba y `profile/`/`razor/` ayudar a localizar límites de CPU/GPU. Preferir DevKit. `retail-cp` queda como vía opcional y estrecha: upstream declara PCH-2000, FW 3.65, Ensō/taiHEN y módulos DevKit 3.65 proporcionados aparte; no instalarlo hasta verificar ese entorno. Para stacks, compilar ELF con `-g` y SELF sin ASLR. Detalle y fuente: [ANALYSIS_AND_TESTING_TOOLING.md](ANALYSIS_AND_TESTING_TOOLING.md#validación-futura-en-ps-vita-física), [psp2-tooling](https://github.com/Grarak/psp2-tooling).

### Suika 623B nivel 9: acción 530 crea PAT 821 e impacta — Iteración 2.131

Se portó el evento PE de pose 7/update 20, factory `0x335`→PAT 821, los cuatro draws de MT19937 y el spawn. Vita3K alcanza daño 800 y coincide con el spawn calculado desde la salida x86 (`350.62018,81.13176` en el fixture). La prueba usa defensor fijo en el área del efecto y RNG semilla 5489; aún falta replay/entrada de partida con Suika para medir alcance contra movimiento natural y sincronizar la secuencia RNG global una vez haya otros consumidores. Suite C 10/10, Python 115/115 y gate Vita3K 600 frames; detalle/hashes: [ITERATION231.md](ITERATION231.md).

### Suika 623B nivel 9: PAT 821 y barrido de alcance del resolver PE — Iteración 2.130

El factory x86 crea PAT 821 con 800 de daño. Una cuadrícula alrededor del spawn `(344.62,261.13)` da contacto en 56/121 posiciones y el centro activa la respuesta original PE. La iteración 2.131 porta el spawn/caja a Vita. El barrido sigue siendo geometría controlada, no alcance contra rival móvil. Evidencia: [ITERATION230.md](ITERATION230.md).

### Suika 623B y 623C por niveles — Iteración 2.128

Suika 623B está conectado a su dispatcher x86: nivel9→530, nivel5→525, base→520 y ambos niveles bloquean. Vita3K verifica impactos 1000/500 y activación 530; también pasan rutas 623C/PAT 821 y escenarios. La evidencia y límites están en [ITERATION228.md](ITERATION228.md). Siguiente: reconstruir efectos de 530 y enlazar niveles a cartas; expandir comandos/skills por el roster, comparar combate con replay y completar escenarios. Sigue sin demostrar paridad total ni probar hardware físico.

### Suika 623C selecciona 521/526/531 según nivel; cuatro ramas pasan Vita3K — Iteración 2.123

El estado de lucha incluye niveles 5/9 y el matcher reproduce las cuatro combinaciones del dispatcher original: base 521 (1000 en dos hits), nivel5 526 (500), nivel9 531 (activación sin daño atribuido) y ambos niveles bloqueados. Gate Vita3K schema46/600 cuadros con máscara 15; Python 114/114. Falta enlazar esos niveles con progresión/cartas y reconstruir la ruta de objetos/efectos de 531; sigue pendiente replicar las otras skills. [ITERATION223.md](ITERATION223.md).


### Suika 623C conecta las dos ventanas PAT de acción 521 — Iteración 2.122

La integración ya aplica los golpes authored de 400 y 600, rearmando el latch al salir de cada pose dañina. Vita3K schema46/600 frames pasó y verificó `hit_delta=1000`; suite Python 114/114. Siguen pendientes las rutas 526/531 y sus niveles; el probe original distingue nivel9→531, nivel5→526, cero→521, ambos→sin activación. La acción 531 aún requiere entender su semántica completa. Evidencia: [ITERATION222.md](ITERATION222.md).


### Primera ruta especial de Suika 623C alcanza PAT 521 y conecta 400 de daño — Iteración 2.121

El matcher de 15 muestras dispara Suika 623C y el gate Vita3K verifica la acción PAT 521, una activación y un impacto real de 400 usando DAT local. Build schema46/600 cuadros aprobada; suite Python 114/114. Esta es la ruta base con niveles efectivos consultados en cero: falta replicar la transición/segundo impacto que el probe de acción x86 sugiere, obtener el selector completo por nivel y extender las skills al roster. Evidencia y hashes: [ITERATION221.md](ITERATION221.md).


### VPK del árbol actual reconstruido y validado — Iteración 2.120

Se generaron de nuevo los VPK interactivo/autotest con el código actual; ambos comparten `eboot.bin` SHA-256 `d1d730c7849097d8b78a09e75ccc708b2668a9b39cf1e716c9a39abd2879fdf5`. El autotest pasó Vita3K SDL schema46/600 cuadros (`status=passed`) y la suite Python completa pasó 114/114. Hashes, capturas, reporte y límites de cobertura: [ITERATION220.md](ITERATION220.md). Esto valida la build instrumentada, no paridad total.

### Replay: decoder y avance del contador enlazados a una invocación Story — Iteración 2.119

Se cerró el orden interno del slot 5: `0x47f810` llama al decoder Story por slot 16 en `0x47f82e` y después a `0x478640` en `0x47f84e`. Ese helper despacha slot 15 en `0x478648`; el destino Story `0x47f7c0` reinicia `[0x85d74c]` y salta a `0x4787f0`, que incrementa `[0x85eb58]`. El probe SHA-pinned ahora verifica la cadena y pasa 53 checks. Con esto queda probado un consumo de palabra y un incremento del contador por ejecución del slot 5; todavía falta establecer cuántas ejecuciones hay por tick/render y obtener playback frame-stepped. Evidencia: [ITERATION219.md](ITERATION219.md).

### Replay: slot 5 Story llama slot 16; cadence aún sin caller probado — Iteración 2.118

Se precisó que el caso 3 de `0x43d480` llama al wrapper `0x437790`, que despacha el slot 1 de `[0x85eb64]` a `0x47eaa0`; no establece el tick que invoca el slot 5. La Iteración 2.119 conecta desde el slot 5 el decoder al incremento de `[0x85eb58]` por medio del slot 15. Probe/test SHA-pinned pasan, 52 condiciones en ese punto. Evidencia: [ITERATION218.md](ITERATION218.md), [ITERATION219.md](ITERATION219.md).

### Validación del VPK actual y herramienta para hardware — Iteración 2.117

Build nativa con VitaSDK 2026.08 desde el árbol actual: VPK interactivo `artifacts/Touhou123Vita-current.vpk` (SHA-256 `28687a897ab8bc773e98b62d5502c9422c175d3689d707a099b0f8c6585e619b`) y autotest `artifacts/Touhou123Vita-current-auto.vpk` (SHA-256 `8a109a285c0587530c48231bf1347b6daafe7d2b99a95210b0d533f74345965a`). El segundo pasó en Vita3K SDL con schema 46, 600 cuadros, `status=passed`, regresión, recorte PAT, sonda de objetos y contratos/capturas de escenario; resultado fresco en `artifacts/vita3k-result.json`. Esto cubre el prototipo actual, no paridad completa de roster, mecánicas, fondos ni reproducción del juego.

Se evaluó [psp2-tooling](https://github.com/Grarak/psp2-tooling): aporta automatización USB/host0, entrada, capturas, volcados y perfilado CPU/GPU para PS Vita física, por lo que puede servir al medir rendimiento después de integrar una escena representativa. No interviene en la decompilación x86, compilación VitaSDK ni pruebas Vita3K. Su ruta DevKit requiere Linux y configuración/módulos de desarrollo; `retail-cp` documenta un caso limitado a Vita PCH-2000 con firmware 3.65, Ensō/taiHEN y módulos DevKit 3.65 aportados aparte. Decisión: conservarlo como herramienta externa de la fase de hardware; no instalar el plugin retail ni cambiar el ciclo de trabajo actual. Detalle: [ITERATION217.md](ITERATION217.md).

### Replay: dispatcher de Story ubicado; cadence del callback pendiente — Iteración 2.116

El caso 3 del dispatcher de lifecycle llega al slot 1 del manager Story (`0x47eaa0`); por sí solo no demuestra el tick de combate. El callback que consume pares (`0x47ee10`) pertenece al slot 16 y se invoca desde el slot 5 (`0x47f810`), según Iteración 2.118. Sigue pendiente identificar quién ejecuta ese slot 5 por tick/render. No había proceso `th123` activo al obtener la evidencia estática inicial. Evidencia: [ITERATION216.md](ITERATION216.md), [ITERATION218.md](ITERATION218.md).

### Replay: rama de fila seleccionada llega al loader — Iteración 2.115

El update del menú `0x449fe0` pasa la guarda de selección activa, consulta la bandera de la fila (`0x43ba50`) y divide navegación vs carga. Si la bandera vale cero, lee ambos componentes del elemento seleccionado, los formatea y llama al loader `0x42e030`; si vale distinto de cero, actualiza la lista. Esto identifica la rama de carga de archivo, sin asumir aún una tecla física concreta. La traza dinámica sigue pendiente para correlacionar entrada y tick/cursor. Probe con 46 contratos pasa; evidencia: [ITERATION215.md](ITERATION215.md).

### Replay: CReplayList y la entrada Sanae conectados estáticamente — Iteración 2.114

RTTI y vtable identifican `CReplayList` (`0x82133c`); su constructor (`0x42bbd0`) fija el filtro `*.rep` y la raíz `replay`, y su slot virtual 1 (`0x43c140`) enumera archivos. La rutina `0x42c0a0` forma la plantilla Story `replay\story\%02d%02d%02d_%02d%02d_%s_story`, compatible con `090815_2219_sanae_story.rep`. El handler de selección toma la fila/index, arma el path y llama al loader `0x42e030`, que en éxito cambia al estado de replay. Esto conecta el archivo con la lista y el loader por análisis estático. Sigue pendiente observar en vivo el evento de confirmación y asociar cada avance de secuencia con ticks del combate. Probe SHA-pinned y test pasan; evidencia: [ITERATION214.md](ITERATION214.md).

### Replay: selección de modo y loader `.rep` separados en CTitle — Iteración 2.113

El handler de selección `0x447c0c` comprueba el índice actual; cuando es 0 solicita estado 12, guarda el valor asociado 6 y llama al helper de transición `0x447310`. El método distinto `0x44a120` construye un path y llama al loader genérico `0x42e030`; si tiene éxito escribe estado 6. Combinado con Iteración 2.112 (estado 12 → manager modo 6/estado 2), esto indica que estado 12 es una entrada de modo Story y que la carga `.rep` es un paso separado. Aún falta mapear el índice a las etiquetas visibles y demostrar en vivo qué selección activa `0x44a120` con Sanae. Probe y test específico pasan. Evidencia: [ITERATION213.md](ITERATION213.md).

### Replay: CTitle state 12 llega a Story mode — Iteración 2.112

La RTTI identifica `0x426d50` como slot 1 de `CTitle`; su tabla de estados enruta estado 12 a `0x426de2`, que solicita `(modo=6, estado=2)`. Estados 8/9 solicitan modos 4/5, estado 1. Esto conecta title→manager Story, pero aún no demuestra que estado 12 sea específicamente Replay ni que cargue el Sanae `.rep`. Sigue localizarse la selección y el loader de registros. Evidencia: [ITERATION212.md](ITERATION212.md).

### Replay: separar setup de input/config del camino Story — Iteración 2.111

El caller `0x425703` dispara `0x43dee0` solo con selector 1; con selector 0 llama al setup de una fuente. `0x44af00` establece modo 7/estado 1 y también usa setup de una fuente; `0x4209c1` es un handler condicionado cuyo selector global sigue dinámico. Ninguno prueba `f0` del replay Story. Falta enlazar el callsite Story `(6,2)` con un caller/estado live. Evidencia: [ITERATION211.md](ITERATION211.md).

### Replay: callers del setup de input identificados — Iteración 2.110

La búsqueda de `CALL rel32` localiza `0x43dee0` desde `0x420a91/0x4258fe` y el setup de fuente única `0x43ccf0` desde `0x4258ec/0x44b091`. Las guardas locales distinguen inicialización con modo cero y una transición de backend, pero falta reconstruir sus funciones contenedoras y demostrar la secuencia en replay Story. La captura dinámica no estuvo disponible: el helper de ventanas no pudo inicializar recursos y el proceso original no estaba abierto. Evidencia: [ITERATION210.md](ITERATION210.md) y el reporte actualizado.

### Replay: inventario completo de slots de backend — Iteración 2.109

La tabla `0x43e248` mapea selectores 1/2/8 a un solo slot (`0x85ef20/null`), 3 a dos slots fijos (`0x85ef20/0x85f70c`), 4/5 a dos slots del manager (`+0x1f0/+0x1f8`) y 6/7 a una ruta que no los escribe directamente. La inicialización común `0x43ccf0` establece un solo slot. El writer calcula `f0` con la presencia de ambos punteros; modo 6 hereda el estado, así que sigue faltando identificar su secuencia real de inicialización. Evidencia y reporte: [ITERATION209.md](ITERATION209.md), `artifacts/kernel/replay-manager-selection-original-2009.json`.

### Replay: modo 6 no demuestra dos fuentes activas — Iteración 2.108

El dispatcher de input `0x43dee0` usa el índice `[0x85ec10]-1`: el selector 6 entra a la ruta común `0x43e122`, que no asigna los slots `0x8602ac/0x8602cc`; las asignaciones explícitas de dos punteros (`0x85ef20/0x85f70c`) pertenecen al selector 3. Las dos ranuras internas del manager Story tampoco bastan para inferir `f0=3`. Siguiente: seguir la preparación efectiva de fuentes y el momento en que `0x42d6b0` actualiza `+0xf0`, luego medir cadence por frame. Evidencia: [ITERATION208.md](ITERATION208.md).

### Replay: todas las parejas ejecutadas por el callback Story x86 — Iteración 2.107

`0x47ee10→0x42a410` ejecutado en Unicorn consume los 33,820 words del Sanae replay como 16,910 parejas, con máscaras de ambos canales y seis flags primarios cotejados por invocación. El harness fuerza `f0=3`; no prueba fuentes activas naturales ni llamadas por frame. Siguiente: medir configuración real y cadence mediante frame-step antes de portar playback. Evidencia: [ITERATION207.md](ITERATION207.md).

### Replay: callback Story ejecutado sobre el PE — Iteración 2.106

Unicorn ejecuta `0x47ee10`: con estado `[0x85ec08]=2` llama una vez a `0x42a410` con `ECX=0x85ec98`; con estado 1 omite el decoder. Se confirma gating/objeto, no consumo del `.rep`, selección desde el menú ni cadence. Siguiente: conectar transición del replay y luego ejecutar decoder real por llamada. Evidencia: [ITERATION206.md](ITERATION206.md).

### Replay: input compartido Story→decoder; modo 6/estado 2 — Iteración 2.105

El callback Story `0x47ee10` y el escritor de fuentes `0x42d6b0` operan sobre `[0x85ec98]`; una ruta en `0x426de6` pide selector 6 y estado 2, que activa el decoder. La ruta es compatible con replay Story, pero todavía no se confirmó que ese bloque sea el usado por el archivo Sanae ni si hay una/dos fuentes activas. Siguiente: cerrar la entrada al replay y medir cadence. Evidencia: [ITERATION205.md](ITERATION205.md).

### Replay: ciclo global separa manager y modo — Iteración 2.104

`0x43d480` despacha por `[0x85ec0c]`: estado 2 selecciona/inicializa vía `0x43cca0`, estados 3–5 llaman rutas de update; el modo `[0x85ec10]` elige variante y lo escribe `0x43d8e0`. Las rutas Story son modos 0/6. Falta recuperar ambos valores durante playback y medir frecuencia por frame. Evidencia: [ITERATION204.md](ITERATION204.md).

### Replay: selector Story acotado a modos 0/6 — Iteración 2.103

`0x43cca0` selecciona `0x43b440` en modo 0 y `0x4378d0` en modo 6; ambos escriben el manager Story a `[0x85eb64]`. `0x42d6b0` calcula flags de fuente para el objeto global de input `[0x85ec98]`, pero su identidad con el `this` del decoder no está probada. Siguiente: obtener el modo efectivo del replay y seguir la ruta hasta el decoder, después medir cadence frame-step. Evidencia: [ITERATION203.md](ITERATION203.md).

### Replay: manager Story y canales son estados separados — Iteración 2.102

`0x85eb64` apunta al manager Story y los inicializadores observados lo asignan con vtable `0x82192c`; esto relaciona la instancia global con los callbacks, pero aún no identifica el constructor tomado en la sesión Sanae. `0x42a410` consume cada canal según los bits 0/1 de `this+0xf0`, por lo que `f0=3` no debe tratarse como configuración universal. Siguiente: seguir callers de inicializadores y escritor de `f0`; obtener frame-step del PE antes de conectar cadence. Evidencia: [ITERATION202.md](ITERATION202.md).

### Replay: slot Story resuelto por RTTI del PE — Iteración 2.101

Las tablas RTTI y constructores fijan el slot virtual 16 de `CBattleManagerStory` a `0x47ee10`; base y Arcade apuntan a `0x481040`. Esto resuelve cuál callback invoca una instancia Story, pero no confirma todavía el objeto creado para la sesión Sanae, el estado de fuente `f0` ni la cadence por frame. Próximo: seguir el global de manager `0x85eb64` y el decoder en la ruta Story; después capturar frame-step del juego PC. Evidencia: [ITERATION201.md](ITERATION201.md).

### Cursor C agrupa los dos canales por llamada — Iteración 2.100

El contrato C consume de forma atómica la pareja de words del decoder x86 bajo `f0=3`; un VPK de prueba recorrió las 16,910 parejas del replay Sanae real en Vita3K con salida 0. El auto-VPK del proyecto pasó schema46/600 frames y el VPK interactivo comparte su eboot probado. Falta observación frame-step para medir cadence/orden de controladores y resolver `0x4600fe`; no hay playback conectado al combate. Evidencia y hashes: [ITERATION200.md](ITERATION200.md).

### Replay Sanae: 33,820 words revalidados contra el update x86 — Iteración 2.99

Se ejecutó `0x481040` del PE original sobre todos los words del replay de tres peleas; cada invocación conservó el word, despachó flags comprobados e incrementó el índice, incluida la guarda de fin. Falta resolver la cadencia respecto a frames y el orden de ambos jugadores; no se afirma playback y no se conectó aún a Vita. Evidencia: [ITERATION199.md](ITERATION199.md).

El replay compatible ya está localizado: `090815_2219_sanae_story.rep` más el PE 2009 del usuario. El próximo gate de replay no es buscar otra muestra, sino capturar frame-step en PC para relacionar word/cursor, callbacks y tick; los slots x86 aún no tienen callers demostrados y el intento de automatización UI local falló por kernel assets faltantes. Actualizar [ANALYSIS_AND_TESTING_TOOLING.md](ANALYSIS_AND_TESTING_TOOLING.md).

### Build con recorte PAT revalidada en Vita3K — Iteración 2.98

El auto-VPK más reciente volvió a pasar schema46/600 frames, regresión, recorte desplazado y contratos actuales de escenario en Vita3K SDL; el VPK interactivo comparte exactamente su `eboot.bin` y queda disponible para revisar. La captura confirma render de Reimu/Cirno y fondo, pero no paridad pixel-perfect. Continúan pendientes la captura dinámica original, combate completo, rutas faltantes del roster y las mecánicas/composición de todos los stages. Evidencia y hashes: [ITERATION198.md](ITERATION198.md).

### Los callers del sampler de escenario restauran WRAP — Iteración 2.97

El inventario estático de 30 llamadas a `SetSamplerState` agrupó inicialización, SpriteEx y callbacks de escenario. Los callbacks SpriteEx, BG02 y BG33 revisados usan CLAMP solo durante sus draws y reponen U/V a WRAP al retornar; el callback de jugador no tiene escritura local del sampler. La expectativa de muestreo PAT es WRAP si se respeta el orden de callback, pero quedan la traza dinámica del frame y captura visual de los ocho recortes extremos. Evidencia: [ITERATION197.md](ITERATION197.md).

### WRAP fijado al inicio para samplers 0/1 — Iteración 2.96

El PE configura `ADDRESSU/V=WRAP` para sampler 0 y 1 en la inicialización. La ruta SpriteEx asigna U/V por objeto, pero el epílogo repone WRAP; el draw directo del jugador tampoco cambia esos campos. Iteración 2.97 completó el inventario de 30 callers y las restauraciones estáticas conocidas; queda medir/capturar los PAT extremos en ejecución. Evidencia: [ITERATION196.md](ITERATION196.md), [ITERATION197.md](ITERATION197.md).

### Ruta de dibujo x86 de recortes extremos confirmada — Iteración 2.95

`0x466720→0x406c60→0x406d30` crea el componente/UV y `0x4075d0` somete su quad a Direct3D sin descartarlo por rango o flags. Siete texturas tienen borde opaco y una de Sakuya es transparente. D3D9 usa WRAP por defecto, así que el tiling es la hipótesis actual; falta probar si el PE cambia el sampler global y capturar un frame del original. No se cambia el runtime Vita todavía. Evidencia: [ITERATION195.md](ITERATION195.md).

### Campos de variante preservados en recortes PAT extremos — Iteración 2.94

La auditoría encontró ocho descriptores no convencionales de origen entre 17,586 secuencias: siete de `alpha000.bmp` y uno de `attackAa000.bmp`. El extractor conserva `flags` y el bloque opcional, sin confundirlos con evidencia de invisibilidad ni cambiar el runtime. La siguiente iteración siguió la ruta de dibujo x86. Evidencia: [ITERATION194.md](ITERATION194.md).

### Contrato de recorte PAT probado también dentro del guest — Iteración 2.93

El auto-VPK ahora ejecuta un test del rasterizador Soft2D con una textura 4×4 sintética y recorte desplazado; verifica los cuatro píxeles del interior y que no se dibujen los bordes excluidos. Vita3K reportó `sprite_region_crop_contract=1` y volvió a pasar schema46/600 cuadros junto con los gates anteriores. El inventario de los 20 PAT halló ocho registros con origen no cero (siete `alpha000.bmp`, uno `attackAa000.bmp`); su semántica queda por trazar en x86. Evidencia y VPK: [ITERATION193.md](ITERATION193.md).

### Origen/tamaño del quad PAT verificados con el constructor x86 — Iteración 2.92

Un nuevo oracle ejecuta `0x406c60` del PE fijado con dimensiones de textura controladas: `tw/th` definen el tamaño del quad y UV termina en `tx+tw, ty+th`. Esto descubrió y corrigió el uso incorrecto de ancho/alto como límites absolutos en el renderer de jugadores y objetos; ahora se envían extremos calculados. Vita3K volvió a pasar 600 cuadros y schema46. El origen PAT y la escala de mundo/cámara todavía necesitan una fixture visual sincronizada. Evidencia, hashes y límites: [ITERATION192.md](ITERATION192.md).

### Campos del quad PAT conectados al renderer 2D — Iteración 2.91

La sonda SHA-pinned confirma el layout en disco y la reorganización del loader x86: el runtime conserva `ox/oy` en `+4/+6`, `tx/ty/tw/th` en `+0xc..+0x12`, aplica signo a las coordenadas y normaliza el rectángulo contra la textura. El renderer Vita ya dibuja el recorte PAT y aplica `ox/oy` como origen firmado con facing y cámara. Vita3K SDL pasó 600 cuadros/schema46; la captura deja ver ambos sprites completos, pero el overlay oculta el piso y no demuestra paridad visual exacta. El anclaje y la escala en unidades de juego siguen en calibración con poses/replays de referencia. VPKs y evidencia: [ITERATION191.md](ITERATION191.md).

### Inicialización del sprite del jugador localizada — Iteración 2.89

El renderer de Reimu ya está identificado: slot 11 → `0x438d20` → `Player+0x154` → `0x4389d0` → cámara. `0x466670` copia palabras con signo a `+0xf0/+0xf4`, pero la composición de esos offsets con el origen/quad aún no se ha cerrado. Evidencia: [ITERATION189.md](ITERATION189.md) y la corrección experimental de [ITERATION190.md](ITERATION190.md).

### Cámara de combate conectada al estado y a los sprites — Iteración 2.88

El slot 11 del vtable de jugador apunta a `0x438d20`, que dibuja `Player+0x154` mediante `0x4389d0` y la cámara `0x4293f0`; falta mapear los campos locales de ese componente contra las poses PAT. La cámara ya avanza con las posiciones de `Fight` y proyecta sprites, objetos y piso durante combate; menús y tarjetas conservan la vista neutral. El VPK interactivo actual comparte el eboot probado por Vita3K. Próximo: mapear la posición/escala del componente del luchador y recuperar su anclaje Y completo y sustituir el fondo provisional por la composición/scroll real del stage. Evidencia: [ITERATION188.md](ITERATION188.md).

### Cámara por tick lista en core; conexión a pelea pendiente — Iteración 2.87

Se combinó el refresco de target y el easing X/Y/zoom en `t123_stage_camera_step`, comparado con el PE y ejecutado dentro del gate de Vita3K. Aún no modifica `Fight` ni el dibujo. Primero hay que demostrar la conversión de coordenadas del prototipo a las del escenario original; luego se conecta la cámara viva al renderer de sprites y capas. Detalle: [ITERATION187.md](ITERATION187.md).

### Siguiente: integrar la cámara dinámica al combate — Iteración 2.86

Target, easing X/Y y zoom ya tienen helpers comparados con el PE; el paso pendiente es alimentarlos con las posiciones reales de ambos jugadores en cada tick y aplicar el viewport a la composición de los fondos. Después, contrastar una ronda completa y perfilar en Vita física. El helper Y de esta iteración todavía no está conectado al renderer de combate. Evidencia: [ITERATION186.md](ITERATION186.md).

### Target vertical dependiente del zoom — Iteración 2.85

El target Y de la cámara se portó con ramas por altura mínima y zoom, validado contra x86/Vita3K. Falta easing por cuadro e integración en combate. Evidencia: [ITERATION185.md](ITERATION185.md).

### Cámara vertical: constructor original emulado — Iteración 2.84

El constructor x86 completo produce fixtures de target/posición/viewport Y y corrige la hipótesis anterior basada en estado artificial. Aún faltan easing vertical en core y conexión al combate. Evidencia: [ITERATION184.md](ITERATION184.md).

### Easing horizontal de cámara contrastado con el PE — Iteración 2.83

El update X y los límites del viewport se portaron y compararon con Unicorn; el VPK pasa Vita3K. Falta el eje Y y usar el estado en combate. Evidencia: [ITERATION183.md](ITERATION183.md).

### Easing de zoom medido en el update x86 — Iteración 2.82

El paso por cuadro del zoom está portado y comparado con la rutina original en ambos sentidos; el VPK automático mantiene la regresión integral en Vita3K. Faltan los pasos X/Y y conectar la cámara a la pelea. Evidencia: [ITERATION182.md](ITERATION182.md).

### Centro automático de cámara contrastado con el PE — Iteración 2.81

Centro X/Y y zoom objetivo están recuperados como función de posiciones y validados por oracle x86 y Vita3K. Falta el update temporal `FUN_00429040`, overrides persistentes e integración al render de pelea. Evidencia y VPK: [ITERATION181.md](ITERATION181.md).

### Zoom automático de cámara contrastado con el PE — Iteración 2.80

El método original fija el zoom a partir de la separación de los jugadores; la fórmula ya está en el core y en un gate del VPK. La suite completa pasa 102 pruebas y Vita3K valida 600 cuadros/schema46. Centro de cámara, easing y cámara conectada al combate siguen abiertos. Evidencia y VPK: [ITERATION180.md](ITERATION180.md).

### Proyección PE de los cuatro auxiliares BG36 — Iteración 2.79

La vista aplica el transform de viewport a torii y nubes con pivotes/anclajes del PE, y el autotest comprueba coordenadas de los cuatro slots. Vita3K 600 cuadros y Python 100/100 pasan; esto sigue siendo una referencia de cámara cero. Próximo: recuperar la actualización de cámara y usarla para dibujar los escenarios en combate. Evidencia: [ITERATION179.md](ITERATION179.md).

### Gate acumulativo de nubes BG36 — Iteración 2.78

La navegación borraba el contador diagnóstico al volver a BG36 tras capturar la página. La evidencia ahora se conserva durante la corrida: cuatro proyecciones, gate Vita3K aprobado a 600 cuadros y Python 100/100; el binario del VPK interactivo coincide con el probado. Sigue pendiente cámara viva, composición real del escenario e integración en combate. Evidencia: [ITERATION178.md](ITERATION178.md).

### Anclaje y pivotes de nubes BG36 — Iteración 2.77

Ambos pases de nube usan el mismo anclaje del escenario y sus pivotes de constructor determinan el origen local: `clowd_l` parte del anclaje y `clowd_s` usa centro inferior. El core, el visor y los contratos reflejan esa relación. Captura y VPK pasan Vita3K; cámara, proyección/escala exactas y composición jugable aún requieren reconstrucción. Evidencia: [ITERATION177.md](ITERATION177.md).

### Recursos BG36 y extracción reproducible de renderers — Iteración 2.76

El visor inspecciona los cuatro auxiliares del constructor BG36 y el nuevo exportador fijado al PE produce instrucciones de los tres renderers. El VPK automático sigue pasando Vita3K y la suite completa. El siguiente bloque requiere reconstruir con esas instrucciones el anclaje/tamaño de nubes, cámara y capas, y después probar un escenario dentro del combate. Evidencia: [ITERATION176.md](ITERATION176.md).

### Mapeo de slots del renderer BG36–BG38 — Iteración 2.75

El orden del constructor enlazado con las instrucciones de renderer confirma transforms por recurso: BG36 desplaza los dos torii; BG37 mueve `tori1` y `clowd_l`, con `clowd_s` fijo en (492, −401); BG38 mueve sus dos nubes. Los VPK nuevos pasan 600 cuadros en Vita3K y Python 100/100. Esto valida el visor de diagnóstico y los callbacks, no la reproducción completa: siguen pendientes la cámara, composición alpha/parallax, las pasadas de nubes de BG36 y la integración jugable. Evidencia: [ITERATION175.md](ITERATION175.md).

### Callbacks de scroll BG37/BG38 — Iteración 2.74

Se midieron velocidades, wraps y diferencia de contador; la identificación de qué recurso usa cada offset se refinó después con los renderers. Evidencia: [ITERATION174.md](ITERATION174.md).

### Cobertura de auxiliares por constructor — Iteración 2.73

El PE asigna cuatro auxiliares a BG36, tres a BG37 (`tori1` y dos nubes) y dos a BG38 (nubes). El auditor dejó de contar como faltantes los torii que esos dos constructores no cargan; la auditoría local queda en 4/4, 3/3 y 2/2. Es un ajuste de cobertura de recursos, no una prueba de composición/paridad de escena. Véase [ITERATION173.md](ITERATION173.md).

### Ejecución completa del método de input replay — Iteración 2.72

Un harness ejecutó las instrucciones originales de `0x481040` una vez por cada uno de los 33.820 words del replay Sanae, con getters/decoder/reader/setter controlados. Todas las máscaras, flags, callbacks, incrementos de un word y el wrap al fin del vector coinciden. Esto no demuestra que cada llamada sea un frame ni que esos guards se alcancen así en una ronda real. Falta instrumentar cadence y estado live antes de portar playback. Evidencia: [ITERATION172.md](ITERATION172.md), [reporte completo](../artifacts/x86-replay-update-method-full-original-2009.json).

### Dispatch de replay en el PE — Iteración 2.71

El original 2009 confirma que `0x481040` lee una palabra de input y avanza el índice en su rama guardada; `0x4600fe` compara contra `[0x85eb58]`, retorna sin consumir si difiere y consume si coincide. Esto resuelve el avance condicional por llamada, pero no la cadence por frame ni la configuración efectiva de una ronda. No conectar playback con timing supuesto. Véase [ITERATION171.md](ITERATION171.md) y [ITERATION238.md](ITERATION238.md).

### Parser C de replay — Iteración 2.66

El core comparte un parser C acotado del formato 2009, conserva IDs y vistas al vector de inputs, y brinda un cursor `peek/next` más decodificación de bits. VitaSDK compila y enlaza el ELF de contrato; suite Python pasa 91/91. Falta probar el ELF, medir cadence por frame, cargar el archivo desde ux0:data y conectarlo al jugador antes del gate de replay Vita3K. Evidencia: [ITERATION166.md](ITERATION166.md).

### Semántica de replay — Iteración 2.65

Los bytes iniciales de cada registro se usan para seleccionar los dos personajes; la secuencia final `uint16` es el stream de inputs. El modo de grabación agrega `[0x85eb58]`, y el modo replay consume/decodifica ese stream a una máscara baja y seis IDs de entrada. En el replay Sanae los IDs son (15,16), (15,17), (15,0), coincidentes con Sanae vs Chirno, Meirin y Reimu del roster. Falta validar cadence/frames y playback paso a paso en el ejecutable original antes de integrarlo a Vita. Evidencia: [ITERATION165.md](ITERATION165.md).

### Esquema binario del replay Sanae — Iteración 2.63

El loader PE 2009 `0x42e030` valida la versión `0x100c8`, lee 10 bytes extendidos y usa el byte 7 como cuenta de tres registros; `0x42cd60` deserializa cada registro en memoria con stride `0x50`. `tools/inspect_replay_layout.py` reproduce el orden de lecturas con límites, y el `.rep` proporcionado se consume exactamente: 67,881/67,881 bytes, cero sobrantes, seis pruebas del parser. El reporte resume tres registros con secuencias `uint16`; sus semánticas y playback real aún no están verificados. Ver [ITERATION163.md](ITERATION163.md) y [reporte JSON](../artifacts/kernel/replay-layout-original-2009.json).

### Build Vita y hit espejo Remilia — Iteración 2.62

El trail secundario ahora conserva el spawn cuantizado del 801 y el hitbox de objetos convierte su desplazamiento a coordenadas locales antes del espejo de facing; el contrato verifica daño en ambos lados. Siete contratos C con GCC/MSYS2 y 83 pruebas Python pasaron. El VPK interactivo `Touhou123Vita-latest.vpk` (SHA-256 `a84133ecc36ef2ba19505a4bd7e5fe8c577c283d44152538b75e9825768c6c7b`) pasó Vita3K SDL, schema46/600 frames, regresiones, ciclo Remilia y contratos BG33. CTest/WSL aún no está disponible; los contratos C y Python se ejecutaron directamente en Windows. Persisten pendientes replay real y paridad integral del roster/escenarios. Ver [ITERATION162.md](ITERATION162.md).

### Replay y suite WSL — Iteración 2.61

El rebuild fresco de la suite en WSL reveló contratos de combate que fallaban; el análisis del PE 2009 localizó el guard de versión del `.rep` y descartó reutilizar `0x42EAC0` de SokuLib en esa build. WSL devolvió `E_ACCESSDENIED`; la suite se continuó de forma nativa en Windows. El parser estructural de Iteración 2.63 siguió el loader `0x42e030` y el decoder `0x42cd60`; falta asociar sus secuencias a input/timing y demostrar playback. Ver [ITERATION161.md](ITERATION161.md), [ITERATION162.md](ITERATION162.md) e [ITERATION163.md](ITERATION163.md).

### Revalidación de VPK — Iteración 2.60

El auto-VPK del ciclo Remilia 801 volvió a pasar Vita3K SDL schema46/600 frames y produjo capturas frescas; se confirmó que el `eboot.bin` coincide con el VPK interactivo `latest`. La suite host permanece pendiente en esta sesión: `ctest` no está en PATH y WSL devuelve `E_ACCESSDENIED`. Sigue abierto el siguiente bloque de alcance real: decodificar/reproducir un `.rep` y cerrar una ronda completa con paridad frente a PC. Ver [ITERATION160.md](ITERATION160.md).

### Ciclo de Remilia 801 en Vita — Iteración 2.59

El runtime ahora emite el raíz 801 y sus secundarios seq.1 desde la acción 412, conserva seis trails al retirar el padre en el tick 73 y valida conteos, poses, edades y posiciones contra la traza x86 con cuantización entera. Vita3K SDL pasó schema46/600 frames; el VPK de auto-prueba SHA-256 `e08d9412508058c3e8e29e9dd63848207174a781ddf1fdcae9b5d00c2c4f935f`. La siguiente paridad de mayor valor es la reproducción real del replay y una ronda completa. Ver [ITERATION159.md](ITERATION159.md) y la medición x86 [ITERATION158.md](ITERATION158.md).

### Preparación de pruebas en hardware Vita

[psp2-tooling](https://github.com/Grarak/psp2-tooling) sirve en la fase M7 para instalar/lanzar VPK por USB, automatizar controles, capturar salida y perfilar CPU/GPU en una Vita física. No sirve para compilar el VPK ni acelerar Vita3K o el análisis del PE. El host es Linux; la ruta DevKit está probada en 3.65 y `retail-cp` exige PCH-2000/3.65/Ensō/taiHEN, módulos DevKit descifrados y altera el modo debug del sistema. Se mantiene fuera del runtime: primero cerrar paridad funcional/emulador; después evaluar `devkit/` con el hardware disponible antes de considerar profiling avanzado. Evaluación: [ANALYSIS_AND_TESTING_TOOLING.md](ANALYSIS_AND_TESTING_TOOLING.md).

### Replay PC Sanae — Iteración 2.57

El replay `090815_2219_sanae_story.rep` es estáticamente compatible con `th123.exe` original proporcionado (`0x100c8`), no con el PE fijado más reciente (`0x100d2`). El checker acepta ambos perfiles por hash/firma y emite reportes separados. Próximo: reproducirlo con el ejecutable 2009 y capturar una ventana frame-step como oracle; la compatibilidad no prueba reproducción ni decodificación. Ver [ITERATION157.md](ITERATION157.md).

### Remilia 2C / objeto 801 — Iteración 2.56

El runtime reproduce el spawn 801 de acción 412, trayectoria y orientación espejo. El probe x86 sitúa la respuesta en el propio proyectil: `+0x194=3`, `+0x196=hitstop PAT` (0 en el cuadro medido), `+0x190=9`; el defensor ya tenía `+0x194=20`. La respuesta aplica 120 HP y el servicio de efecto x86 queda simulado. Tras separar las listas del probe de parejas del manager de objetos, el slot 4 del manager ejecuta 73 callbacks originales, avanza 801 de pose 1 a 12 y lo retira al llegar `+0x34c=0`; quedan seis objetos secundarios enlazados. Vita3K valida el hit en frame 16 y continuidad de pose sin daño repetido. VPK schema46/600 frames aprobado, SHA-256 `408e4bd32f50b0a04653038d9f2bc85abf4bcf34d890c57efd76c2a175ec910a`. La corrida aún usa listas/allocator/servicios controlados: faltan replay PC, efectos visuales reales, round completo y las demás rutas especiales. Ver [ITERATION155.md](ITERATION155.md) e [ITERATION156.md](ITERATION156.md).

## Objetivo

Entregar una demo funcional para PS Vita que cargue los recursos originales locales de todo el elenco, recorra todos los escenarios con sus capas y efectos, y reconstruya progresivamente las mecánicas del juego con referencia al ejecutable de PC. Cada subsistema debe tener una traza o contrato comparable, un VPK reproducible y evidencia en Vita3K. La compatibilidad y los FPS en hardware real se miden después de estabilizar la paridad funcional.

## Inventario actual

### Contrato de recursos BG35 — Iteración 2.51

El dispatcher PE sí acepta BG35 (`0x23`) y usa el constructor común 5×6, que solicita 30 bitmaps con patrón `0000[01..05][01..06].bmp`. Los índices locales TH105+TH123 no contienen ninguno. Queda por verificar el comportamiento del juego original al elegir BG35 y si otra distribución incluye esos recursos; no se debe asumir que la etapa está vacía ni sintetizar arte sin evidencia. Ver [ITERATION151.md](ITERATION151.md).

### Quads afines BG33 en Soft2D — Iteración 2.50

El core forma vértices por tile desde la matriz base y `FUN_00429440`; Soft2D los rasteriza como quads afines. La página diagnóstica dibuja 30/30 con cámara cero encajada en el mapa; no usa estado vivo del manager ni constituye la escena de combate. Guest gate schema46 y captura documentados en [ITERATION150.md](ITERATION150.md).

### BG33: contrato de traslación y 30 ranuras visibles — Iteración 2.49

Las anclas viven en la geometría base; el callback añade sólo el origen `+0x44/+0x48` y el scroll/wrap. Se corrigió el helper y el viewer ya representa los 30 slots/24 fuentes en una cuarta página local. Vita3K comprueba captura y máscara `0x3fffffff`; aún falta componer la matriz afín/cámara dentro del combate. Ver [ITERATION149.md](ITERATION149.md).

### Traslación compartida de viewport/cámara — Iteración 2.48

El helper `t123_stage_viewport_translation` porta la traslación de `FUN_00429440` con constantes/offsets originales. La autoprueba del guest y schema43 ahora requieren dos vectores exitosos y validación de zoom/puntero; Vita3K pasa. Continúa pendiente aplicar la matriz afín completa, los estados reales de sprites y composición en pelea. Evidencia y VPK: [ITERATION148.md](ITERATION148.md).

### Inventario PE del constructor BG33 — Iteración 2.47

El constructor hash-pinned reserva 24 sprites de tile con patrón `0000[fila][columna]` y carga aparte `0001/0002`. El renderer transforma esos dos auxiliares en tres pases cada uno con escala/rotación y matrix viewport; no se ha reconstruido su tiempo global ni su matriz de pantalla. Oracle de constructor, renderer y helpers pasa con la suite 77/77. Ver [ITERATION147.md](ITERATION147.md).

### Cadena de matriz/cámara BG33 — Iteración 2.46

El renderer llama al update del sprite, agrega el desplazamiento del fondo, delega transformación a viewport/cámara `0x429440` y filtra por ventana temporal del sprite. El oracle verifica las llamadas y los offsets consumidos; los helpers se agregaron a la exportación Ghidra. Falta obtener límites/estado real de cada sprite e implementar matriz afín, rotación y cámara en Vita. Ver [ITERATION146.md](ITERATION146.md).

### Renderer BG33 y slots locales — Iteración 2.45

El oracle del PE confirma cuatro fases, 30 iteraciones, rotación por seis fuentes, wrap de 24 sprites, corrección vertical `+0x400`, stride `0xe8` y suma de `+0x44/+0x48`. `t123_bg33_render_slot` pasa pruebas sobre los 30 slots y las cuatro fases; por ahora es contrato de host, todavía no está integrado en la vista animada ni combate. Falta reconstruir límites temporales, matriz/cámara y proyección. Evidencia: [ITERATION145.md](ITERATION145.md).

### Update animado BG33 — Iteración 2.44

La vtable BG33 (`0x85ae44`) apunta al update `0x473610`, que hace `counter=(counter+1)&0x3ff`, y al renderer `0x473620`, que lee `+0x64`. El port aplica ese ciclo y el gate de Vita3K registra cuatro updates/counter=4 mientras BG33 está seleccionado. El render de las 30 instancias/24 texturas, wrap espacial, matrix/cámara y composición en pelea aún no está portado. Evidencia de PE y corrida: [ITERATION144.md](ITERATION144.md).

### Composición fuente BG33 — Iteración 2.43

El constructor original `FUN_00473af0` solicita 24 tiles (`0000[01..04][01..06]`) y dos sprites (`0001/0002`), con llamadas de carga que fijan sus pivotes en `(700,228)` y `(350,152)`. El visor usa esa rejilla 6×4 en coordenadas locales y ahora la prueba de Vita3K exige haber dibujado y capturado la vista con los 24 tiles cargados. Captura y alcance en [ITERATION143.md](ITERATION143.md). La cámara, el callback de render final, animación y composición durante combate siguen pendientes; no asumir que las dos posiciones constructoras son proyección de pantalla.

### Ruta de creación e impacto de Suika 623C/531 — Iteraciones 2.31–2.32

La acción 531 pide `createObject(821)` en pose 7; la factory genera 821/seq.0 con nueve poses PAT y el update lo retira tras 27 ticks. Al sincronizar ambos combatientes con transforms originales, `0x47a5b0` confirma contacto en el spawn y en offsets verticales 0–200; `0x47ce20` aplica daño PAT 800 (HP 1000→200) y temporizador de reacción `+0x194=20` (`+0x196` hitstop=0). El probe valida factory, cajas transformadas, filtro, daño y reacción inicial bajo posiciones/listas controladas. Siguen pendientes input/replay natural, efectos/texturas reales, continuación PAT de acción 0 y una ronda completa/KO. La auditoría conjunta TH105+TH123 clasifica los 25 IDs del dispatcher x86 y encuentra carpetas fuente para 24; 14 vienen de TH123, con contenido heredado 10.5 para BG00–06/BG15/BG16/BG18 y traslape en BG10–14/BG17. BG35 tiene constructor genérico pero no aparece en ninguno de los dos manifiestos locales; separa nombres base convencionales, auxiliares según constructor (BG12 2/2, BG33 2/2, BG36 4/4, BG37 3/3, BG38 2/2) y el conjunto completo de BG34 (30+30 tiles, cuatro bitmaps, 30 sprites), sin llamar bugs a las celdas aún no demostradas. Evidencia: [ITERATION131.md](ITERATION131.md), [ITERATION132.md](ITERATION132.md), [ITERATION135.md](ITERATION135.md), [ITERATION141.md](ITERATION141.md) y [STAGE_RESOURCE_AUDIT.tsv](STAGE_RESOURCE_AUDIT.tsv). Sin cambios al VPK.

### Hit-confirm de skills Suika 623C — Iteración 2.30

El resolver de combate original confirma overlap y aplica la ruta especial de hit para Suika 521/seq.1/frame0 (400 PAT → 533 HP) y 526/seq.0/frame7 (500 PAT → 666 HP); el caso Remilia 320 mantiene 200. Iteración 2.31 confirma además el proyectil 821/daño 800 contra hurtbox Remilia auténtica en el resolver de objetos. El efecto visual y las corridas naturales siguen pendientes. Ver [ITERATION130.md](ITERATION130.md) y [ITERATION131.md](ITERATION131.md).

### Dispatch, PAT y update x86 de Suika 623C — Iteración 2.29

El bloque original de `handleInputs` ejecutó cuatro casos con 623C inyectado: selecciona 531, 526 o 521, o rechaza cuando los move-locks no permiten activar. El setter, initializer y lookup PAT originales de Suika inicializan esas acciones en seq.0/pose0. Una corrida parcial del update avanza 521 a seq.1/pose0 con 400 de daño en tick12 y seq.3/pose0 con 600 en tick30, pero la fixture de `PlayerSuika` llega a la frontera SEH/Win32 y no completa naturalmente. La iteración 2.30 ya valida combate de pareja para 521/526 con constructor base controlado; siguen pendientes el constructor especializado, input/matcher natural y ruta 531. Ver [ITERATION129.md](ITERATION129.md).

### Dispatch estático de acciones — Iteración 2.28

Los 20 CFGs de `handleInputs` producen 713 sitios donde `useSkill` recibe un primer argumento inmediato 400–599, 682 parejas handler/acción y pruebas de bits `Player+0x7c8` en los 20 personajes. El probe x86 confirma que ese primer argumento se entrega a `setAction`; corresponde al action ID PAT. En Suika se identificaron las ramas 623C/623B (531/526/521 frente a 530/525/520) y 22C/22B (571/566/561 frente a 570/565/560). Próximo: ejecutar la ruta 623C con los gates originales y seguir pose/objeto; después generar el comando con el matcher y ring buffer originales. El inventario estático no prueba alcanzabilidad ni jugabilidad. Ver [ITERATION128.md](ITERATION128.md).

### Remilia 412 → objeto 801 — Iteración 2.20

Con acción 321 (`ACTION_5AAA`) desde setter/PAT originales, el dispatcher `0x587bab` completa un update: subframe 0→1; el pair dispatcher aplica 120 de daño, HP 1000→880. Esto sigue usando posición, setter y listas controladas, y el callback de presentación cae después de aplicar daño. El handler original de Remilia transiciona 320→321 (`0x59d876–0x59d8ce`) si `Player+0x190` (`CollisionType`) no es 0/3 y llama el setter virtual con 321. La ejecución aislada de daño por proyectil deja ese campo en 0 aunque baja HP, así que aún falta la respuesta real de combate entre personajes, el ciclo natural de input/move-lock, reacción/hitstop y recursos spell-background para validar 602. Ver [ITERATION122.md](ITERATION122.md), [ITERATION121.md](ITERATION121.md), [ITERATION120.md](ITERATION120.md), [ITERATION119.md](ITERATION119.md), [ITERATION118.md](ITERATION118.md), [ITERATION117.md](ITERATION117.md), [ITERATION116.md](ITERATION116.md), [ITERATION115.md](ITERATION115.md), [ITERATION114.md](ITERATION114.md), [ITERATION113.md](ITERATION113.md), [ITERATION112.md](ITERATION112.md) y [ITERATION111.md](ITERATION111.md).

### Resolver de personaje y candidato PAT para hit-confirm — Iteración 2.24

El parser preserva los traits PAT completos. La sonda x86 alcanza geometría, `CollisionType=1`, combo y solicitud de efecto `0xC9`; al enlazar multiplicadores de ataque/defensa, el PE resta 200 HP (1000→800 en `Player+0x184`). La selección pide reacción 50, presente en el PAT de Remilia; la causa de la terminación posterior en `EIP=0` sigue bajo análisis. El efecto usa un objeto sintético. Regresión Remilia 412 5/5 y prueba de pareja de Players 1/1; VPK/runtime sin cambio. Siguiente: comparar lookup e inicialización de acción 50 con el camino normal, luego cotejar con replay. Ver [ITERATION123.md](ITERATION123.md), [ITERATION124.md](ITERATION124.md) y [ANALYSIS_AND_TESTING_TOOLING.md](ANALYSIS_AND_TESTING_TOOLING.md).

### Remilia 412: dispatch y datos ofensivos de 801 — Iteración 2.03

El ID 801 selecciona initializer `0x7991a5` y update `0x7879da`; el PAT de Remilia tiene seq.0 con daño 120/caja ofensiva durante 20 poses y seq.2 con daño 100/caja ofensiva durante 20 poses. La ruta 412 crea 801, así que ya hay un candidato atacante concreto. Falta correr factory/update/colisión y probar el daño acumulado frente al 750 del PAT dueño. Ver [ITERATION103.md](ITERATION103.md).

### Remilia 412: factory del objeto 801 — Iteración 2.02

`0x46eb30` es el wrapper de `Player::createObject`; la rama especial de action 412 lo llama con ID 801 y posición relativa al jugador en el subestado 4. Le sigue el callback indexado `0x464980`. Esto da un objetivo claro para el siguiente tramo: resolver factory, initializer, update y colisión de 801, y comprobar el daño contra el oracle x86. El objeto aún no está probado como fuente de los 750 PAT. Ver [ITERATION102.md](ITERATION102.md).

### Corrección del update Remilia 412 — Iteración 2.01

La conclusión de Iteración 1.95 queda supersedida: action 412 sigue la tabla del dispatcher especial (`0x58a3a1 → 0x58cce7`), no el handler genérico `0x483f40`. En el subestado `+0x140 == 4`, el handler arma la solicitud del objeto 801 (`0x46eb30`) y llama un callback de objeto indexado. Siguiente trabajo: resolver ese callback y probar update/collision/daño con una secuencia natural y un oracle x86. No marcar el 2C completo ni trasladarlo al runtime hasta verificarlo. Ver [ITERATION101.md](ITERATION101.md).

### Audit de `attack_flags` — Iteración 1.87

El roster contiene 1,442 combinaciones personaje/acción/índice/flags con poses dañinas sin cajas explícitas, distribuidas en 164 valores raw (`PAT_ATTACK_FLAGS.md`). Remilia 412:0 marca 750 de daño con `0x00204002`; 416:0/1, 800 con `0x0000240a`. Alice 418:0 marca daño con `0x00088404` y el handler crea objeto 849. Iteración 1.88 desensambla `0x465e10` y consumidores geométricos: los bits `0x00400000/0x00800000` leídos en descriptor `+0x4c` gobiernan punteros de hit/hurt transformados y corresponden a `frameFlags`, no a `attack_flags`. El sincronizador publica conteos y buffers de vectores PAT. Siguiente: recuperar el productor de CharacterFrameData para Remilia 412; no inferir hitboxes solo por daño/flags. Ver [ITERATION88.md](ITERATION88.md).

Iteración 1.89 regeneró el CFG x86 de 20 handlers con el PE fijado y confirmó que Remilia consulta `getMoveLock(412)` antes de seleccionar 2C. La ruta de entrada no muestra una llamada directa al factory conocido, sin excluir callbacks o spawn durante actualización. La búsqueda de `[reg+0x50]` no aisló lectores de `attackFlags`; falta rastrear el callback y construir el descriptor 412 real en el harness. Ver [ITERATION89.md](ITERATION89.md).

Iteración 1.90 refinó los datos: pose 5 de Remilia 412 tiene una `collision_box` `[-20,-155,20,-1]`, aunque `attack_boxes` esté vacío. El vtable resuelve `initializeAction` a `0x59ad64` para 412; `update` `0x5879a0` no tiene branch directo para 412. `0x465e10` transforma `CharacterFrameData+0x54` a `object+0x310` y publica `object+0x348`. Iteración 1.91 sigue la cadena posterior a contacto en `0x47c770`: `0x47b5d0/0x47b490/0x47c590/0x47aa50` filtran y procesan respuesta/daño, pero no producen geometría. Iteración 1.92 encontró la ruta candidata `0x4649b0 → 0x47b1d0 → 0x4799b0`, llamada por varias rutinas de Remilia. Iteración 1.93 descarta cuatro callsites próximos: sus guards exigen secuencias 2 o 3, distinto al daño PAT de 412/seq.0/pose5; un bloque de punteros en `0x59a2c8` sigue sin referencia absoluta ni consumidor confirmado. Siguiente: demostrar si el bloque participa en el dispatch y resolver la ruta 412 antes de modelar el daño. Ver [ITERATION90.md](ITERATION90.md), [ITERATION91.md](ITERATION91.md), [ITERATION92.md](ITERATION92.md) y [ITERATION93.md](ITERATION93.md).

Iteración 1.94 ejecuta `0x465e10` del PE fijado con el PAT real de Remilia 412/seq.0/pose5 y luego el helper original `0x47a5b0`: publica cuatro hurt boxes, cero hit boxes y el puntero de collision box; la prueba hit-vs-hurt retorna cero contacto aun con cuatro hurtboxes defensoras. Las funciones de transform se sustituyen por copias controladas; no es una traza de combate nativa. Los 750 de daño siguen sin explicación. Siguiente: localizar el callback/emisor alterno de Remilia 412. Ver [ITERATION94.md](ITERATION94.md).

Iteración 1.95 sigue el update común de Remilia: action 412 enruta a `0x483f40`, cuyo switch solo cubre actions 50–181; 412 retorna por la rama por defecto. El dispatcher común no explica ese daño ni evidencia llamadas directas a los callbacks 2/3. Es una conclusión estática, pendiente de probar vtables y objetos secundarios con setup/update dinámico. Ver [ITERATION95.md](ITERATION95.md).

Iteración 1.96 verifica el mapa del initializer: 412 → grupo 15 → `0x59ad64`. Unicorn ejecuta la rutina original y `0x4636b0`, confirmando el reset de estado, contadores y movimiento sin spawn ni daño en ese initializer. Próximo: instrumentar el caller y la transición de entrada a 412, con atención a llamadas virtuales/factories, hasta ubicar el emisor de contacto. Ver [ITERATION96.md](ITERATION96.md).

Iteración 1.97 ejecuta además el selector original `0x59ab40`: acción 412 alcanza exactamente `0x59ad64` y completa los resets verificados. La selección del initializer queda probada dinámicamente; aún faltan el setter desde input, update de personaje, factories y fuente del primer contacto. Ver [ITERATION97.md](ITERATION97.md).

Iteración 1.98 ejecuta el setter real después de los gates: `0x464930 → 0x438ca0 → 0x465370 → 0x59aaa0/0x59ad64`. Con un PAT map controlado selecciona seq.0, pose 0 y las 12 poses reales; el reset queda verificado. Falta aún el lookup real de moveLock, correr el handler desde input y rastrear update/factories/impacto. Ver [ITERATION98.md](ITERATION98.md).

Iteración 1.99 ejecuta además el bloque exitoso de `0x59dd97`: `0x489610` recibe la clave 412 y retorna lock 0 desde un fixture; la rama alcanza setter/reset/initializer y secuencia PAT real de 12 poses. Se saltan los gates anteriores (estado/movimiento/recurso) y se controlan PAT lookup y callback de pose. Sigue pendiente demostrar entrada natural, probar el rechazo y rastrear actualización/daño. Ver [ITERATION99.md](ITERATION99.md).

Iteración 2.00 añade el caso diferencial: BX 0 vs lock 0 acepta 412 y completa el setup; BX 1 vs lock 0 rechaza 412, consulta moveLock(410) y no alcanza el setter 412. Esto confirma ambas salidas del compare en el fragmento instrumentado, aún con gates previos omitidos y PAT/pose controlados. Falta input natural, update, factory/contacto y daño. Ver [ITERATION100.md](ITERATION100.md).

### Medición B/C actual — Iteración 1.86

La última compilación de diagnóstico VitaSDK pasó schema31 en Vita3K SDL aislado, 600 frames; conserva roster PAT/recursos/tarjetas 20/20, BG34 y A natural 20/20. La sonda B/C valida ataques PAT directos u objetos incluidos, no specials por comandos/flags. La Iteración 2.26 conectó Alice 66B/66C por objeto 849. La Iteración 2.27 corrigió orientación por `face` y amplió offsets aéreos, sin cambiar los impactos: B 15/20 (`0x0EBBBE`) y C 15/20 (`0x0BF9B7`). Esos masks describen el probe parcial, no todos los ataques del roster. El PE Suika `0x609dc0` separa rutas dash y specials 623B/623C con flags `Player+0x7c8` y gates de nivel; queda pendiente ejecutar el dispatcher/player input completo y verificar todas las rutas contra PC/replay. Ver [ITERATION126.md](ITERATION126.md), [ITERATION127.md](ITERATION127.md) y [roster-bc-natural.tsv](../artifacts/roster-bc-natural.tsv).

### Gate A de reconstrucción — Iteración 1.85

Build VitaSDK fresco, VPK de 96,291 bytes, SHA-256 `1a1461e7197ac65694ce45f01f45f3460288301bd7029c27a1b072300372fd08`; Vita3K SDL aislado schema30 pasó 600 frames. El gate prueba rutas A con aproximación natural desde spawns normales contra Cirno inmóvil para los 20 PAT (`roster_a_natural_attack_mask=0xFFFFF`), además de ataque A con geometría controlada, hits A/B/C en la pelea principal, roster de recursos 20/20 y BG34. No verifica todos los matchups, IA/guardia ni paridad por frame. La evidencia visual está en [fight-natural-a.bmp](../artifacts/screenshots/fight-natural-a.bmp); los otros escenarios y sus mecánicas siguen pendientes. El VPK queda local en `artifacts/`. Ver [ITERATION85.md](ITERATION85.md), [ITERATION84.md](ITERATION84.md), [ITERATION83.md](ITERATION83.md) y [STATUS.md](STATUS.md).

### Seguimiento activo de objetos — Iteración 1.81

`GameObjectBase::BoxInfo` inicia en `object+0x1b4`: frameData `+0x1c0`, conteos hit/hurt `+0x1cb/+0x1cc`, hurt boxes `+0x1d0`, hit boxes `+0x220`, buffers rotados `+0x270` y punteros auxiliares `+0x320`. El PE fija `0x465e10` como sincronizador de vectores PAT al runtime. El manager ejecuta fases de pares en `0x47cb70/0x47ce20`; `0x47a5b0` prueba hit boxes contra hurt boxes y `0x47a740` hurt contra hurt, con helpers para formas rotadas y AABB. Falta la traza dinámica que conecte el action 808 con respuesta/daño. Ver [ITERATION80.md](ITERATION80.md) y [ITERATION81.md](ITERATION81.md).

El handler 808 de seq.0 consulta el action del owner con `0x48ce90` y el suelo por separado con `0x4397f0`; el primero no es detección geométrica. El manager retira el objeto cuando `object+0x34c==0`, pero pool/handles/lista no están integrados dinámicamente en el harness. Siguiente: localizar por CFG/traza la resolución real del impacto y el ciclo de vida 808. La última regresión fresca es Iteración 1.82; no incluye la mecánica 808. Ver [ITERATION79.md](ITERATION79.md), [ITERATION78.md](ITERATION78.md), [ITERATION76.md](ITERATION76.md), [ITERATION77.md](ITERATION77.md) y el reporte `artifacts/x86-suwako-808-factory-probe.json`.

La revisión TH75 recomienda instrumentación por evidencia, contratos ABI y watchdog; el prototipo semántico x86→C del chat solo pasó un smoke test sintético y su bootstrap VitaSDK no se validó. No importar runtime/renderer/imports ni datos TH075. Ver [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md).

### Seguimiento activo de objetos — Iteración 1.65

La ruta original de Suwako 808 ya está reubicada en su handler real `00788d3e`. El oracle Unicorn ejecuta el dispatcher/update original y captura dos llamadas hijas con posición compartida y custom data; casos controlados de colisión, suelo y latch confirman guards sin split. El delta `0.075/0.005` afecta `object+0x11c`, mientras `vy` pierde `0.2` en ambas secuencias. El port sigue usando `vx=4`/vida 90 provisionales; seguir initializer/update/hit/terminación del hijo y contrastar una traza natural antes de corregir la mecánica. Ver [ITERATION65.md](ITERATION65.md) y [ITERATION66.md](ITERATION66.md). Esta evidencia también corrige el callback mal atribuido en la Iteración 36.

Los tres DAT de 12.3 contienen 11,283 entradas (1,088,266,746 bytes sin comprimir), 22 carpetas bajo `data/character` y 14 carpetas de escenario bajo `data/background`. El índice de 10.5 aporta los recursos heredados que nueve PAT de 12.3 referencian para sus poses idle. El inventario también identifica cartas, efectos, escenas, audio, clima y recursos de menú. La carpeta `common` y el contenido `namazu` aún necesitan clasificarse frente al roster jugable. Ver [RESOURCE_INVENTORY.md](RESOURCE_INVENTORY.md); los manifiestos locales están en `artifacts/th123-resource-manifest.tsv` y `artifacts/th105-resource-manifest.tsv`.

## Actualización de combate — Iteración 1.51

Las skills terrestres de Reimu usan la tabla x86 de 12 cartas. Acciones 540 y 565 conectan sus primeras cajas PAT: Vita3K confirma 1100 en seq.3/imagen39 (carta102) y 450 en seq.1/imagen47 (carta107), en los ticks derivados de sus duraciones PAT. Carta103/acción560 conserva startup, impacto, vuelo vertical/horizontal y aterrizaje. El movimiento de escenario sigue parcialmente modelado; otras rutas, traza PC end-to-end, rutas aéreas, mano/costo/consumo, efectos y objetos siguen pendientes. Ver [ITERATION54.md](ITERATION54.md), [ITERATION55.md](ITERATION55.md), [ITERATION56.md](ITERATION56.md), [ITERATION57.md](ITERATION57.md), [ITERATION58.md](ITERATION58.md) y [ITERATION59.md](ITERATION59.md). La revisión de Touhou75Vita aporta método CFG/cobertura, mientras los oráculos del PE 12.3 siguen siendo la referencia. Ver [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md).

La Iteración 1.48 ejecuta `nextPose` y localiza la transición de touchdown: action 560 (`00490490 -> 004A0639`) invoca `applyAirMechanics` y, al contactar el suelo descendiendo, el bloque `0049295D` pide `setSequence(3)`. El helper `00463550` añade la integración horizontal con direction/speedPower; el port representa y valida en Vita3K el caso base. Faltan reglas completas de movimiento, colisiones y cartas/cancelaciones.

## Hitos

| Hito | Trabajo | Criterio de cierre | Estado |
|---|---|---|---|
| M0: referencias | Versiones/hash del ejecutable y DAT, análisis Ghidra, dependencias y formatos | Referencias separadas por versión y cada hipótesis vinculada a funciones/datos | Base x86 y exportación Ghidra disponibles; inventario de mnemonics de los 20 handlers de input; análisis de objetos y escenas incompleto. Ver [ITERATION41.md](ITERATION41.md) |
| M1: pipeline | Build host/ARM, VPK interactivo/automático, runner aislado y evidencia por corrida | Checkout limpio genera ambos VPK y archiva log, hash y reporte | Build ARM/VPK nativo Windows con `tools/build-vita-native.ps1`; consolidar con pipeline host y repetir desde checkout limpio |
| M2: inventario integral | Manifiesto de todos los DAT, clasificación de roster, PAT, sprites, audio, fondos, escena y efectos | Cada entrada tiene tipo, consumidor, conversor y cobertura de demo | Primera pasada: 11,283 entradas, 22 carpetas de personaje y 14 de escenario |
| M3: demo de recursos | Galería navegable de cada personaje/pose y visor de escenarios/capas/efectos | Cobertura del 100% de recursos renderizables esperados y ausencia de referencias rotas | Galería PAT 20/20; BG34 conserva 30+30 tiles, 4 bitmaps y 30 sprites `objectFa`. El visor carga auxiliares BG12/33/36–38; BG02 ya muestra sus 48 recursos y expone los offsets locales extraídos del renderer x86 (`left -332,-472`; `center Background+44/+48`; `right 312,-472`). Gate schema40 comprueba ese contrato y las capturas BG02/BG12/BG36 en sus vistas. Faltan proyección de cámara, composición y paridad visual, referencias/huecos y render integrado de todos los assets localizados. La auditoría PAT cubre 12,189 imágenes de pose de 20 candidatos. Ver [ITERATION135.md](ITERATION135.md) y [ITERATION142.md](ITERATION142.md) |
| M4: motor de personajes | Locomoción, ataques A/B/C, habilidades, proyectiles, hitboxes, combo, guardia, hitstop, daño, KO y rondas para todo el roster | Acciones alcanzables comparadas por frame contra PC en personajes y casos acordados | 19 handlers con rutas 408/418 y moveLocks comprobados; 35 impactos directos PAT verificados. Los dispatchers seleccionan Alice 849 seq. 19 (408), 21/23 (418), Suwako 989 seq. 5 (408) y 808 seq. 0 (418); cuatro variantes ofensivas PAT (Alice 418 seq. 21/23 y Suwako 408/418) más Alice 408 sin caja. Hay runtime experimental visible; spawn/anclaje parcial contrastados con x86 y Vita3K 5/5. En Suwako 418, poses 5–17 ajustan movimiento y el gate de creación es contador impar 1–19; Vita3K schema19 verificó diez spawns. La asociación DI-secuencia0 es hipótesis; coordenadas, trayectoria, vida, ciclo de vida y daño por frame siguen pendientes. Remilia 2C/412 tiene probe dedicado. Reimu tiene 12 cartas mapeadas por contexto; `00489660` modifica niveles/variantes y consume cartas. El gate estático requiere cancellable, `actionLock<51`, spellcard, estado y costo válido. Ruta Vita de prueba 103 → acción PAT 560: Iteración 49 conserva el orden original, sin daño en los primeros 11 updates y primer impacto al entrar en seq. 1 en el update 12; Vita3K schema21 conserva las regresiones del roster, escenario, dash y B/C. La asignación de slot es fija: mano/costo/consumo/mejora, cancelaciones, aire, objetos de las otras skills, byte `+0x836` y paridad por frame PC siguen pendientes. También faltan objetos completos, cartas, hitstop y KO. Ver [ITERATION49.md](ITERATION49.md), [ITERATION48.md](ITERATION48.md), [ITERATION47.md](ITERATION47.md), [ITERATION45.md](ITERATION45.md), [ITERATION44.md](ITERATION44.md), [ITERATION42.md](ITERATION42.md), [ITERATION40.md](ITERATION40.md), [ITERATION39.md](ITERATION39.md), [ITERATION38.md](ITERATION38.md), [ITERATION37.md](ITERATION37.md), [ITERATION36.md](ITERATION36.md), [ITERATION35.md](ITERATION35.md), [ITERATION34.md](ITERATION34.md), [ITERATION33.md](ITERATION33.md), [ITERATION32.md](ITERATION32.md), [ITERATION31.md](ITERATION31.md), [ITERATION30.md](ITERATION30.md) y [DASH_DISPATCH_COVERAGE.md](DASH_DISPATCH_COVERAGE.md) |
| M5: escenarios y sistemas | Escenarios multicapa, animaciones, colisiones, clima, spirit, cartas, menú/selección y transiciones | Reproducción de cada escenario y mecánica con secuencias trazables y sin recursos ausentes | Auditoría de 25 IDs x86 cruzada con ambos DAT: carpetas fuente para 24/25; BG35 sin carpeta en esos manifiestos. BG02: 48 sprites indexados en grupos de 16, ciclo cada tres updates y offsets locales comprobados contra PE; falta recuperar origen de escena y cámara. BG04 `cloud2` y BG16 cuatro assets siguen inventariados, pendientes de composición. BG34 conserva 30+30 tiles, 4/4 bitmaps, 30/30 sprites; auxiliares BG12 2/2, BG33 2/2, BG36 4/4, BG37 3/3 y BG38 2/2 según sus constructores x86. Véase [ITERATION173.md](ITERATION173.md). BG36 reproduce offsets/wrap de dos nubes; BG37 y BG38 reportan el scroll x86 de las nubes en páginas auxiliares probadas en Vita3K. Faltan composición y cámara de esos renderers y los demás parallax/callbacks, referencias ausentes, colisión, clima, transiciones y paridad visual/funcional. Ver [ITERATION132.md](ITERATION132.md), [ITERATION133.md](ITERATION133.md), [ITERATION135.md](ITERATION135.md), [ITERATION140.md](ITERATION140.md), [ITERATION141.md](ITERATION141.md) e [ITERATION142.md](ITERATION142.md). |
| M6: demo integral | Flujo de selección, combate, fin de ronda y galería completa dentro del VPK | Recorrido de todos los personajes y escenarios en Vita3K, cargas/reinicios y regresión determinista | Pendiente |
| M7: rendimiento y hardware | Perfil de CPU/GPU/memoria, optimización del renderer y prueba física | Objetivos FPS acordados sostenidos en PS Vita y sin regresiones visuales/funcionales | Pendiente; Vita física aún no probada. `psp2-tooling` queda como candidato de automatización/profiling, sujeto a confirmar host Linux y modelo/firmware de Vita. |

## Herramientas y aceleración de pruebas (2026-10-17)

La revisión de recursos externos prioriza ReplayInputView+/LabTool de SokuMods para obtener una traza PC controlable de entradas, hitboxes y frame data; es más directa para cerrar la interacción Remilia que añadir de inmediato un solver. El artículo SMT compartido inspira un experimento acotado de ejecución simbólica para resolver guards y producir fixtures, verificados luego por Unicorn. El harness actual de Vita3K es una regresión integral de 600 frames; documentamos una escalera host → sonda x86 → smoke corto → gate full, y proponemos perfiles separados `smoke`/`full` como mejora futura. La sonda reemplaza temporalmente la factory global de efectos `0x8985f0` por una respuesta sintética; tras confirmar daño, el fallo queda en la continuación que asigna/inicializa acción de reacción 50. Detalle, enlaces y diseño de la corrida corta: [ANALYSIS_AND_TESTING_TOOLING.md](ANALYSIS_AND_TESTING_TOOLING.md).

`psp2-tooling` (Grarak) no acelera la decompilación ni el build actual: es Linux-only y está orientado a conectar una Vita física por USB para instalar/lanzar VPK, automatizar entrada/captura y obtener dumps/perfiles. El README upstream confirma además controles por `host0:`, instalación VPK, capturas de HDMI, dumps de procesos detenidos, muestreo CPU y capturas/métricas Razor GPU; son funciones de hardware para la fase M7, no un reemplazo del runner Vita3K. Se reserva para M7, una vez que M6 tenga una escena estable. Primer paso futuro: usar únicamente `devkit/` en una configuración compatible y comprobar VPK + captura; dejar perfiles avanzados para cuando tengamos ELF con `-g`, SELF sin ASLR y los módulos/conexiones requeridos. No integrar `retail-cp` como requisito: su ruta retail se limita según upstream a PCH-2000/FW 3.65/Ensō/taiHEN y módulos DevKit descifrados; además altera el entorno de depuración de la consola. En este checkout no se detectó una instalación Linux configurada ni se comprobó una consola física compatible, así que el gate de hardware queda pendiente; no se instaló plugin alguno. Mantener la herramienta host separada y con licencia GPL-3.0. Fuente y requisitos: [psp2-tooling](https://github.com/Grarak/psp2-tooling).
## Siguiente secuencia de trabajo

1. La demo interactiva actual incluye la galería de 20 PAT. El gate automático comprueba entradas de navegación y textura, pero no es un build de juego completo. Las tarjetas `data/stand/<slug>.cv2` son arte de selección, no frames de pelea.
2. Muestrear visualmente en Vita3K animaciones/poses de los 20 personajes; seguir en Ghidra los callbacks y vtables para componer BG12/33/36–38 desde las referencias ya conectadas, clasificar huecos de tiles y recuperar IDs faltantes con evidencia DAT 10.5/12.3; rastrear `common/000 hikakuyou.bmp`.
3. Loader Ghidra: `00408cf0` hace lookup de variantes (`DAT_00896b84=0` en el EXE base); `00409b50` calcula CRC32 plegado a mayúsculas, `0041c530` busca el árbol y `0041c080` comprueba nombres ante colisiones. `0041bb50` descifra y enumera el DAT, `0041bdd0` inserta rutas, offset y tamaño. Los 74 nombres idle heredados ya se resuelven con `th105a.dat`.
4. Correlacionar transiciones, variantes PAT y daño con pseudocódigo/trace por personaje. El port C del helper `0046cc90` se contrasta como ARMv7 contra x86: 17 casos fijos más 384 secuencias generadas pasan. El historial de 90 muestras también se prueba con wrap, y `NRNR`/`NLNL` reemplazó el atajo de dos toques en el combate. En Vita3K, 35 dashes aplican daño PAT directo. El análisis estático resuelve las secuencias creadas por Alice 408/418 (849: 19, 21/23) y Suwako 408/418 (989: 5; 808: 0); tres tienen cajas ofensivas en PAT y una no. Falta portar y validar update, colisión y daño de esos objetos. El empaque de `0046d5d0` ya está fuente-base; `Player+0x784` se confirmó como estado del botón C, y la cadena de Suika 200→418 ahora corre con constructor, deque, update y matcher originales bajo fixture determinista. Controles físicos/replay, neutralización exacta y timing PC todavía deben probarse. `0046d950` resembraría `Player+0x7b0` durante inicialización/transiciones. Remilia conserva su 2C/412. Próximo: enlazar replay/controles, recuperar update y colisión y comparar con trazas PC. Ver [ITERATION250.md](ITERATION250.md), [ITERATION34.md](ITERATION34.md), [ITERATION32.md](ITERATION32.md), [PORT_REFERENCES.md](PORT_REFERENCES.md), [INPUT_STATE.md](INPUT_STATE.md), [ITERATION27.md](ITERATION27.md), [ITERATION26.md](ITERATION26.md), [ITERATION22.md](ITERATION22.md) e [ITERATION23.md](ITERATION23.md).
5. Ghidra confirmó el dispatch `00470e40`, la rejilla 6×5 y orientación x del loader `0046fe40`, más dos rejillas y un desplazamiento vertical de 1200 unidades en `bg34` (`00474f70`). La vtable `0085afa4` prueba que el contador `+0x64` avanza cada tick y que el renderer selecciona `objectFa((tick % 60)/2)`; Vita3K reproduce el ciclo. El mapa de colocación está disponible para inspección, con proyección todavía provisional ([ITERATION15.md](ITERATION15.md)). Recuperar transformaciones de cámara, condiciones de dibujo, parallax y colisión antes de integrarlos como mundo jugable. Extender la auditoría a los otros 23 IDs.
6. Recuperar el combate por subsistema y personaje; integrar clima, cartas, audio y flujo de ronda. Cada entrega incluye entrada fija, traza x86/Vita y prueba fresca Vita3K.
7. Perfilar y optimizar tras cerrar cobertura/paridad en emulador, y finalmente validar FPS en una PS Vita física.

## Pruebas y evidencia

Iter06 conserva el alcance interactivo conocido; iter07 añadió detalle de 76,357 poses PAT; iter10 añadió tarjetas 20/20; iter11–12 resolvieron los idle heredados con DAT de 10.5. La iteración 1.6 valida galería PAT en Vita3K con navegación de personajes/acciones/poses y textura visible; la auditoría decodifica 12,189 imágenes de poses para los 20 candidatos. El combate B/C sigue siendo experimental; escenarios, mecánicas y paridad quedan pendientes. Ver [PAT_RESOURCE_COVERAGE.md](PAT_RESOURCE_COVERAGE.md), [PAT_IMAGE_DECODE.md](PAT_IMAGE_DECODE.md), [ITERATION04.md](ITERATION04.md), [ITERATION05.md](ITERATION05.md), [ITERATION06.md](ITERATION06.md), [ITERATION07.md](ITERATION07.md), [ITERATION09.md](ITERATION09.md), [ITERATION10.md](ITERATION10.md), [ITERATION11.md](ITERATION11.md) y [STATUS.md](STATUS.md).

Cada corrida de recursos o mecánica debe empezar en instalación fresca, archivar el reporte anterior y verificar hash del VPK, cierre sin error y digest/traza. Vita3K sirve para regresión, no sustituye una prueba en hardware.

Las decisiones de arquitectura de recompilación están contrastadas con [D2Vita, repentogxm y Touhou75Vita](PORT_REFERENCES.md). Esas referencias inspiran el pipeline de análisis y validación; no son código integrado ni evidencia de paridad.

## Actualización Iteración 1.67

Para Suwako 808 ya se ejecuta el handler de split, initializer radial y ocho updates por hijo bajo Unicorn. La secuencia sigue explícita como hipótesis porque falta emular la cadena virtual de factory; tampoco está cerrada persistencia por tick, colisión, vida ni terminación. El runtime Vita sigue con placeholder y requiere estos contratos antes del port fiel. Siguiente paso: ejecutar la factory del PE hasta la llamada del initializer de acción y capturar +0x13e, luego conservar el layout de objeto entre ticks y comparar colisión/ciclo de vida. Ver [ITERATION67.md](ITERATION67.md).

## Gate de regresión Iteración 1.68

El build actual de auto-test pasó 600 frames en Vita3K aislado con hash 11d0c4df4f35a27edd275ef0bb96ed4f8751df26ba9a68c3576700ad385873c3. Confirma los gates automatizados existentes para roster 20/20, BG34, objetos/dashes y tres rutas de skill Reimu. No eleva el alcance de paridad; la mecánica Suwako 808 radial sigue en análisis x86 y fuera de este VPK. Ver [ITERATION68.md](ITERATION68.md).

## Actualización Iteración 1.69

Se corrigió el cadence del oracle 808: el movimiento espacial ocurre cada ocho subframes, mientras gravedad/escalar avanzan cada callback. El JSON de trayectoria anterior se regeneró con subframe persistente; la secuencia aún se pasa explícitamente y no es prueba del factory real. Siguiente gate sigue siendo instrumentar la cadena virtual para capturar +0x13e natural, luego hitbox/ciclo de vida. Ver [ITERATION69.md](ITERATION69.md).

## Actualización Iteración 1.70

La secuencia del objeto 808 está resuelta por customData[2] según el initializer de Suwako ya auditado en ITERATION34; no depende de arg4. Unicorn ejecuta el initializer original y confirma secuencia 1 para ambos hijos. El factory virtual y el reloj externo del subframe siguen pendientes para una trayectoria nativa comparable, además de hitbox/ciclo de vida. Ver [ITERATION70.md](ITERATION70.md).

## Actualización Iteración 1.71

Se corrigió otro offset crítico en el modelo 808: +0x113 es alpha RGBA, no subframe. Seq.1 reduce alpha en pasos de 8 y deja de integrar posición bajo 8. El constructor/factory debe confirmar alpha inicial y valores RGB; collision, vida y salida siguen pendientes antes del port Vita. Ver [ITERATION71.md](ITERATION71.md).

## Iteración 1.72: auditoría de transferencia TH075 y alpha 808

La revisión comparativa de TH075 confirma que su mapa CFG/cobertura, contratos ABI, watchdog y metodología de medición son buenas referencias; su runtime x86→C, loader, imports, renderer y direcciones son específicos/no validados para TH123 y no se copiaron. Detalle en [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md).

Se corrige una suposición del harness 808: `object+0x113` es alpha; el valor inicial 255 era inyectado. `0x799000` no escribe el byte y `0x438bb0` configura color desde `+0x10c`, sin tocar `+0x113`. La ruta de creación real está pausada antes del objeto por el pool/manager y sus datos de animación. Se requiere reconstruir ese estado antes de calcular una trayectoria natural o cambiar el placeholder Vita.

### Gate técnico 808 actualizado (Iteración 1.72)

El ctor aislado `783a70` y la cadena `setAction→setSequence→initializeAction` ya corren con asignaciones internas cdecl controladas y mapa PAT sintético. El constructor del sprite deja color blanco/alpha 255; los setters preservan el color. Sigue pendiente integrar manager/handles del factory, además de frame data auténtico, colisión y vida antes de portar. Véase [ITERATION72.md](ITERATION72.md).

La prueba aislada `x86_suwako_808_action_probe.py` ahora ejecuta `setAction→setSequence→setPose→initializeAction` con mapa PAT sintético y demuestra la selección de seq.1/frame0, la velocidad radial, y que no hay escritura de RenderInfo al inicializar. El alpha de entrada depende todavía del allocator/pool de la factory; no marcar el proyectil completo ni portarlo hasta medir la asignación/reuso y recuperar update/colisión/vida. Ver [ITERATION72.md](ITERATION72.md).
