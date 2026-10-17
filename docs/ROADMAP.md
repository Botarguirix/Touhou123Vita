# Roadmap: reconstrucción integral de Touhou 12.3

## Objetivo

Entregar una demo funcional para PS Vita que cargue los recursos originales locales de todo el elenco, recorra todos los escenarios con sus capas y efectos, y reconstruya progresivamente las mecánicas del juego con referencia al ejecutable de PC. Cada subsistema debe tener una traza o contrato comparable, un VPK reproducible y evidencia en Vita3K. La compatibilidad y los FPS en hardware real se miden después de estabilizar la paridad funcional.

## Inventario actual

### Remilia 412 → objeto 801 — Iteración 2.16

El dispatcher `0x47ce20` corre con listas de equipo y alcanza filtro/resolver. El constructor de personaje original `0x46b7f0` establece `object+0x1ac=1` (la limpieza `0x46b9a0` lo borra); ahora ese valor se ejecuta en la fixture. El PAT neutral Remilia (`frameFlags=0x31`) sigue sin impacto. Si solo se abre sintéticamente el bit `0x40` de frameFlags, el PE sigue `0x47b660→0x47a5b0`, confirma overlap, resta 120 y fija cooldown 9, luego falla en el callback global de efectos. No es impacto natural: queda encontrar una pose vulnerable PAT genuina con hurtbox y conectarla al update real. Después: callback de presentación, guardia/reacción/hitstop y combate end-to-end. VPK de runtime sin cambios. Ver [ITERATION116.md](ITERATION116.md), [ITERATION115.md](ITERATION115.md), [ITERATION114.md](ITERATION114.md), [ITERATION113.md](ITERATION113.md), [ITERATION112.md](ITERATION112.md), [ITERATION111.md](ITERATION111.md), [ITERATION110.md](ITERATION110.md), [ITERATION109.md](ITERATION109.md) y [ITERATION108.md](ITERATION108.md).

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

