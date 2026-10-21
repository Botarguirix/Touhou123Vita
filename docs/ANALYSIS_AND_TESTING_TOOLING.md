# Herramientas para acelerar el análisis y las pruebas

## Hallazgo principal

El artículo de MS Reverse Engineering comparte una muestra educativa de un curso: material de ensamblador x86, ejercicios y código Python para ensamblar/desensamblar. La parte transferible al proyecto es el método de análisis de programas binarios con SMT: simbolizar entradas, encontrar condiciones de rama y generar casos que alcancen rutas concretas. No es un desempaquetador ni una solución lista para reconstruir el juego. Este repositorio ya tiene Capstone, Unicorn y Ghidra; conviene añadir ejecución simbólica solo para los gates concretos que bloquean una ruta.

## Recursos evaluados

| Recurso | Uso posible aquí | Prioridad |
|---|---|---|
| [Artículo del curso SMT](https://www.msreverseengineering.com/blog/2015/7/30/smt-based-binary-program-analysis-course-sample-x86-assemblydisassembly) y [SMTSample](https://github.com/RolfRolles/SMTSample) | Muestra con código Python, ejercicios, implementación y slides x86. Referencia educativa, no un motor SMT listo para nuestro PE ni integración con Unicorn. | Referencia/prueba puntual |
| [SokuMods](https://github.com/SokuDev/SokuMods) | Mods de diagnóstico para el juego de PC original. ReplayInputView+ muestra entradas, hitboxes y datos de estado; permite pausar, avanzar un cuadro, acelerar y ralentizar. LabTool expone frame data y reinicio/guardado de posiciones. Es el camino más directo para observar el comportamiento de referencia | Alta |
| [th123_toolset](https://github.com/kghost/th123_toolset) | Extractor/conversor alternativo de DAT y CV0/CV1/CV2, útil para contrastar parsers o recursos que nuestro lector aún no cubra. Tiene licencia GPL-2.0; mantenerlo como herramienta externa de análisis | Media |
| [angr](https://docs.angr.io/en/v9.2.162/analyses/cfg.html) | CFGFast estático para contrastar límites de funciones y bloques; CFGEmulated intenta cubrir flujo dinámico, pero es más lento y puede fallar en emulación del entorno | Media, focalizada |
| [Triton](https://github.com/JonathanSalwan/Triton) | Ejecución simbólica dinámica, taint y solucionador SMT en x86. Posible extensión del harness Unicorn para descubrir entradas que cruzan un guard concreto | Media, experimento aislado |
| [Qiling](https://github.com/qilingframework/qiling) | Capa de sistema operativo sobre Unicorn con loader PE, imports y hooks. Puede servir para explorar una rutina que necesite contexto Win32; no reemplaza nuestras sondas deterministas, porque configurar el entorno del juego y sus APIs sería trabajo adicional. | Baja, solo si una rutina depende de imports que hoy estorban |
| [Miasm](https://github.com/cea-sec/miasm) | IR y análisis simbólico PE/x86; duplica el stack y tiene licencia GPL-2.0 | Baja |
| [SokuStreaming](https://github.com/SokuDev/SokuStreaming) | API HTTP/WebSocket local: `/state` expone estado; `/internal/*` sirve recursos y convierte CV2→PNG. Registrar snapshots y cotejar assets, validando primero campos disponibles. | Alta |
| [th123toolkit](https://github.com/andry-dev/th123toolkit) | Utilidades DAT/CV0/CV1/CV2/CV3. Contrastar pocos archivos; historial pequeño y código parcialmente atribuido a terceros, revisar licencia/procedencia antes de copiar. | Media |
| [repentogxm](https://github.com/0xl0cal/repentogxm) | Recompilación estática x86→ARM para Vita con runtime, VitaGL y métricas de hardware. Referencia arquitectónica; GPL-2.0, no plug-and-play. | Alta como referencia |
| [D2Vita](https://github.com/Franckrst/D2Vita) | Ejecuta un PE x86 real en Vita con loader Win32, puente de imports y recompilador dinámico x86→ARMv7; su documentación incluye un banco con el ejecutable real sobre QEMU ARM para iterar en escritorio. Demuestra una vía alternativa al port nativo, pero implica portar un runtime Win32/dynarec y revisar licencias; no conviene cambiar el motor actual por esto. | Alta como referencia de estrategia y pruebas |
| [Vita3K CLI](https://github.com/Vita3K/Vita3K/blob/master/vita3k/config/src/config.cpp) | Acepta VPK posicional y modo consola/log/configuración; puede simplificar smoke local. | Alta |
| [psp2-tooling](https://github.com/Grarak/psp2-tooling) | Automatiza validación en Vita física: USB/host0, instalación y lanzamiento, entradas, capturas HDMI, consola, dumps y perfiles CPU/GPU (DTrace/CoreSight y Razor). Linux-only, probado con DevKit FW 3.65. La ruta retail requiere PCH-2000, FW 3.65, Ensō/taiHEN y módulos DevKit 3.65 aportados por el usuario; modifica switches de depuración/USB y comportamiento de fallos. No sustituye Vita3K ni ayuda a decompilar el PE. | Alta para profiling en hardware cuando haya escena integrada y Vita compatible; baja ahora |

Las herramientas de análisis de terceros no deben incorporarse al binario Vita. Primero validar las licencias y mantener parsers/solvers como dependencias de desarrollo separadas.

## Validación futura en PS Vita física

`psp2-tooling` sirve para la fase posterior de validación en hardware, cuando haya una Vita física y un host Linux. `devkit/` puede automatizar copias/instalación de VPK, lanzamiento, entrada, consola y capturas HDMI; `profile/` aporta perfiles CPU y `razor/` procesa métricas/capturas de GPU. Para nosotros lo más útil es medir FPS y localizar cuellos CPU/GPU una vez que la demo integrada llegue a una escena estable. Las capturas CPU pueden reconstruir stacks si el ELF conserva DWARF (`-g`) y el SELF se genera sin ASLR (`vita-make-fself -na`); Razor ofrece métricas y capturas GXM. No reduce el trabajo de decompilación del PE, reconstrucción de mecánicas ni las corridas de Vita3K; tampoco es un SDK de compilación ni genera el VPK del proyecto. Debe mantenerse como herramienta host externa. Operativamente, ahora seguimos con análisis x86, reconstrucción de combate/escenarios y gates Vita3K; retomaremos `devkit/` al tener Linux y una escena integrada representativa. `retail-cp` queda solo como opción si verificamos el modelo/firmware exactos y contamos con los módulos DevKit requeridos, dado que modifica el estado debug/USB de la consola.

El README declara pruebas en DevKit firmware 3.65 y dependencias Linux (`pyusb`, VitaSDK; para profiling, `libdw` y `perf`/Hotspot; para captura HDMI, ffmpeg/arecord). La ruta `retail-cp` es distinta: el repo la documenta para PCH-2000 con 3.65, Ensō y taiHEN, módulos DevKit 3.65 descifrados aportados por el usuario y offsets de kernel específicos. La documentación advierte que cambia switches de desarrollo/debug persistentes, comportamiento de crash/suspensión y USB; por eso no es un paso de instalación general ni aplica a Vita3K. El repositorio tiene licencia GPL-3.0 y se mantiene como herramienta host externa, no en el VPK.

Para perfiles con call stacks, su README requiere compilar el ELF con símbolos `-g` y crear un SELF sin ASLR; el profiling CPU/GPU avanzado necesita además módulos y conexiones específicas de DevKit. Nuestro build normal no habilita ese perfil de depuración. Decisión: no añadirlo al ciclo inmediato; en la fase de pruebas físicas, primero probar solo `devkit/` en el hardware disponible y activar perfiles en una configuración compatible. La ruta retail solo se considerará después de verificar modelo/firmware, disponibilidad legal de módulos y respaldos de recuperación. Fuente: [psp2-tooling README](https://github.com/Grarak/psp2-tooling) y [RETAIL.md](https://github.com/Grarak/psp2-tooling/blob/main/RETAIL.md).

## Cómo usar SMT/DSE en este proyecto

Para un caso acotado, fijar un handler y su estado de entrada, simbolizar solo campos relevantes (input reciente, `CollisionType`, lock o frame PAT) y pedir una ruta que alcance un bloque/call objetivo. Confirmar el modelo como fixture determinista en Unicorn y comparar registros, escrituras y llamadas.

Prueba candidata: el gate de Remilia 5AA→5AAA. Hay contacto geométrico PAT, pero falta el vínculo con `CollisionType`. Simbolizar solo campos del gate si una traza real da demasiados estados; confirmar en Unicorn con servicios externos fijados. Esto genera un caso de prueba, no demuestra combate natural. Triton puede servir en ese experimento acotado; no simbolizar todo el juego.

## Prueba de referencia rápida con el juego de PC

1. Abrir el replay reproducible en el juego de PC con ReplayInputView+ y LabTool; confirmar que el ejecutable corresponde al hash analizado.
2. Avanzar frame a frame por el contacto y registrar 10–30 cuadros antes/después: inputs, acción/pose, posición, cajas, bloqueo/impacto, hitstop y acción resultante.
3. Probar SokuStreaming y guardar snapshots `/state`/WebSocket con tiempos; confirmar campos disponibles, sin asumir hitboxes/pose PAT. Usar `/internal/*` para comparar recursos CV2.
4. Restaurar posición en práctica, variar una condición y convertir la ventana a fixture x86. Comparar transición, frame, colisión y HP antes que imagen.

El README actual indica F10/F9 velocidad, F11 pausa, F12 un frame, F4 hitboxes, F6 diagnóstico y F7 visualización de inputs; validar con la versión instalada. Se encontró `replay/story/090815_2219_sanae_story.rep` (67,881 bytes; SHA-256 `6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e`). Su cabecera `0x100c8` no es aceptada por el PE fijado del proyecto (`0xd2/0x100d2`), pero sí coincide con la build 2009 proporcionada (`th123.exe`, SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`): el helper `0x43ca50` devuelve `0xc8/0x100c8` y el caller `0x42bdd8` compara el valor leído del replay contra dicho helper. El checker verifica ambos perfiles conocidos y genera [replay-compatibility-original-2009.json](../artifacts/kernel/replay-compatibility-original-2009.json) y [replay-compatibility-pinned.json](../artifacts/kernel/replay-compatibility-pinned.json). Esto demuestra compatibilidad estática de versión; el layout se decodificó estructuralmente después, pero aún falta asociar sus campos con el estado del juego y demostrar playback. Ver [ITERATION157.md](ITERATION157.md) e [ITERATION163.md](ITERATION163.md).

La Iteración 2.63 ubicó el loader de datos `0x42e030` y decoder de registros `0x42cd60` en el PE 2009. `tools/inspect_replay_layout.py` consume actualmente los 67,881 bytes con tres registros y sin residuo; esto solo valida el orden estructural de lectura. No se han identificado aún los significados de sus vectores ni se ha demostrado playback. Reporte resumido: [replay-layout-original-2009.json](../artifacts/kernel/replay-layout-original-2009.json); detalles y comando: [ITERATION163.md](ITERATION163.md).

## Escalera de pruebas para reducir tiempo

- **Cada cambio de regla C:** correr los contratos host ya definidos en CMake y la prueba unitaria afectada; evita abrir Vita3K por una regresión de lógica evidente.
- **Cada cambio de oráculo x86:** correr solo la sonda Python/Unicorn implicada y revisar su JSON/traza; agregar el caso mínimo que reproduce el hallazgo.
- **Cada cambio de contenido o una función integrada:** recompilar VPK y hacer un smoke corto en Vita3K, verificando arranque, pantalla objetivo y reporte fresco.
- **Antes de entregar un VPK y tras cambios amplios de runtime:** ejecutar `tools/vita3k-test.ps1`, que valida el recorrido integral actual de 600 frames, roster, recursos, escenas y probes.

El runner valida 600 frames; recortarlo directamente causaría falsos fallos. Crear perfiles `smoke` (boot, menú, escena/animación, combate corto) y `full` (gate vigente), con schema/criterios propios. El CLI Vita3K permite VPK posicional y modo consola, limitado a VPK. Guardar logs, hash VPK y tiempos por fase.

La reducción de tiempo más directa es que el smoke sea un perfil separado, sin debilitar el gate de 600 frames; primero correr la sonda host específica y recompilar Vita solo si cambió código integrado. En el PC, ReplayInputView+ ofrece velocidad, pausa, avance de un frame, cajas e inputs: capturar una ventana del replay reduce la revisión manual de peleas completas. Si SokuStreaming expone por /state los campos necesarios, guardar snapshots con frame y timestamp permitirá comparar corridas repetibles. El banco D2Vita/QEMU ARM inspira un oracle de escritorio para el binario Vita, pero el probe Unicorn ya ejecuta el x86 original y la suite host es más barata para el código portado; conviene medir antes de sumar otro runtime.

## Plan priorizado

1. Ya hay un replay `.rep` reproducible para el PE 2009: `replay/story/090815_2219_sanae_story.rep` con `th123.exe` SHA-256 `24e6149f…`. Abrir esa pareja en ReplayInputView+/LabTool, probar SokuStreaming `/state` y capturar 10–30 ticks con frame-step; registrar input, jugador/acción, cursor y reloj para medir cadence. La build fijada dentro del repo no acepta esa cabecera. Para paridad Remilia, capturar después el golpe/cancel y resolver `5AA → CollisionType → 5AAA`.
2. Contrastar uno o dos assets mediante `/internal` y `th123toolkit`; sustituir parser solo con discrepancias reproducibles.
3. Separar perfil Vita3K `smoke` del `full` actual.
4. Probar Triton/SMT solo si un guard real cuesta demasiado explorar manualmente. No añadir herramientas analíticas al build Vita.

## Foco de la siguiente sonda x86 (Iteración 2.24)

La pareja de Players ya supera la geometría, el hit-confirm y la pérdida de vida: escribe `attacker+0x190=1`, incrementa `defender+0x4b4`, registra `CreateEffect(0xC9, 7, 50, ...)` y baja `Player+0x184` de 1000 a 800. El efecto de reacción se entrega a un objeto sintético en el slot `vtable+0x0c` de `EffectManager_Effect` global `0x8985f0`; esto permite avanzar el resolver, pero no crea/renderiza el efecto original. La traza nueva revela que el resolver pide al defensor acción 50 (no 74), que sí existe en el PAT de Remilia; el fallo posterior apunta al lookup/inicialización de esa secuencia o al contexto que espera el setter. Próximo: registrar el resultado del lookup de acción 50 y compararlo con la inicialización normal de Remilia antes de ampliar el harness. Después cotejar un replay PC de 10–30 frames. Esto es más barato y concluyente que simbolizar todo el resolver; SMT/Triton se reserva para un guard específico que aún no pueda satisfacerse con fixtures deterministas.

Para reducir el costo por intento, primero se corre la sonda Unicorn focalizada y las dos suites de regresión x86. Vita3K no requiere reinicio/rebuild porque este trabajo solo cambia herramientas de análisis; correr el smoke Vita3K al cambiar lógica/runtime del port, y el gate integral de 600 frames antes de entregar VPK.

SMTSample contiene slides, código Python, manual y ejercicios. Integrar su assembler no aceleraría el pipeline actual, que ya usa Capstone y Unicorn.

## Fuentes revisadas (18 octubre 2026)

- [Artículo SMT/x86](https://www.msreverseengineering.com/blog/2015/7/30/smt-based-binary-program-analysis-course-sample-x86-assemblydisassembly) y [SMTSample](https://github.com/RolfRolles/SMTSample)
- [SokuMods](https://github.com/SokuDev/SokuMods), [SokuStreaming](https://github.com/SokuDev/SokuStreaming)
- [th123toolkit](https://github.com/andry-dev/th123toolkit)
- [repentogxm](https://github.com/0xl0cal/repentogxm)
- [D2Vita](https://github.com/Franckrst/D2Vita), [Qiling](https://github.com/qilingframework/qiling)
- [psp2-tooling](https://github.com/Grarak/psp2-tooling) y [requisitos retail-cp](https://github.com/Grarak/psp2-tooling/blob/main/RETAIL.md) (solo etapa de pruebas en hardware físico; revisión de README confirmada el 18 octubre 2026)
- [angr](https://github.com/angr/angr)
- [Vita3K CLI](https://github.com/Vita3K/Vita3K/blob/master/vita3k/config/src/config.cpp)


