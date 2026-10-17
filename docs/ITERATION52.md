# Iteración 1.48: límite x86 de secuencias PAT en bucle

## Evidencia ejecutable

La vtable de Reimu, en `artifacts/kernel/<sha>/manifest.tsv`, asigna slot 5 a `00464BF0`, slot 8 a `00464B70`, slot 3 a `004652A0` y slot 16 a `00487EF0`. El slot 8 avanza el contador de pose `+0x140` módulo la cantidad `+0x148`, llama al actualizador de pose y solo devuelve verdadero cuando el contador vuelve a cero y el nodo PAT actual (`+0x15C`, campo `+0x14`) no tiene loop. En el loop retorna falso. Por tanto, el loop no puede por sí solo señalar su final ni disparar el siguiente nodo.

`00464BF0` es otra operación virtual: avanza al siguiente nodo enlazado en `+0x15C`, incrementa índice de secuencia `+0x13E`, recalcula cantidad de poses y llama al refresco gráfico virtual slot 7 (`+0x1C`). Devuelve verdadero cuando el nodo siguiente no tiene secuencia enlazada (`node+0x18 == 0`) y limpia el índice/contador. `004652A0` selecciona un índice explícito, sigue el enlace `node+0x1C`, calcula la cantidad y llama también a slot 7. Los tres métodos tienen contratos distintos; el valor de retorno de fin de secuencia no resuelve quién pide seleccionar seq. 3 desde el loop.

El oráculo Unicorn ejecuta `00464B70` contra nodos sintéticos con los tamaños reales de PAT seq. 2 (2 poses) y seq. 3 (3 poses). Ambos límites avanzan a pose 0 y reinician subframe; seq. 2 retorna 0 (sigue activa) y seq. 3 retorna 1 (fin). El callback `0043A250` de envío de pose a render está aislado con stub, pero la función de avance y su condición son bytes x86 originales. `artifacts/x86-skill-sequence-oracle.json` conserva estos casos.

## Update común y dispatcher de la acción 560

El puente de animación `00438C60` incrementa subframe `+0x142`; al alcanzar duración llama al slot 8 `nextPose` (`00464B70`). Solo si este retorna verdadero, llama al slot 5 `nextSequence` (`00464BF0`). Esta es la cadena automática que demuestra por qué seq. 2 loop no avanza por sí misma.

El slot 10 del Player es `00490490`, no el slot 16 de física (`00487EF0`). Este update compara `action +0x13C` con `0x230` y salta a `004A0639` para Reimu 560. Ese dispatcher lee el índice de secuencia `+0x13E`, procesa física/pose y llama `00438C60`. La rama llama `applyAirMechanics` (`00487EA0`); si retorna verdadero y el índice es menor que 3, transfiere a `0049295D`, que selecciona la secuencia 3 mediante el slot 3 (`004652A0`).

El contrato ejecutado de `00487EA0` compara la altura del jugador `+0xF0` con `getGroundHeight` (`004397F0`), requiere velocidad vertical `+0xF8 < 0` y el flag `+0x4C4 == 0`. Con PE x86 real y Unicorn, contacto en el plano o debajo mientras desciende solicita `setSequence(3)` desde action 560/seq. 2. En el aire, velocidad vertical cero o flag activo el gate devuelve falso. La transición es touchdown/contacto con suelo durante el descenso; no depende de pulsar un botón ni de que expire el loop PAT. La secuencia 3 es la recuperación (`dashStop`) no-loop de tres poses.

`004AC600` (slot 17) es un thunk de inicialización que salta a `0048B000`, y este último inicializa muchos campos. Un scan general de offsets `+0x190/+0x194` se descartó por demasiado ambiguo debido a su reutilización en otras clases.

## Conclusión y alcance

Queda probado que la transición ocurre al tocar el suelo durante el descenso. El sistema de input puede cancelar la acción por rutas independientes, pero no es el disparador necesario para seq. 3. El runtime Vita todavía debe portar esta regla con coordenadas/velocidad comparables y una prueba de touchdown en combate; después hay que reconstruir el resto de secuencias, cancelaciones y skills del roster.

La revisión de Touhou75Vita queda afinada: límites, archivado de evidencia y timeout ya están cubiertos por `tools/vita3k-test.ps1`; no hay que duplicarlos. No se copia runtime, renderer ni código del checkout TH075.

## Verificación

Los bytes corresponden al ejecutable original `th123.exe` con SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. El oráculo ejecuta `nextPose`, `setSequence`, `applyAirMechanics` y la rama de actualización action 560; el lookup PAT, `getGroundHeight`, callback físico no relacionado y envío gráfico se aíslan. Las pruebas de secuencia pasan 3/3 y la suite Python 19/19. Esto prueba la rutina y rama de referencia, no la paridad del combate Vita; no se reconstruyó VPK porque todavía no se portó la regla.
