# Iteración 2.110: callers directos de los setups de input

La búsqueda previa de referencias con una pasada lineal de Capstone no encontró callers porque algunas instrucciones del PE quedan fuera de alineación en ese barrido. Se corrigió la búsqueda: ahora escanea los opcodes `E8 rel32` de las secciones ejecutables y convierte las coincidencias a callsites, que luego se desensamblan por dirección exacta.

En el PE original 2009 (SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`), `0x43dee0` tiene dos llamadas directas: `0x420a91` y `0x4258fe`. En la primera, un guardado de estado/counter y la llamada `0x41ffa0` preceden al dispatcher. En la segunda, el caller compara el modo devuelto por `0x43ccd0` con `EBX` antes de entrar. `0x43ccf0`, que instala una fuente y null, se llama desde `0x4258ec` y `0x44b091`; en `0x4258ec` el getter de modo acaba de devolver cero, mientras `0x44b091` viene después de copiar datos de configuración/input.

La sonda de manager ahora fija los cuatro callsites y sus guardas locales en `artifacts/kernel/replay-manager-selection-original-2009.json`. Esto demuestra puntos de entrada estáticos y reduce la búsqueda al control de estado de esas rutinas; no demuestra que se ejecuten en el replay Sanae ni el orden efectivo entre ellas y el setter Story `(6,2)`.

No hay un proceso del ejecutable original abierto en esta sesión. Se intentó iniciar el helper de ventanas de solo lectura y falló dos veces con `failed to write kernel assets: El sistema no puede encontrar la ruta especificada. (os error 3)`; los procesos Vita3K existentes se dejaron intactos. Por eso no se obtuvo una captura dinámica de los globals.

Las pruebas `tests.test_replay_manager_selection_probe` y `tests.test_replay_story_callback_probe` pasan (3/3); el runtime y los VPK no cambian. Siguiente: reconstruir la función contenedora de `0x420a91`/`0x4258fe` para recuperar sus estados de entrada y vincular (o descartar) esas transiciones con la selección Story.
