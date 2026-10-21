# Input buffer reconstruido desde 1.10a

Referencia fijada: `original/th123.exe`, SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.

`00487020` limpia los bitmasks en `this+0x7c4` y `this+0x7c8`, y consulta patrones con `0046cc90`. Para cada patrón pasa el límite de historial, la longitud y el puntero al texto. El primer parámetro acota los índices examinados en el búfer circular de inputs; el patrón NRNR y NLNL se evalúa sobre un historial de 15 ticks y 4 símbolos. Los bits 0 y 1 de `this+0x7c4` se activan respectivamente para NRNR y NLNL. `0048a220` los interpreta según `face`, de modo que el patrón correspondiente a derecha/izquierda se convierte en dash frontal/reverso.

| Patrón | Máximo historial | Símbolos | Salida de `00487020` |
|---|---:|---:|---|
| NRNR | 15 | 4 | `0x7c4 |= 0x01` |
| NLNL | 15 | 4 | `0x7c4 |= 0x02` |
| N09 | 20 | 3 | `0x7c4 |= 0x10` |
| N07 | 20 | 3 | `0x7c4 |= 0x08` |
| N08 | 20 | 3 | `0x7c4 |= 0x04` |
| DD | 15 | 2 | `0x7c4 |= 0x20` |
| 421X | 15 | 4 | `0x7c8 |= 0x1000 << (match-1)` |
| 214X | 15 | 4 | `0x7c8 |= 0x10 << (match-1)` |
| 412X | 15 | 4 | `0x7c8 |= 0x10000 << (match-1)` |
| 623X | 15 | 4 | `0x7c8 |= 0x100 << (match-1)` |
| 236X | 15 | 4 | `0x7c8 |= 1 << (match-1)` |
| 4136X | 20 | 5 | `0x7c8 |= 0x100000 << (match-1)` |
| 6314X | 20 | 5 | `0x7c8 |= 0x1000000 << (match-1)` |
| 2N2X | 15 | 4 | `0x7c8 |= 0x10000000 << (match-1)` |

