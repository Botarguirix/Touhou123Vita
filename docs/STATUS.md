# Estado del proyecto

Fecha de esta evaluación: 2026-10-17 (America/Mexico_City).

## Iteración 2.08: callsite Remilia 412 → objeto 801

- Probe x86 ejecuta el bloque original de subestado 4 y captura ID 801, coordenadas `(403,360)`/`(237,360)` para facing `+1`/`-1`, bloque temporal `[-70,12,0]` y callback indexado por EBX. El punto de entrada, EBX, tabla, retorno del manager y dispatcher externo son fixtures; no prueba combate natural, actualización, impacto ni daño. Suite Python 40/40. Ver [ITERATION108.md](ITERATION108.md).

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

El checkout actual compiló un VPK auto-test y pasó una corrida fresca Vita3K aislada de 600 frames (schema28), SHA-256 11d0c4df4f35a27edd275ef0bb96ed4f8751df26ba9a68c3576700ad385873c3. Reportó roster PAT/combate/cartas 20/20, DAT 31, 148 texturas, BG34 capas/tiles/objetos, rutas dash, Suwako 418 diez spawns y skills Reimu 540/565/505 con los daños esperados por los probes. Es una regresión de la versión integrada; no incluye el cambio de oracle 808, que aún no está portado. Reporte rtifacts/vita3k-result.json; capturas rtifacts/screenshots/. Ver [ITERATION68.md](ITERATION68.md).

## Iteración 1.69: cadence corregido del objeto Suwako 808

La revisión del handler seq.1 mostró que solo integra posición al alcanzar subframe 8; cada callback aplica gravedad 0.2 y suma 0.005 a +0x11c/+0x120. Se corrigió el harness para conservar ese escalar y el reloj externo; la trayectoria previa de ITERATION67 queda supersedida. Con secuencia 1 explícita, 24 callbacks dan (287.6873,428.4290) y (279,430.9731) para ambos custom data. Prueba enfocada 7/7. Factory real, secuencia natural, colisión y vida siguen sin resolver; no se alteró el motor ni el VPK. Ver [ITERATION69.md](ITERATION69.md).

## Iteración 1.70: secuencia radial del objeto 808

El selector de secuencia viene de customData[2] (contrato de initializeAction 0799000 documentado en ITERATION34), no del rg4 independiente de la fábrica. Los custom data del split terminan en 1; la ejecución Unicorn del initializer original confirma +0x13e=1 y el vector radial. La traza 24 callbacks se regeneró. El reloj externo, factory virtual, colisión/ciclo de vida siguen controlados/no probados end-to-end. Suite enfocada 7/7; el VPK sigue sin cambio. Ver [ITERATION70.md](ITERATION70.md).

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
