# Iteración 2.102: separar el manager Story del estado de canales de replay

La revisión del PE 2009 fijado por SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3` precisó dos piezas que antes estaban mezcladas:

- `0x85eb64` es el puntero global al objeto manager Story. Las rutinas de inicialización que comienzan en `0x4378d0` y `0x43b440` asignan allí el objeto recién construido con vtable `CBattleManagerStory` (`0x82192c`); la segunda además prepara otros objetos asociados. Las rutas de update `0x437790` y `0x4377e0` despachan slots virtuales sobre ese global. Esto vincula la clase Story con el loop global, pero todavía no prueba cuál inicializador se toma para la reproducción Sanae ni cuándo se invoca el loop.
- `0x42a410` decide cuántos canales leer mediante bits separados de `this+0xf0`: bit 0 habilita el canal primario y bit 1 el secundario. Cada canal habilitado llama por separado al consumidor `0x42a3a0`; el primero extrae la máscara baja y seis flags, y el segundo conserva solo la máscara baja. El valor `f0=3` usado en la sonda anterior modela ambos canales habilitados, pero la inspección del decoder por sí sola no demuestra que esa sea la configuración efectiva de cada sesión.

Por tanto, el manager global, la selección de callback por RTTI y los bits de fuentes son tres hechos relacionados pero distintos. El replay almacenado en `replay/story` hace pertinente la ruta Story; no prueba el constructor efectivo ni una correspondencia llamada/frame. No se conectó el cursor al combate ni se alteró el runtime.

La siguiente comprobación debe seguir los callers de los inicializadores hasta el selector de modo de juego y determinar dónde se escribe `this+0xf0` para el objeto que llega al callback Story. Después se necesita una traza con frame-step del PE para relacionar consumo de words y tick; mientras esa observación no exista, no se debe asumir una pareja por frame.

Verificación del análisis: se confirmó el hash del PE original y se volvió a generar el reporte RTTI de la Iteración 2.101. Las rutas de inicialización y el decoder se inspeccionaron en desensamblado; los valores runtime de modo, `f0` y cadence permanecen sin medir.
