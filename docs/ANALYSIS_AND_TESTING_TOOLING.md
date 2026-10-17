# Herramientas para acelerar el análisis y las pruebas

## Hallazgo principal

El artículo de MS Reverse Engineering comparte una muestra educativa de un curso: material de ensamblador x86, ejercicios y código Python para ensamblar/desensamblar. La parte transferible al proyecto es el método de análisis de programas binarios con SMT: simbolizar entradas, encontrar condiciones de rama y generar casos que alcancen rutas concretas. No es un desempaquetador ni una solución lista para reconstruir el juego. Este repositorio ya tiene Capstone, Unicorn y Ghidra; conviene añadir ejecución simbólica solo para los gates concretos que bloquean una ruta.

## Recursos evaluados

| Recurso | Uso posible aquí | Prioridad |
|---|---|---|
| [Artículo del curso SMT](https://www.msreverseengineering.com/blog/2015/7/30/smt-based-binary-program-analysis-course-sample-x86-assemblydisassembly) | Ideas y ejercicios de análisis simbólico; la muestra es didáctica, no un pipeline de portabilidad | Referencia |
| [SokuMods](https://github.com/SokuDev/SokuMods) | Mods de diagnóstico para el juego de PC original. ReplayInputView+ muestra entradas, hitboxes y datos de estado; permite pausar, avanzar un cuadro, acelerar y ralentizar. LabTool expone frame data y reinicio/guardado de posiciones. Es el camino más directo para observar el comportamiento de referencia | Alta |
| [th123_toolset](https://github.com/kghost/th123_toolset) | Extractor/conversor alternativo de DAT y CV0/CV1/CV2, útil para contrastar parsers o recursos que nuestro lector aún no cubra. Tiene licencia GPL-2.0; mantenerlo como herramienta externa de análisis | Media |
| [angr](https://docs.angr.io/en/v9.2.162/analyses/cfg.html) | CFGFast estático para contrastar límites de funciones y bloques; CFGEmulated intenta cubrir flujo dinámico, pero es más lento y puede fallar en emulación del entorno | Media, focalizada |
| [Triton](https://github.com/JonathanSalwan/Triton) | Ejecución simbólica dinámica, taint y solucionador SMT en x86. Posible extensión del harness Unicorn para descubrir entradas que cruzan un guard concreto | Media, experimento aislado |
| [Miasm](https://github.com/cea-sec/miasm) | IR, emulación y análisis simbólico para PE/x86; puede contrastar resultados, pero duplica mucho el stack actual y tiene licencia GPL-2.0 | Baja |

Las herramientas de análisis de terceros no deben incorporarse al binario Vita. Primero validar las licencias y mantener parsers/solvers como dependencias de desarrollo separadas.

## Cómo usar SMT/DSE en este proyecto

El artículo ayuda como guía conceptual, pero no justifica reescribir el análisis. Para un caso acotado, fijar un handler y su estado de entrada, marcar como simbólicos solo los campos relevantes (por ejemplo, input reciente, `CollisionType`, lock o frame PAT), y pedir una ruta que alcance un bloque/llamada objetivo. Guardar el modelo resultante como fixture determinista; reproducirlo después con Unicorn y comparar registros, escrituras y llamadas con el harness actual. Si requiere emular el motor completo o stubs extensos, detener el experimento: el coste probablemente supera el beneficio.

Prueba candidata: el gate de Remilia 5AA→5AAA. Resolver qué estado mínimo de contacto hace que el handler consulte `CollisionType` no nulo/no 3 y llegue al setter de 321; después confirmar el modelo mediante una corrida Unicorn instrumentada. Esto solo encuentra un test de la rama, no demuestra que el combate natural produzca ese estado.

## Prueba de referencia rápida con el juego de PC

1. Abrir la pelea/replay de historia reproducible en el juego original e instalar una compilación local de SokuMods con ReplayInputView+ y LabTool.
2. Reproducir alrededor del contacto y usar pausa/avance de un cuadro; mostrar entradas y hitboxes. Registrar personaje/acción/pose de ambos luchadores, frame del replay, posición, cajas, estado de impacto/bloqueo y el cambio de acción posterior.
3. Usar guardado/restauración de posición o macros de PracticeEx para repetir el mismo contacto con pocos cambios controlados.
4. Convertir la secuencia en fixture para el harness x86 y ejecutar la misma entrada en el port. Comparar primero transición, frame, colisión y HP; luego apariencia.

Los atajos exactos dependen de la versión de ReplayInputView+; confirmar el README de la compilación instalada. El proyecto aún no tiene un parser dedicado de replay, así que la primera ganancia puede obtenerse inspeccionándolo en el juego y transcribiendo una ventana pequeña. Después conviene automatizar el parser/trace si el formato de replay lo permite.

## Escalera de pruebas para reducir tiempo

- **Cada cambio de regla C:** correr los contratos host ya definidos en CMake y la prueba unitaria afectada; evita abrir Vita3K por una regresión de lógica evidente.
- **Cada cambio de oráculo x86:** correr solo la sonda Python/Unicorn implicada y revisar su JSON/traza; agregar el caso mínimo que reproduce el hallazgo.
- **Cada cambio de contenido o una función integrada:** recompilar VPK y hacer un smoke corto en Vita3K, verificando arranque, pantalla objetivo y reporte fresco.
- **Antes de entregar un VPK y tras cambios amplios de runtime:** ejecutar `tools/vita3k-test.ps1`, que valida el recorrido integral actual de 600 frames, roster, recursos, escenas y probes.

El runner actual está deliberadamente construido como gate integral de 600 frames y valida varias capturas y muchas propiedades; acortar el límite sin perfiles de prueba coherentes causaría falsos fallos. Mejora futura recomendada: agregar perfiles explícitos `smoke` y `full`, donde `smoke` compruebe boot, menú, una escena/animación y un combate corto, con su propio schema y criterios, manteniendo `full` como gate existente. Registrar tiempos por fase para ver si Vita3K, compilación o inicialización es el cuello de botella.

## Siguiente paso recomendado

Usar el replay PC con ReplayInputView+ para capturar una ventana de 10–30 frames alrededor de un golpe que habilite el cancel de Remilia. Convertirla en fixture, usarla para terminar la sonda de interacción x86 y solo entonces integrar el estado confirmado al runtime. En paralelo, prototipar una opción `smoke` de Vita3K sin debilitar el runner integral. No instalar Triton/angr hasta identificar una rama concreta cuyo fixture manual cueste más que el setup simbólico.

