# Iteración 2.04: factory original de Remilia 801 bajo Unicorn

El harness de factory x86 se parametrizó por personaje/acción y se amplió el espacio del fixture PAT para secuencias de 20 frames, conservando los valores por defecto de Suwako 808. La regresión original de Suwako vuelve a completar factory y ocho updates con action 808/seq.1.

Con Remilia action 801, el factory original `0x784020` crea el objeto (vtable `0x85f22c`) y ejecuta su initializer; el resultado es action 801, seq.1, posición controlada `(300,400)`, color/alpha inicial blancos y `+0x34c=1`. El harness también ejecuta el selector de pose y sincronizador original `0x465e10`: PAT seq.0 publica una attack box y seq.1 ninguna, con cero hurtboxes en ambas.

El update original `0x7876d0` avanza tres ticks en seq.1; en el cuarto intenta continuar por una ruta de servicio/recursos del motor y falla con lectura fuera de memoria (`EIP=0x4818c2`, cerca de la ruta `0x43fe10/0x8248a5`). El probe no tiene inicializados esos servicios globales. Por eso no se afirma ciclo de vida, secuencia ofensiva natural ni daño. El trace de fallo se conservó en `artifacts/kernel/remilia-object801-factory.json` (ignorado). `pytest` no está instalado en el Python local; la regresión funcional del harness Suwako se ejecutó directamente y pasó.

Siguiente: mapear/stubear con contrato los servicios exactos del host que bloquean el tick 4, sin sustituir la lógica del update; luego correr el objeto con el sequence/setup real que entrega la rama 412 y comparar su contacto/daño. Sin runtime Vita ni VPK nuevo.