La última compilación de VitaSDK pasó schema31 en Vita3K SDL aislado, 600 frames; conserva roster PAT/recursos/tarjetas 20/20 y A natural 20/20. La sonda B/C intenta aproximación desde spawn, rutas terrestres/aéreas/dash y valida el daño PAT directo o de objeto; registró B 14/20 (`0x0EBBB6`) y C 15/20 (`0x0BF9B7`). Es una medición diagnóstica, no un gate final: el inventario ve variantes PAT, pero el selector provisional de runtime solo cubre dash 408/418; las demás variantes requieren contraste x86 y flags de ataque sin cajas quedan sin simular. Los fallos actuales incluyen rutas B en Reimu, Alice, Remilia, Udonge, Tenshi y Cirno, y rutas C en Alice, Remilia, Suika, Udonge y Utsuho. Ver [ITERATION86.md](ITERATION86.md) y [roster-bc-natural.tsv](../artifacts/roster-bc-natural.tsv).

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
| M3: demo de recursos | Galería navegable de cada personaje/pose y visor de escenarios/capas/efectos | Cobertura del 100% de recursos renderizables esperados y ausencia de referencias rotas | Galería PAT 20/20; para BG34, Vita3K decodifica 30+30 tiles, 4 bitmaps y 30 sprites `objectFa`. Los 34 recursos auxiliares se inspeccionan en catálogo, pero aún no se presentan como objetos animados del escenario. Falta auditar composición y referencias de todos los IDs. La auditoría PAT cubre las 12,189 imágenes de pose de 20 candidatos |
| M4: motor de personajes | Locomoción, ataques A/B/C, habilidades, proyectiles, hitboxes, combo, guardia, hitstop, daño, KO y rondas para todo el roster | Acciones alcanzables comparadas por frame contra PC en personajes y casos acordados | 19 handlers con rutas 408/418 y moveLocks comprobados; 35 impactos directos PAT verificados. Los dispatchers seleccionan Alice 849 seq. 19 (408), 21/23 (418), Suwako 989 seq. 5 (408) y 808 seq. 0 (418); cuatro variantes ofensivas PAT (Alice 418 seq. 21/23 y Suwako 408/418) más Alice 408 sin caja. Hay runtime experimental visible; spawn/anclaje parcial contrastados con x86 y Vita3K 5/5. En Suwako 418, poses 5–17 ajustan movimiento y el gate de creación es contador impar 1–19; Vita3K schema19 verificó diez spawns. La asociación DI-secuencia0 es hipótesis; coordenadas, trayectoria, vida, ciclo de vida y daño por frame siguen pendientes. Remilia 2C/412 tiene probe dedicado. Reimu tiene 12 cartas mapeadas por contexto; `00489660` modifica niveles/variantes y consume cartas. El gate estático requiere cancellable, `actionLock<51`, spellcard, estado y costo válido. Ruta Vita de prueba 103 → acción PAT 560: Iteración 49 conserva el orden original, sin daño en los primeros 11 updates y primer impacto al entrar en seq. 1 en el update 12; Vita3K schema21 conserva las regresiones del roster, escenario, dash y B/C. La asignación de slot es fija: mano/costo/consumo/mejora, cancelaciones, aire, objetos de las otras skills, byte `+0x836` y paridad por frame PC siguen pendientes. También faltan objetos completos, cartas, hitstop y KO. Ver [ITERATION49.md](ITERATION49.md), [ITERATION48.md](ITERATION48.md), [ITERATION47.md](ITERATION47.md), [ITERATION45.md](ITERATION45.md), [ITERATION44.md](ITERATION44.md), [ITERATION42.md](ITERATION42.md), [ITERATION40.md](ITERATION40.md), [ITERATION39.md](ITERATION39.md), [ITERATION38.md](ITERATION38.md), [ITERATION37.md](ITERATION37.md), [ITERATION36.md](ITERATION36.md), [ITERATION35.md](ITERATION35.md), [ITERATION34.md](ITERATION34.md), [ITERATION33.md](ITERATION33.md), [ITERATION32.md](ITERATION32.md), [ITERATION31.md](ITERATION31.md), [ITERATION30.md](ITERATION30.md) y [DASH_DISPATCH_COVERAGE.md](DASH_DISPATCH_COVERAGE.md) |
| M5: escenarios y sistemas | Escenarios multicapa, animaciones, colisiones, clima, spirit, cartas, menú/selección y transiciones | Reproducción de cada escenario y mecánica con secuencias trazables y sin recursos ausentes | Pendiente; hay assets de fondo, escena, clima y cartas en los DAT |
| M6: demo integral | Flujo de selección, combate, fin de ronda y galería completa dentro del VPK | Recorrido de todos los personajes y escenarios en Vita3K, cargas/reinicios y regresión determinista | Pendiente |
| M7: rendimiento y hardware | Perfil de CPU/GPU/memoria, optimización del renderer y prueba física | Objetivos FPS acordados sostenidos en PS Vita y sin regresiones visuales/funcionales | Pendiente; Vita física aún no probada |

## Siguiente secuencia de trabajo

