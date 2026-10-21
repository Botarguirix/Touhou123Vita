# Iteración 2.74: scroll de nubes BG37/BG38 en Vita3K

Se recuperaron los callbacks virtuales de escenario del PE fijado (`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`):

- BG37 usa update `0x476260`. Incrementa `+0x64`, resta 1.5 de `+0x68` y 1.0 de `+0x6c`; las nubes hacen wrap bajo −1200/−800 a 800.
- BG38 usa update `0x476c90`. Aplica las mismas velocidades y wraps, pero no incrementa `+0x64` en este método.
- Ambos constructores inicializan los offsets de nubes en −400/−300. Los vtables fijan también renderers BG37 `0x4762c0` y BG38 `0x476d60`.

El core C expone estado separado BG37/BG38, incluyendo el contador de BG37. El visor ofrece una página de offsets auxiliares para cada escenario; el selector y el recorrido automático ahora llegan a esas páginas y escriben capturas. La representación sigue siendo un diagrama local: no se integraron las capas en el renderer jugable ni se recuperaron la cámara, el orden alpha, el torii de BG37 o la composición completa.

Verificación: VitaSDK compila el core y `vita_main.c`; 3 pruebas nuevas de contrato cotejan vtables, instrucciones/constants PE y cableado C; suite Python completa 99/99. Vita3K SDL ejecutó un VPK recién compilado por 600 cuadros y pasó schema46/regresión. El gate verificó capturas de ambas páginas y comparó offsets con el número de updates: estado final BG37 −403/−302 en 2 updates y BG38 −406/−304 en 4. Las capturas de escena son [BG37](../artifacts/screenshots/stage-bg37-scroll.bmp) y [BG38](../artifacts/screenshots/stage-bg38-scroll.bmp); el reporte fresco está en `artifacts/vita3k-result.json`.

La escena de referencia PC no se capturó y este paso no afirma paridad visual; los renderers x86 están identificados pero aún requieren análisis de composición. Builds finales: interactivo [Touhou123Vita-latest.vpk](../artifacts/Touhou123Vita-latest.vpk), 93.343 bytes, SHA-256 `f9cb3fab55c65aeee33e8ae6bc5bab285339974bcf8a1cf5c86f6b57afa8dca6`; automático [Touhou123Vita-auto.vpk](../artifacts/Touhou123Vita-auto.vpk), SHA-256 `10f99aa903163e92ad9080dd21d7c13afb82d53fbfad3e9f9e256c77e434f23a`, usado en la corrida Vita3K. El VPK automático solo añade el disparador de pruebas.


**Corrección de mapeo (Iteración 2.75):** la medición numérica de offsets, rates y wrap de este informe sigue vigente, pero la etiqueta “offsets de nubes” para ambos campos BG37 era imprecisa. El renderer asigna `+0x68` a `tori1` y `+0x6c` a `clowd_l`; `clowd_s` ocupa una posición fija. BG38 sí desplaza `clowd_l` y `clowd_s`. Véase [ITERATION175.md](ITERATION175.md).
