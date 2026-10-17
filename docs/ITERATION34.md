# Iteración 1.30: rutas de objetos de Alice y Suwako

## Hallazgo

Las cuatro rutas 408/418 de Alice y Suwako no colocan una caja ofensiva en la pose directa del personaje, pero sí alcanzan `Player::createObject` (`0046eb30`). Tres seleccionan variantes de objeto con cajas ofensivas y una (Alice 408) no. Se fijó el ejecutable con SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` y se siguieron las tablas de salto del dispatcher con Capstone.

| Personaje | Acción | Entrada de tabla → bloque | Factory y PAT de objeto | Evidencia XML asociada |
|---|---:|---|---|---|
| Alice | 408 | `005100b0` → `0051484d` | `0046eb30`, objeto `0x351` (849), `customData[2]=19` selecciona secuencia 19 | `alice.xml`, move 849 índice 19 no tiene caja ofensiva. El trait `damage=200` sin caja no demuestra impacto; esta ruta crea un objeto, pero no un golpe confirmado |
| Alice | 418 | `005100b0` → `0051552f` | `0046eb30`, objeto `0x351` (849); secuencia 21 en los subestados 2/4 y 23 en 3/5 | `alice.xml`, índices 21 y 23 tienen 4 frames de daño 450 con cajas ofensivas |
| Suwako | 408 | `00765ab0` → `0076df42` | `0046eb30`, objeto `0x3dd` (989), `customData[2]=5` selecciona secuencia 5 | `suwako.xml`, move 989 índice 5 contiene frames dañinos de 800 con cajas ofensivas |
| Suwako | 418 | `00765ab0` → `0076f3b4` | `0046eb30`, objeto `0x328` (808), `customData[2]=0` selecciona secuencia 0 | `suwako.xml`, move 808 índice 0 tiene 10 frames con daño 100 y caja ofensiva en cada frame |

La selección de secuencia se confirmó en los inicializadores virtuales de objeto: Alice `GameObjectAlice::initializeAction` (`0053ce80`) y Suwako (`00799000`) leen el tercer float de `customData` y lo pasan a `setSequence`. El `GameObjectList` de Alice (`005246e0`) y Suwako (`00784020`) copia el buffer de 3 floats al objeto antes de invocar `setAction`. Así se correlaciona cada llamada de creación con la variante concreta del XML.

Esto corrige la lectura anterior basada solo en PAT del personaje: `hitbox dañina ausente` significa que esa acción no tiene caja directa allí, no que la acción completa sea inocua. Tres de las cuatro rutas seleccionan variantes PAT con cajas ofensivas; Alice 408 selecciona un objeto sin caja ofensiva.

## Límite de la evidencia

Se confirmó el factory, la secuencia seleccionada y la presencia de cajas/daño en los moves de Alice 418, Suwako 408 y Suwako 418. Aún no se reconstruyeron su velocidad/actualización por frame, colisión, eliminación y daño efectivo; por ello todavía no se marcan esos impactos como reproducidos en el motor Vita.

Los siguientes callbacks quedaron localizados en las vtables de los objetos: Alice `update` `00527280`, Suwako `update` `007876d0`, y `updatePhysics` compartido `00475790` (retorno inmediato). Por ahora esto solo acota dónde se calcula el movimiento: las funciones `update` hacen dispatch por action y sequence y falta aislar el camino específico de cada objeto.

El pseudocódigo Ghidra sigue pendiente: la importación y análisis completo del PE se reutilizaron en un proyecto nuevo, pero el compilador de scripts Java falló al intentar resolver JAR de la instalación compartida (`GraphServices/jheaps-0.13.jar` y `Processors/Dalvik/Dalvik.jar`, `AccessDeniedException`). El análisis de flujo de control se hizo sobre el PE fijado por hash; sus listados están en el área ignorada `artifacts/ghidra/object-analysis/capstone/`.

## Próximo paso

Seguir los bloques por secuencia en `00527280` y `007876d0`, y después recuperar colisión/eliminación del objectList para los objetos 849, 989 y 808. Mapearlos a la simulación Vita. La prueba debe reproducir las tres secuencias ofensivas y la ruta no ofensiva de Alice 408, verificando daño, cajas, posición y duración frente al juego original antes de contarlas como jugables.