1. La demo interactiva actual incluye la galería de 20 PAT. El gate automático comprueba entradas de navegación y textura, pero no es un build de juego completo. Las tarjetas `data/stand/<slug>.cv2` son arte de selección, no frames de pelea.
2. Muestrear visualmente en Vita3K animaciones/poses de los 20 personajes; recorrer y auditar las 24 carpetas de escenario presentes en DAT 10.5/12.3, sus objetos/efectos, y rastrear `common/000 hikakuyou.bmp`.
3. Loader Ghidra: `00408cf0` hace lookup de variantes (`DAT_00896b84=0` en el EXE base); `00409b50` calcula CRC32 plegado a mayúsculas, `0041c530` busca el árbol y `0041c080` comprueba nombres ante colisiones. `0041bb50` descifra y enumera el DAT, `0041bdd0` inserta rutas, offset y tamaño. Los 74 nombres idle heredados ya se resuelven con `th105a.dat`.
4. Correlacionar transiciones, variantes PAT y daño con pseudocódigo/trace por personaje. El port C del helper `0046cc90` se contrasta como ARMv7 contra x86: 17 casos fijos más 384 secuencias generadas pasan. El historial de 90 muestras también se prueba con wrap, y `NRNR`/`NLNL` reemplazó el atajo de dos toques en el combate. En Vita3K, 35 dashes aplican daño PAT directo. El análisis estático resuelve las secuencias creadas por Alice 408/418 (849: 19, 21/23) y Suwako 408/418 (989: 5; 808: 0); tres tienen cajas ofensivas en PAT y una no. Falta portar y validar update, colisión y daño de esos objetos. El empaque de `0046d5d0` ya está fuente-base; controles configurados, neutralización exacta, replays y timing PC todavía deben probarse. `0046d950` resembraría `Player+0x7b0` durante inicialización/transiciones. Remilia conserva su 2C/412. Próximo: recuperar update y colisión y comparar con trazas PC. Ver [ITERATION34.md](ITERATION34.md), [ITERATION32.md](ITERATION32.md), [PORT_REFERENCES.md](PORT_REFERENCES.md), [INPUT_STATE.md](INPUT_STATE.md), [ITERATION27.md](ITERATION27.md), [ITERATION26.md](ITERATION26.md), [ITERATION22.md](ITERATION22.md) e [ITERATION23.md](ITERATION23.md).
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

La secuencia del objeto 808 está resuelta por customData[2] según el initializer de Suwako ya auditado en ITERATION34; no depende de rg4. Unicorn ejecuta el initializer original y confirma secuencia 1 para ambos hijos. El factory virtual y el reloj externo del subframe siguen pendientes para una trayectoria nativa comparable, además de hitbox/ciclo de vida. Ver [ITERATION70.md](ITERATION70.md).

## Actualización Iteración 1.71

Se corrigió otro offset crítico en el modelo 808: +0x113 es alpha RGBA, no subframe. Seq.1 reduce alpha en pasos de 8 y deja de integrar posición bajo 8. El constructor/factory debe confirmar alpha inicial y valores RGB; collision, vida y salida siguen pendientes antes del port Vita. Ver [ITERATION71.md](ITERATION71.md).

## Iteración 1.72: auditoría de transferencia TH075 y alpha 808

La revisión comparativa de TH075 confirma que su mapa CFG/cobertura, contratos ABI, watchdog y metodología de medición son buenas referencias; su runtime x86→C, loader, imports, renderer y direcciones son específicos/no validados para TH123 y no se copiaron. Detalle en [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md).

Se corrige una suposición del harness 808: `object+0x113` es alpha; el valor inicial 255 era inyectado. `0x799000` no escribe el byte y `0x438bb0` configura color desde `+0x10c`, sin tocar `+0x113`. La ruta de creación real está pausada antes del objeto por el pool/manager y sus datos de animación. Se requiere reconstruir ese estado antes de calcular una trayectoria natural o cambiar el placeholder Vita.

### Gate técnico 808 actualizado (Iteración 1.72)

El ctor aislado `783a70` y la cadena `setAction→setSequence→initializeAction` ya corren con asignaciones internas cdecl controladas y mapa PAT sintético. El constructor del sprite deja color blanco/alpha 255; los setters preservan el color. Sigue pendiente integrar manager/handles del factory, además de frame data auténtico, colisión y vida antes de portar. Véase [ITERATION72.md](ITERATION72.md).

La prueba aislada `x86_suwako_808_action_probe.py` ahora ejecuta `setAction→setSequence→setPose→initializeAction` con mapa PAT sintético y demuestra la selección de seq.1/frame0, la velocidad radial, y que no hay escritura de RenderInfo al inicializar. El alpha de entrada depende todavía del allocator/pool de la factory; no marcar el proyectil completo ni portarlo hasta medir la asignación/reuso y recuperar update/colisión/vida. Ver [ITERATION72.md](ITERATION72.md).
