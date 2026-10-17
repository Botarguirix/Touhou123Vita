# Iteración 1.66: oracle dinámico del split de Suwako 808

## Resultado

El nuevo `tools/x86_suwako_808_object_oracle.py` ejecuta el dispatcher original `007876d0` y la rama real del update de acción `0x328` en `th123.exe` 1.10a, con SHA-256 fijado `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. El oracle reemplaza por stubs controlados el suelo, RNG, probe de colisión, servicio de animación/audio y fábrica de objetos; el bytecode x86 decide la ruta, actualiza al padre, genera parámetros y emite las llamadas de creación capturadas.

Con X/Y `(300,400)`, facing `1`, suelo simulado `500`, colisión despejada y retornos de RNG `[10,2,20,4]`, la ejecución original emite dos objetos `0x328`, ambos en `(300,400)`, flags `3`, y custom data float `[-20,12,1]` y `[-30,14,1]`. El initializer pasa los dos primeros floats al transformador `00438c00` como ángulo y magnitud. Los helpers `004095f0/00409580` usan una tabla de seno a resolución de 0.1 grados; `00438c00` calcula `sin(ángulo)*magnitud` en `object+0xf4` y `cos(ángulo)*magnitud` en `object+0xf8` (el setter recibe `ECX=objeto+4`). En facing 1, `[-20,12]` produce `vx≈-4.104`, `vy≈11.276`; `[-30,14]` produce `vx≈-7.000`, `vy≈12.124`. El padre termina con latch `+0x36c=1`; `vy=-0.2`. Los límites RNG capturados en orden son `[160,6,160,6]`.

Se corrige explícitamente la interpretación de Iteración 1.65: los deltas `0.075` de seq0 y `0.005` de seq1 se suman al escalar auxiliar `object+0x11c` que también se publica en `+0x120`; no son aceleración vertical. En ambas rutas la actualización observada resta `0.2` a `vy`.

Casos negativos dinámicos: suelo simulado `300` con padre Y=`400`, probe de colisión positivo y latch previamente puesto a `1` producen cero hijos. El caso con latch conserva `vx=vy=0` después del branch.

Un quinto caso ejecuta el handler original directamente en secuencia 1 con un `vx=-4.10424` controlado y subframe 8. El update mueve X de `300` a `295.89575`, avanza Y de `400` a `399.8` tras restar `0.2` a `vy`, y no crea hijos. Esto demuestra el consumidor horizontal `object+0xf4` de la rutina común; el estado inicial se inyectó, no se afirma todavía que el argumento 1 de las llamadas factory sea el selector de secuencia.

## Verificación y alcance

- `tests/test_suwako_808_object_oracle.py`: 6 casos pasan, incluyendo constructor real con trigonometría controlada y un tick radial.
- `tests/test_object_motion_analysis.py`: la auditoría estática fija tablas, bytes y constantes.
- Los resultados de referencia se guardan en `artifacts/x86-suwako-808-update.json` y tres reportes de guards negativos. Son entradas controladas; no afirman que los valores RNG/floor elegidos correspondan a una escena natural.
- No se ejecuta la fábrica real ni su callback de carga. El constructor base y el initializer de acción 808 sí corren desde el PE: con custom data `[-20,12,1]`, escriben `vx≈-4.10424` en `objeto+0xf4` y `vy≈11.27631` en `objeto+0xf8`. Los helpers x86 de seno reciben resultados calculados con `math.sin` como servicio controlado; el resto de la inicialización/aritmética es original. Un shim del harness repara únicamente el marco de retorno sintético al epílogo del dispatcher. Luego se ejecuta un tick original seq.1/subframe 8: `(300,400)` pasa a `(295.89575,411.0763)` y `vy≈11.07631` tras gravedad. Se suministra seq.1 explícitamente; aún no se demuestra que el arg4=1 de factory seleccione esa secuencia ni las mecánicas de daño, vida o salida.

## Siguiente paso

Seguir la evolución temporal completa y resolver qué significa el cuarto argumento de la llamada factory frente al estado `+0x13e`; ejecutar constructor/update/animación/colisión de los hijos hasta la salida. Después comparar una traza del juego PC bajo la misma posición/escenario y portar la máquina 808 a C. Mantener el runtime actual (`vx=4`, vida 90) marcado provisional hasta completar ese diferencial; no publicar VPK de esta iteración porque no cambió el binario de combate.
