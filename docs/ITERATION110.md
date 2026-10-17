# Iteración 2.10: hijo 801 y umbral hit-vs-hurt original

La probe de Remilia 412 ahora reutiliza el objeto 801/seq.0 creado por la factory original `0x784020`, sincroniza sus cajas desde PAT con `0x465e10` y alimenta ese hijo al helper original `0x47a5b0`. El defensor se prepara desde el PAT neutral de Remilia, acción 0, con una hurtbox; las transformaciones de cajas de `0x4640b0/0x464200` corren desde el PE. El proceso del terreno/orientación sigue controlado y no se ejecuta la fase de pares completa del manager.

Con centros alineados en Y y posiciones X separadas 0, 40, 60, 70, 71, 100 y 200, el helper devuelve contacto para 0/40/60 y ninguno desde 70. Esto establece un límite geométrico abierto: solapamiento sí, mero toque de bordes no. El hijo real sigue teniendo action 801, seq.0, 20 poses y 1 hitbox PAT; su dispatcher original corrió 60 ticks sin error en la misma corrida.

La prueba no ejecuta el callback indexado de Remilia, el loop de pares del manager, bloqueo/guardia, respuesta posterior ni aplicación de daño. No demuestra el daño de 120 por impacto ni la ruta del daño PAT 750 del action 412. Siguiente: conectar el update de objetos al phase dispatch del manager (`0x47cb70/0x47ce20`) y seguir el primer contacto hacia el handler de respuesta/daño.

Regresión añadida: factory 801, hitbox sincronizada y matriz de siete distancias. Sin cambio del runtime Vita o VPK.
