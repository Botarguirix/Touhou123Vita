# Iteración 2.104: el ciclo global separa selección y actualización del manager

La sonda de selección se amplió con el dispatcher `0x43d480` y el setter de modo `0x43d8e0`. En el PE original 2009 (SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`), el dispatcher lee `[0x85ec0c]`: el caso 2 llama a `0x43cca0`, que selecciona/inicializa el manager según `[0x85ec10]`; los casos 3, 4 y 5 llaman a `0x437790`, `0x4377b0` y `0x4377e0`, respectivamente. El setter `0x43d8e0` escribe su primer argumento en `[0x85ec10]`.

Esto muestra dos estados distintos en el ciclo global: el estado `[0x85ec0c]` decide si se selecciona el manager o se ejecuta uno de sus dispatchers; el modo `[0x85ec10]` escoge la variante del manager. Los casos 0 y 6 de ese segundo selector llegan a inicializadores Story y publican el objeto en `[0x85eb64]`. No se ha medido qué valores toman ambos estados durante la reproducción Sanae ni cuántas veces el ciclo corre por frame.

Se mantiene el límite anterior: `0x42d6b0` configura flags de fuentes en el objeto global de input `[0x85ec98]`; no hay evidencia de identidad entre ese receptor y el `this` de `0x42a410`. Por ello no se cambia el consumo del cursor en el runtime Vita.

La regresión estática verifica la selección de los modos Story, la escritura del modo global y los destinos del dispatcher del ciclo. Pasó junto con las pruebas previas de dispatch/layout. Próximo: seguir el evento de entrada al replay hasta las escrituras de `[0x85ec0c]` y `[0x85ec10]`, y luego capturar frame-step/cadence del PE.
