# Iteración 1.95: action 412 cae fuera de las ramas del update común

Se volvió a desensamblar el PE fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`, esta vez siguiendo el update de personaje `0x5879a0` y la rutina genérica `0x483f40`.

En `0x5879a0`, el flujo por action compara el id con `0xE2` (226): ids hasta ese límite usan una tabla de clases en `0x59a044` y un jump table en `0x599fb8`; ids mayores saltan al tail `0x599dfc`, que llama a `0x483f40`. Action 412 (`0x19c`) toma esta última ruta. En `0x483f40`, el switch cubre ids desde `0x32` hasta `0xB5` (50–181); 412 queda fuera del rango y cae en el epílogo por defecto `0x484be3`. El tramo común del update tampoco contiene una comparación directa contra 412 ni una llamada directa a los callbacks `0x4649b0` observados en secuencias 2/3.

Conclusión limitada: el dispatcher común de movimiento no contiene una rama específica para 412 ni explica por sí solo el daño PAT 750. Es evidencia estática; no demuestra que ningún virtual, objeto secundario, rutina compartida o manager aplique ese daño. Las exportaciones reproducibles están en `artifacts/kernel/remilia-update-full.tsv`, `remilia-update-dispatch-tail.tsv`, `remilia-generic-action-update.tsv` y `remilia-generic-action-default.tsv` (artefactos ignorados, porque derivan del ejecutable comercial).

Siguiente: volver al initializer 412 (`0x59ad64`) y a su consumidor de move lock; ejecutar el camino de setup/update con la menor cantidad de servicios stub posible para detectar vtable/callbacks y creación de objetos en runtime. Mientras la fuente del daño no esté probada, no añadir una hitbox inventada al port. Sin cambio de runtime o VPK en esta iteración.