La traducción y comparación se inspeccionaron en el desensamblado completo de `0046cc90` (960 bytes hasta el comienzo de la siguiente función; dump local bajo `artifacts/kernel/<sha>/input-state/0046cc90.capstone.txt`). La rutina recibe el patrón, su longitud y el límite de historial; toma el índice actual desde `this+0x7bc`, recorre la historia circular asociada a `this+0x7b0` y coteja símbolos traducidos contra muestras empaquetadas. El selector `this+0x104` es el byte `Direction` heredado de `AnimationObject`, no un ajuste desconocido: el layout lo fija en `0x104` después de posición/velocidad/gravedad ([SokuLib AnimationObject.hpp](https://github.com/SokuDev/SokuLib/blob/master/src/AnimationObject.hpp#L17-L25)). El signo de esa dirección elige la tabla `0x883b08` o `0x883adc`. En la primera, por ejemplo, `N/R/L/D` se traducen a `0/2/1/0x80`, `4/6` a `1/2`, `A/B/C` a `0x10/0x20/0x40` y `X` a `0xf0`; la segunda invierte la numeración relativa de diagonales y 4/6. El layout de `Player` confirma el deque en `0x7b0` y los campos de movimiento/comando en `0x7c4`/`0x7c8` ([SokuLib Player.hpp](https://github.com/SokuDev/SokuLib/blob/master/src/Player.hpp#L124-L141)).

El desensamblado confirma que `0046cc90` compara muestras de estado empaquetadas y maneja direcciones, botones y comodines. `src/input.c` implementa el buffer de 90 muestras y el matcher que ahora alimenta el gate de dash de combate. La traducción de dirección, el ring y los comandos base se contrastaron contra el x86; falta validar la captura real de controles contra el productor `0046d5d0` y replays. Esta paridad del helper no implica paridad de todo el motor.

### Productor y layout del ring

El barrido de referencias al PE fijado localizó inicialización del objeto en `0046c43d–0046c455`, uso en `0046cc90` y el update de entrada en `0046d5d0`, que agrega la muestra desde `0046d78f`. `0042cf90` agrega una muestra de 16 bits al ring: toma el índice `[+0x0c] + [+0x10]`, escribe el word y aumenta `+0x10`. Cada bloque de datos reserva `0x10` bytes y contiene 8 muestras consecutivas de 16 bits; `+0x04` apunta al arreglo de bloques, `+0x08` cuenta bloques, `+0x0c` es el inicio/índice circular y `+0x10` la cantidad que el matcher considera disponible. Estas interpretaciones se basan en aritmética de índices, tamaño de asignación y acceso indexado observados en `0042cf90`/`0042c920`.

En `0046d5d0–0046d69b` el update del jugador empaqueta botones y ejes en un word antes de pasarlo al ring. Tras el append, `0046d79d–0046d7bd` avanza el inicio, envuelve por `bloques*8` y reduce la cantidad, conservando N muestras y expulsando la más antigua. La inicialización en `0046ba29` llama a `0046d950`, que empaqueta el byte bajo actual desde `+0x754..+0x768` y pide a `0046d890` reconfigurar la cola con 90 (0x5a) copias; la misma función se llama antes de varias transiciones. El byte bajo contiene A/B/C/D en los bits altos (`0x10/20/40/80`) y los cuatro signos de los ejes vertical/horizontal en los bits bajos; `0046d5d0` agrega change-card/spellcard en bits 8/9. `0046d890` borra el rango mediante `0042bc40` y delega la inserción por cantidad a `0046d050`. Así se explica el tamaño 90 durante el combate y la parte principal del formato. Evidencia: [ITERATION23.md](ITERATION23.md) y `artifacts/kernel/<sha>/input-state/player-input-window-seed.capstone.txt`. Faltan neutral/diagonales/orientación, las rutas de transición y la semántica completa de las ramas de `0046cc90`. El gate Vita es aún aproximado. `0046d939` es interno del editor de rango, no un caller externo. Los barridos lineales aportan candidatos, no xrefs confirmados.

La captura reproducible de instrucciones de `00487020` está en `artifacts/kernel/<sha>/input-state/00487020.capstone.txt`. Se regenera con:

```powershell
python tools/find_pe_callers.py --exe original/th123.exe --output local/input-state-callers.tsv --quiet --window 00487020:1F1
```

La iteración 1.38 ejecutó bajo Unicorn `00487ba0` (`useSkill`) con el dispatcher virtual sustituido por un stub controlado: el argumento de acción llega a `setAction`, el bit `Player+0x4ad:0x08` se activa cuando el segundo argumento es `>=10`, se llama una vez al reinicializador de input y `Player+0x12c` queda a cero. Se ejecutó además el productor `0046d950` con `0046d890` interceptado después de capturar su capacidad y muestra; 144 combinaciones de ejes A/B/C/D coinciden con el empaque esperado y capacidad 90. Esto verifica el helper y el formato del seed, no la carga de cartas, el loop de llenado del historial ni la activación jugable de skills. Ver [ITERATION42.md](ITERATION42.md).

La iteración 1.13 usaba un borde temporal aproximado. La iteración 1.23 reemplaza el empaque provisional por el formato observado en `0046d5d0`; el gate del dash sigue limitado al patrón NRNR/NLNL ya contrastado y no reproduce todas las reglas del combate original.

### Productor real de muestras: `0046d5d0`

El dump Capstone fijado en `artifacts/kernel/<sha>/input-state/player-input-update.capstone.txt` confirma las siguientes fuentes y bits del word de 16 bits, antes del append a `0042cf90`:

| Fuente en Player | Condición | Bit en muestra |
|---|---|---:|
| `+0x754` (eje horizontal) | positivo / negativo | derecha `0x02` / izquierda `0x01` |
| `+0x758` (eje vertical) | positivo / negativo | abajo `0x08` / arriba `0x04` |
| `+0x75c`, `+0x760`, `+0x764`, `+0x768` | valor igual a 1 | A/B/C/D `0x10/0x20/0x40/0x80` |
| `+0x76c`, `+0x770` | valor igual a 1 | change-card/spellcard `0x100/0x200` |

El mismo productor mantiene flags buffered usados por handlers: `0x46d70f–0x46d744` escribe `+0x77c/+0x780/+0x784` a partir de comparaciones booleanas sobre `+0x75c/+0x760/+0x764`. En particular, `Player+0x784 = (Player+0x764 == 1)`, es decir, el control C actual. En la ruta de Suika action 200→418, `handleInputs 0x609dc0` consulta ese valor antes del dispatch; omitir C explica un retorno temprano aunque el historial NRNR se haya formado correctamente. La Iteración 2.150 confirmó el productor y el gate dinámicamente en un Player construido por el PE y el mismo deque original; la fuente física de controles continúa como fixture. Ver [ITERATION250.md](ITERATION250.md) y [reporte](../artifacts/x86-suika-constructed-handler.json).

`input_sample()` en `src/fight.c` ahora traduce los controles de la demo a ese formato. El probe ARM/Vita verifica `0x019` para izquierda+abajo+A y `0x3e6` para derecha+arriba+B+C+D+change-card+spellcard. Estas aserciones validan la traducción de la abstracción de controles; todavía no capturan los valores configurados del juego PC ni la neutralización exacta de ejes en runtime. La semántica del ring y el matcher se valida por separado contra el x86.

### Ejecución dinámica del helper original

La iteración 1.22 ejecuta el x86 y el C compilado para ARM en la misma suite: pasan 401 vectores, 17 contractuales y 384 secuencias generadas determinísticamente. El runner está en [test_input_arm_oracle.py](../tools/test_input_arm_oracle.py), y el resultado queda en `artifacts/x86-arm-input-vectors.json`. El gate de dash usa historial `NRNR`/`NLNL` de 15 muestras y pasó el probe integrado en Vita3K. Restan trazas del productor/replay y comparación del timing del movimiento contra una corrida PC.
