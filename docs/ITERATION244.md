# Iteración 2.144: update x86 de KeyInput alimenta el guard 418

Se encadenaron los productores originales `0x46c8e0` y `0x46d5d0` con el bloque de decisión `0x4b0ac2`. Con `KeymapManager.input.horizontalAxis=1`, el primer update escribe el KeyInput actual `[1,0]`, genera sample `0x02` y la ruta solicita acción 418. Con horizontal=1 y A=1, el update además copia `[1,0]` a `bufferedKeyInput`, deja el contador `+0x7ac=9`, genera sample `0x12` y la ruta solicita 418 a través del input buffered. El limpiador original `0x46cac0` borra ese snapshot luego de la transición.

El runner `tools/x86_suika_418_producer_probe.py --dynamic` ahora informa diez casos: ocho variaciones del guard y dos cadenas desde el KeymapManager hasta el action producer. Las diez pasan; la regresión fija los samples, los dos KeyInput y la limpieza buffered. Artefacto: [x86-suika-418-producer.json](../artifacts/x86-suika-418-producer.json).

Alcance: `0x46c8e0`, `0x46d5d0`, `0x4b0ac2` y `0x46cac0` corren como código original. Se usan estado de KeymapManager sintético y se aíslan el refresco físico `updateInput`, la inserción del ring/matcher `checkAllMotionInputs`, la consulta grounded/move-lock y el cuerpo del setter. Esto demuestra el mapeo input→KeyInput/sample y que esos valores satisfacen el guard; aún no demuestra doble toque/matcher real, setter virtual Suika→PAT, update natural 418 ni combate en replay. No cambia Vita runtime/VPK.

Siguiente: ejecutar `0x487020` con el ring real de 90 muestras; entonces encadenar el slot vtable de Suika `handleInputs`/`setAction`, el updater del personaje y el timeline PAT en una misma fixture reproducible.
