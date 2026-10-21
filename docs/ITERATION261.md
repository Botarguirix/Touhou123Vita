# Iteración 2.161: escritor estático de `+0x884` pertenece a Reimu

Se volvió a revisar el PE de referencia fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. La referencia ejecutable aparente `0x490795` está dentro de la función que comienza en `0x490490`; la función escribe `word [ESI+0x884]=BX` y `word [ESI+0x886]=BX` en ese bloque, y contiene más accesos/escrituras a `+0x884` hasta limpiar o decrementar el campo.

El manifest Ghidra ya existente identifica `0x85bf4c` como vtable de Reimu y asocia su slot 10 con `0x490490` (`artifacts/kernel/f0db.../manifest.tsv`, filas 11 y 88). La misma tabla identifica `0x4ae670` como slot 20 de Reimu, concordando con los análisis anteriores de su handler. En cambio, el vtable de Suika en `0x85da84` señala slot 10 `0x5ee620` y callback de acción `0x6086a0`. Así, `0x490490` es una escritura válida del mismo desplazamiento en otra clase Player, pero **no** es evidencia de que Suika produzca su `+0x884` por esa ruta.

Un barrido Capstone lineal de secciones ejecutables tampoco decodifica esta zona como instrucciones continuas: `0x490490` está en una región que el barrido lineal trata como datos/entrelazado, mientras la tabla de saltos de la función alcanza el bloque `0x490795`. Esto explica por qué el barrido lineal no basta para descartar referencias y confirma que los candidatos requieren anclaje a límites de función/vtables. No se extrapola el significado del campo de Reimu al de Suika.

Resultado y siguiente paso: excluir `0x490490` de los candidatos de productor Suika; recuperar la función slot 10 real de Suika (`0x5ee620`) y las rutas de manager/callback de combate para buscar escrituras naturales, después repetir el hook de memoria con más de una clase de reacción. El producer de Suika y el significado de action96 permanecen sin resolver.

Verificación: dirección de función y escrituras contrastadas con disassembly Capstone; identidad de clase y slots cotejados contra el manifest Ghidra existente y vtable del PE. Sin cambios al runtime Vita ni VPK.
