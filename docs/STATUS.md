# Estado del proyecto

Fecha de esta evaluación: 2026-10-13 (America/Mexico_City).

## Verificado

**Estado actual: iteración 0.2.** Ver [ITERATION02.md](ITERATION02.md), [DATA.md](DATA.md) y [KERNEL.md](KERNEL.md). Lo descrito abajo corresponde a la línea base 0.1 para conservar su evidencia histórica.

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
