# Recuperación de animación original

El kernel portable de `src/animation.c` se reconstruyó del control de poses/secuencias del ejecutable original. No es una temporización inventada para hacer que el sprite parezca moverse.

| Función | Ver1.10a | Ver1.01 |
|---|---|---|
| Avanzar un frame | `0x438c60` | `0x437d50` |
| Siguiente pose | `0x464b70` | `0x463b30` |
| Establecer pose | `0x464b50` | `0x463b10` |
| Siguiente secuencia | `0x464bf0` | `0x463bb0` |
| Refrescar frame | `0x464ae0` | `0x463aa0` |

El contador global incrementa como uint32; el contador de pose incrementa como uint16 y compara como int16 con la duración. Al terminar una pose se recarga su duración. Las secuencias no cíclicas avanzan y devuelven la terminación de la acción al regresar a la primera secuencia.

`tools/x86_animation_oracle.py` ejecuta código PE32 original en Unicorn con estado sintético. Conserva los bytes de las funciones originales; intercepta solamente el refresco de gráficos después de seleccionar el frame, que queda fuera del contrato. Compara resultado, secuencia, pose, duración y contadores con la implementación C. Incluye overflow de contadores y límites de duración.

Se probaron 2048 casos en cada referencia: 4096 comparaciones sin diferencias. Las referencias están protegidas por SHA256:

- 1.10a: `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.
- 1.01: `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`.

Esto valida el kernel de animación; no valida la máquina de estados completa de Reimu/Cirno, física, input buffering, cancelaciones o combate completo. El control de acción y física de la arena siguen siendo provisionales.

Las constantes de caminar de Reimu en 1.10a se identificaron como ±4.5, y se exportaron funciones de inicialización, inputs y física a evidencia local con Ghidra. Su adaptación completa todavía no está integrada; no se debe afirmar que caminar/saltar ya coincide con PC.

## Punto de continuación: movimiento y estados

La referencia 1.01 está disponible en `F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe` (4,583,424 bytes; SHA256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`). Coincide con el hash registrado arriba. La copia `original/th123.exe` es 1.10a; no intercambiar direcciones entre ambas.

Para 1.10a, `artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/` ya contiene los pseudocódigos de los métodos de acciones/estado de Reimu (`004ac670`, `004ae670`) y Cirno (`006fa260`, `006fb8b0`), además de la actualización compartida por frame (`00487ef0`). Las tablas virtuales están en `manifest.tsv`; los cuatro métodos de personaje se ejecutan desde sus vtables y varios despachan acciones por ID. Esto explica por qué las constantes aisladas no bastan para sustituir `data_act`: hace falta mapear el estado y la ruta de entrada que selecciona cada acción.

### Refinamiento del despacho B/C

