# Estado del proyecto

Fecha de esta evaluación: 2026-10-13 (America/Mexico_City).

## Verificado

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
- VPK automático probado: SHA256 `4c3221db73d4abe7614e93b53d9968f24f029c284f07aed712bd240f8e4b52dd`.
- VPK interactivo: SHA256 `c72b0bea59f676c2d3866a8e0895630fd8c4360bfd6da81c7c853258cb368ac8`.
- Vita3K `0.2.1 4170-7e152b66`, frontend SDL, Vulkan, entorno aislado con copia del firmware local. Se usó una copia de la versión instalada en `windows-latest`; la versión `4103-e6ac4272` de la carpeta indicada inicialmente no completó el arranque automático Qt.
- El cierre inicial provocaba un acceso inválido al liberar el framebuffer aún en uso. Corregido conservando los buffers hasta la salida del proceso. Última ejecución: salida 0 y sin error crítico de runtime.
- Capturas del framebuffer generadas por el guest dentro de Vita3K: menú, configuración de práctica y pelea; revisadas visualmente. No son capturas de la ventana del host.
- Controles manuales de teclado aún pendientes: el usuario detuvo Computer Use con Escape. No se reanudó ese control ni se afirma que entradas físicas estén verificadas.
- Repositorio privado creado y código subido a [Botarguirix/Touhou123Vita](https://github.com/Botarguirix/Touhou123Vita), tras confirmar cuenta/destino y verificar el payload sin archivos comerciales.

## Pendiente del port original

Ninguna parte del combate original ha sido reconstruida y validada contra PC. El núcleo jugable actual es un prototipo propio. No están implementados los movimientos reales, decks, clima, animaciones originales, sonido, historia, netplay ni paridad de replays. PS Vita física no probada.

Los resultados locales completos están bajo `artifacts/`; no se publican recursos comerciales ni pseudocódigo bruto.
