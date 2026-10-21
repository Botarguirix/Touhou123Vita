# Iteración 2.64: conexión entre selección de replay y decoder

## Ruta de entrada observada

En el ejecutable original TH123 2009 fijado por SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`, el manejador que empieza en `0x44a0e0` obtiene componentes de la ruta seleccionada, los pasa al formateador indirecto en `0x44a12c` y llama a `0x42e030` en `0x44a141`. Si el loader devuelve éxito, el flujo pide la transición `0x28` mediante `0x43d010` y asigna `6` a `0x848a94`. La evidencia liga el parser a la selección de un replay desde la interfaz y al cambio de estado posterior; por sí sola no confirma qué se reproduce en el combate.

## Estado del objeto del loader

El código de `0x42e030` establece estas relaciones de layout:

- lee 10 bytes de cabecera en `objeto+0xe8`;
- usa el byte `objeto+0xef` como límite del loop de registros;
- inicializa una colección asociada a `objeto+0xf4` y decodifica cada registro llamando a `0x42cd60`;
- avanza el destino `0x50` bytes por iteración, consistente con el stride observado por el parser estructural;
- escribe `objeto+0x140 = objeto[0xef] - 1` y activa indicadores en `+0x6c` y `+0xd4` cuando termina.

Estas son relaciones de control y almacenamiento verificadas en el desensamblado, no nombres semánticos de campos. La función `0x42cd60` serializa/deserializa dos secuencias `uint16` por registro, pero esta iteración no demuestra si contienen entradas, tiempos, índices u otro tipo de evento.

## Siguiente análisis

Seguir las lecturas del objeto/campo `+0xf4` después de la transición y del miembro `+0x140`, incluyendo despacho indirecto y los inicializadores del estado `6`. Identificar un consumidor que avance una secuencia y correlacionar su valor con una captura frame-stepped del replay en el ejecutable original. Hasta tener esa correlación, no conectar el parser al runtime Vita ni etiquetar los vectores como inputs.

## Alcance y verificación

El análisis se hizo con Capstone sobre el PE original presente en `F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe`; el SHA-256 coincide con el perfil de build 2009. No se modificó código de juego, no se recompiló el VPK y no se hizo una nueva corrida de Vita3K. El artefacto estructural previo y sus seis pruebas sintéticas siguen documentados en [ITERATION163.md](ITERATION163.md).