La etiqueta pública de SokuLib para `0x487ba0` es `Player::useSkill(int id, short action)`: no es el despachador general de ataques normales. Los puntos comunes de input documentados son `handleGroundBE` (`0x487990`), `handleAirBE` (`0x487ab0`) y `checkAllMotionInputs`. Las llamadas a `0x487ba0` desde `004ae670`/`006fb8b0` deben interpretarse como uso de habilidades. Fuente: [SokuLib Player.hpp](https://github.com/SokuDev/SokuLib/blob/master/src/Player.hpp).

El enum de acciones identifica `408 = ACTION_66B` y `418 = ACTION_66C`; `400–407` son otros B y `410–417` otros C. El catálogo PAT local confirma poses dañinas para Reimu en 408 índice 1 y 418 índice 0, y para Cirno en 408 índice 1 y 418 índice 0. Los handlers seleccionan esas acciones desde dash frontal `200`; falta recuperar el doble toque y sus cancelaciones completas. Fuente: [SokuLib CharacterManager.hpp, revisión fijada](https://github.com/SokuDev/SokuLib/blob/51486a0c400201313f6afff1155e8f84bbb9d809/src/Core/CharacterManager.hpp#L2068-L2101).

#### Evidencia sobre move locks y handlers de input (1.10a)

- `00489610(action)` es `Player::getMoveLock(unsigned short action)` según la definición pública de SokuLib. En el binario 1.10a consulta el árbol/mapa del objeto en `this+0x160` mediante `0043f2f0` y devuelve el valor de move lock para esa acción. Por tanto, esos resultados describen la disponibilidad/cancelabilidad de acciones, no la antigüedad de inputs.
- `00489e90` es `handleHJInput(moveLock, hjCancelable)`: consulta locks para acciones `0xD0`, `0xD1`, `0xD2` y puede despachar esos mismos IDs según campos `0x1d5`, `0x1d6`, orientación `0x41`, banderas `0x1f1`, estado `0x4f` y contador `0x1da`.
- `0048a220` (`handleGroundDash`) consulta locks `0xC8`/`0xC9`; `0048a380` (`handleFwdAirDash`) consulta `0xCA`; `0048a470` (`handleBackAirDash`) consulta `0xCB`; `0048a560` (`handleNormalFlight`) consulta `0xD6` y elige según dirección vertical/horizontal.
- `00487990` (ground BE) exige flag `0x20`, filtra un subestado byte en `+0x80e`, y solo actúa en una banda de estados que empieza en `0x96` y se divide en `0x9e`; produce `0xDC`–`0xE0` y, en un caso, una llamada adicional de skill. `00487ab0` (air BE) exige estado `0x9e` y produce `0xE1`/`0xE2` según orientación. Esos valores `0x96`/`0x9e` son comparaciones del campo de estado `0x4f`, no se etiquetan como carga.
- Los pseudocódigos están en `artifacts/kernel/<sha>/00489610.c`, `00489e90.c`, `0048a220.c`, `0048a380.c`, `0048a470.c`, `0048a560.c`, `00487990.c` y `00487ab0.c`. La inspección Capstone confirma que `0043f2f0` implementa una búsqueda de árbol/mapa; el barrido x86 encontró los callers candidatos en `artifacts/move-lock-callers.tsv`.

La inspección de instrucciones x86 confirma la consulta: `00489610` pasa el árbol/mapa situado en `this+0x160` y un ID de acción de 16 bits a `0043f2f0`; después lee el valor asociado al nodo. SokuLib identifica la rutina como `Player::getMoveLock(unsigned short action)` ([Player.hpp](https://github.com/SokuDev/SokuLib/blob/master/src/Player.hpp#L1241)). El constructor inicializa el miembro en `00411714–0041171f` y el destructor recorre y elimina sus nodos en `00411760–004117c1`. Llamadas reales a la búsqueda desde métodos vecinos aparecen en `00483aa2` y `00483b85`. Capstone halló 32 candidatos de llamada a `0043f2f0` y 1,299 a `00489610`; como el barrido lineal puede atravesar regiones de datos/código mixtas, esos totales no son un conteo auditado de callers. El TSV conserva bytes y desensamblado para confirmar cada dirección en Ghidra.

La corrección cambia el siguiente paso: `00489610` consulta move locks y no un historial de input. Los handlers `handleInputs`/`checkAllMotionInputs` ya permitieron identificar las rutas `408` (`66B`) y `418` (`66C`) desde el dash frontal `200`. Falta reconstruir cómo el doble toque produce ese estado, en qué ventanas de cancelación se permite B/C y cómo los move locks afectan cada personaje. Los IDs `C8–D6` usados por helpers de movimiento no deben confundirse con botones físicos.

La tabla virtual de Reimu/Cirno asigna el slot 20 a `004ae670`/`006fb8b0` (`handleInputs`) y el slot 21 compartido a `00487020` (`checkAllMotionInputs`), consistente con la interfaz [SokuLib Player.hpp](https://github.com/SokuDev/SokuLib/blob/master/src/Player.hpp#L1216-L1218). El desensamblado de `00487020` lee secuencias configuradas como `NRNR`, `NLNL`, `DD`, `N07`–`N09`, `4136X`, `236X`, `623X`, `412X`, `214X` y `421X` mediante `0046cc90`, y arma bitmasks en `this+0x7c4`/`+0x7c8`. SokuLib documenta `keyUpA/B/C` en `0x794`–`0x79c` ([Player.hpp](https://github.com/SokuDev/SokuLib/blob/master/src/Player.hpp#L1071)); los bloques B/C en los handlers acceden a `this+0x798`/`+0x79c`.

El detalle de la ventana está en `004ae670.c` (Reimu) y `006fb8b0.c` (Cirno): el handler requiere estado 200 y dirección hacia delante, y compara el frame actual con `getMoveLock(0x198/0x1a2)`; permite la transición cuando `frame <= moveLock`. `00489610` consulta la tabla de locks por ID de acción, cuyos valores destino aparecen en el PAT. La iteración 1.25 implementa esta regla para 408/418 y verifica el límite inclusivo y un frame posterior. El selector de variantes basado en puntuación de hitboxes permanece heurístico. Ver [ITERATION29.md](ITERATION29.md).

Para ambos personajes, los handlers seleccionan `408` (`0x198`, 66B) y `418` (`0x1a2`, 66C) desde el estado de dash frontal `200`, con movimiento hacia el frente y el `moveLock` de esa acción. El PAT local confirma que Reimu y Cirno necesitan `408:index 1` (la variante 0 no tiene caja dañina) y `418:index 0`. La iteración 1.17 impide seleccionar 408/418 desde neutral y modela el doble toque que crea la acción 200. El desensamblado recupera una ventana de historia de 15 ticks para `NRNR`/`NLNL`; el lock temporal y la semántica completa de cancelación siguen aproximados. La corrida Vita3K valida la ruta y los límites de 15/16 ticks, no la paridad completa de input. Ver [INPUT_STATE.md](INPUT_STATE.md) y [ITERATION17.md](ITERATION17.md).

La evidencia actual confirma los recursos PAT y el daño de `408:index 1` y `418:index 0` en Reimu/Cirno bajo la prueba simplificada. El gate local ya usa el matcher `NRNR`/`NLNL`, conserva 90 muestras, pasa 401 comparaciones x86/ARM y rechaza una secuencia fuera del historial; el probe fresco de Vita3K también pasó. Aún falta capturar el productor real, confirmar todos los bindings, mapear move locks/cancelaciones y contrastar por frame la ruta dinámica por personaje. El caller TSV es una lista de candidatos estáticos y debe confirmarse en Ghidra antes de asignar semántica a direcciones adicionales.

### Siguiente ciclo verificable

1. Enfocar una versión a la vez, empezando por 1.10a, y documentar los campos de posición/velocidad, orientación, estado de acción, contadores de input y bloqueo que lee/escribe `00487ef0`, `004ac670` y `006fa260`.
2. Seguir los callers de `00487ef0` y los lectores/escritores de esos campos en Ghidra para localizar el paso de física y la selección de estado de caminar/salto. Exportar solo las funciones nuevas y anotar direcciones junto con el SHA del EXE.
3. Crear una traza PC reproducible para Reimu y Cirno con posición, velocidad, acción y pose por frame ante secuencias fijas: quieto, caminar, cambiar dirección, saltar y aterrizar. La referencia debe registrar también versión, lado y estado inicial.
4. Implementar el primer contrato portable solo cuando esas trazas revelen reglas y límites suficientes; comparar la primera diferencia por frame antes de integrar cambios en la demo.

No se requiere documentación adicional del usuario para continuar el análisis estático. Una vez que toque validar comportamiento dinámico, la evidencia que más ayudará será una traza de frames o una grabación/replay de entradas de la instalación PC; si no está disponible, primero se construirá el extractor/oráculo local a partir del ejecutable original proporcionado.
