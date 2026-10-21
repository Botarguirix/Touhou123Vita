# Iteración 2.117: VPK actual revalidado y evaluación de psp2-tooling

Se reconstruyeron los paquetes interactivo y de autotest desde el árbol de trabajo con VitaSDK 2026.08:

- Interactivo: [Touhou123Vita-current.vpk](../artifacts/Touhou123Vita-current.vpk), SHA-256 `28687a897ab8bc773e98b62d5502c9422c175d3689d707a099b0f8c6585e619b`.
- Autotest: [Touhou123Vita-current-auto.vpk](../artifacts/Touhou123Vita-current-auto.vpk), SHA-256 `8a109a285c0587530c48231bf1347b6daafe7d2b99a95210b0d533f74345965a`.
- Vita3K SDL produjo evidencia fresca con `status=passed`, schema 46 y 600 cuadros. Pasaron el gate de regresión, recorte PAT, cámara/viewport, rutas de objetos y contratos de scroll/layout de BG33, BG36, BG37 y BG38. El reporte incluye el hash exacto del autotest: [vita3k-result.json](../artifacts/vita3k-result.json); las capturas están en [screenshots](../artifacts/screenshots/).

Este resultado verifica que el autotest del prototipo arranca, ejecuta el recorrido instrumentado y termina en Vita3K. No demuestra paridad completa con el original: los recursos propios del usuario deben estar disponibles para su lector DAT, el combate todavía no cubre todas las rutas de todos los personajes, los escenarios no están integrados en una campaña completa y el replay Sanae aún no controla el combate Vita. Tampoco es una medida de FPS en una consola.

## Evaluación de psp2-tooling

[Grarak/psp2-tooling](https://github.com/Grarak/psp2-tooling) agrega herramientas host para la fase de Vita física: transferencia y lanzamiento por USB/host0, entrada, capturas, consola, volcados y perfilado CPU/GPU. Es complementario a Vita3K: puede ayudar a medir cuellos de botella después de que una escena de combate integrada sea representativa, pero no acelera análisis del PE x86, no compila el proyecto y no ejecuta pruebas de Vita3K.

La ruta DevKit del repositorio es Linux-only y lista dependencias que incluyen VitaSDK y pyusb; perfiles y capturas añaden libdw/perf/Hotspot o ffmpeg/arecord. La alternativa `retail-cp` tiene una condición mucho más estrecha: README documenta PCH-2000, firmware 3.65, Ensō/taiHEN y módulos DevKit 3.65 que se deben aportar; además altera el modo de depuración, USB y manejo de fallos de la consola. Por eso no forma parte del ciclo inmediato ni se instala sobre una Vita retail sin verificar compatibilidad. Se conserva como herramienta externa para la fase de rendimiento en hardware. Referencias: [README](https://github.com/Grarak/psp2-tooling), [RETAIL.md](https://github.com/Grarak/psp2-tooling/blob/main/RETAIL.md).

## Siguiente trabajo

1. Continuar cerrando el replay Story en el PE de 2009: identificar quién invoca el slot virtual 5 de `CBattleManagerStory` en el ciclo real y medir cuándo el callback de slot 16 consume cada pareja respecto a los ticks de simulación. No inferir cadence por frame de la ejecución de 16,910 parejas en el harness.
2. Mantener Vita3K como gate barato de integración; usar `tools/vita3k-test.ps1` para la corrida integral antes de compartir un VPK.
3. Retomar `psp2-tooling` al disponer de Linux y Vita física compatible, cuando haya una pelea integrada con sprites/objetos/escenario que merezca perfilar. La configuración `retail-cp` no es un requisito para seguir decompilando o generando VPK.

