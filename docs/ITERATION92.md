# Iteración 1.92: candidato de daño directo desde callbacks de personaje

La búsqueda de llamadas directas al helper `0x4799b0` encontró cinco sitios del ejecutable fijado al SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`: `0x47aa8f`, `0x47b1fc`, `0x47b3a6`, `0x47bfc8` y `0x47c318`. Cuatro pertenecen a respuestas de combate/colisión. El otro, `0x47b1fc`, está en `0x47b1d0`, y esa rutina tiene un caller directo fuera del manager: el wrapper `0x4649b0` en `0x4649d2`.

`0x4649b0` reenvía al BattleManager el personaje, su manager rival y cuatro argumentos recibidos. El PE contiene 25 llamadas directas a ese wrapper, incluidas `0x591f6b`, `0x591ff9`, `0x59243f` y `0x592498`, dentro de rutinas del bloque de código de Remilia. Algunas calculan un valor de daño y llaman al wrapper sin una llamada visible a `0x47c770`; por eso esta es una ruta candidata para ataques o efectos especiales con procesamiento directo.

La relación con acción 412 aún no está demostrada. Los bloques examinados contienen condiciones de secuencia/temporizador y daños calculados de 1000 o valores similares; no se aisló una comparación con action 412 ni el primer frame PAT `attackBa002.bmp` de 750. Tampoco prueba que la ruta dependa de `collision_box`. Los TSV reproducibles se guardan localmente bajo `artifacts/kernel/` y no se versionan.

Siguiente: mapear límites de función y condiciones que alcanzan los sitios de Remilia, relacionarlos con action/sequence y contrastarlos con las duraciones y daño del PAT. Si el callback es alcanzable en 412, ejecutar su contrato en el harness x86 antes de portarlo; si no, continuar el seguimiento del productor del descriptor 412. Añadí `0x4649b0` y `0x47b1d0` a `ExportKernel.java`. Sin cambio de runtime/VPK ni afirmación de paridad nueva.
