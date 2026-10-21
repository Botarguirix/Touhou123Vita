# Iteración 2.147: experimento intermedio de input y rama Suika

Esta iteración encadenó updates de input y el matcher originales con un salto al bloque interno de Suika, pero usó action 300 como precondición. La auditoría del flujo desde el prólogo en la Iteración 2.148 demostró que el handler carga `BX=0xc8` y la acción correcta es 200. Por tanto, este experimento no acredita la transición Suika 418; el resultado corregido está en [ITERATION248.md](ITERATION248.md).

La secuencia de muestras N,R,N,R y el bit NRNR siguen siendo evidencia válida del matcher, aislada de la conclusión incorrecta sobre el handler. NRNR tampoco se atribuye como causa de 418: el handler consulta el KeyInput actual y requiere el estado previo de dash.
