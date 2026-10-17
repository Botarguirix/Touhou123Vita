# Iteración 1.72: límites reales del constructor de Suwako 808

## Evidencia confirmada

- El factory de la lista `0x784020` llama al gestor `0x783de0`; éste obtiene una ranura de `0x783ba0`, copia `customData` a `object+0x35c` y despacha `setAction` mediante vtable.
- El constructor de objeto `0x783a70` llama a `0x4adcc0`, inicializa sus listas y devuelve con la vtable base `0x85f1d4`; la factory instala después la vtable derivada `0x85f22c`. El constructor base pone `object+0x350=0`, `+0x34c=1`, `+0x35c=0`, `+0x354=0`, `+0x360/+0x362=0`, HP `+0x184/+0x186=0`. En la corrida real del constructor sí aparece `RenderInfo.color=0xffffffff`: la escritura es transitiva en la construcción del sprite (`0x438bb0`), llamada desde la cadena de constructores (`4adcc0→46b7f0→4232f0`). El constructor directo `783a70` no escribe esos offsets por sí solo.
- `setAction` (`0x464930`) llama `0x438ca0` para asignar el action id y después el virtual `initializeAction` (`0x799000`). Éste invoca `setSequence` (`0x4652a0`) mediante vtable. El setter busca action en el `Map` de `object+0x160` y recorre los nodos de secuencia; `+0x13e` es el índice PAT seleccionado. Por tanto, la entrada anterior del oracle que escribió directamente `+0x13e` omitía esta cadena de selección.
- El initializer `0x799000` para action 808 y seq.1 ejecuta la transformación radial de `customData[0:2]`, selecciona el PAT de la acción y asigna campos adicionales. No se encontró escritura a los cuatro bytes de color `+0x110..+0x113` en el initializer de acción ni en `setSequence/setPose`; la cadena transitiva del constructor del sprite sí fija `0xffffffff`. El byte `+0x113` sí se lee y decrementa en el update seq.1 (`0x788d3e`).
- El recurso PAT local declara action 808 seq.0 como 10 frames dañinos de 100 y seq.1 como un frame dañino de 150. El split produce `customData[2]=1`, que selecciona seq.1.

## Límite y siguiente experimento

El factory completo sigue pendiente porque `0x783ba0` requiere las estructuras de lista y handles. La corrida de ctor aislado ya no depende de una suposición sobre el color: ejecuta `0x783a70` con el allocator de nodos cdecl controlado y luego `setAction→initializeAction→setSequence` con un mapa PAT sintético. Mantener separado el contenido de ranuras y la gestión del manager, pero la construcción del sprite original sí establece alpha 255.

La trayectoria con alpha 255 queda como escenario de sensibilidad del harness, no pronóstico natural. No integrar aún 808 en el motor Vita ni producir un VPK por esta investigación. La evaluación de reutilización del proyecto TH075 está en [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md).

## Corrida adicional: cadena real de acción sobre mapa PAT mínimo

Se agregó `tools/x86_suwako_808_action_probe.py`. Ejecuta desde el PE la cadena original `setAction(808) → reset/setSequence → setPose → initializeAction(0x799000) → setSequence(1) → setPose`, usando el vtable auténtico de Suwako y un árbol de mapa/vector con dos secuencias. Ejecuta el lookup/dispatch/aritmética x86; sólo PAT (dos nodos con las cardinalidades/duraciones observadas), almacenamiento del objeto, trigonometría, RNG y callback gráfico son controlados.

Resultado fijado en `artifacts/x86-suwako-808-action-probe.json`: la acción queda 808, `+0x13e=1`, `currentSequence` apunta al nodo seq.1, el frame seleccionado es el nodo de pose 0 y la velocidad radial queda `(-4.1042418, 11.2763119)`. La cadena visita poses de seq.0 y seq.1 y no escribe el color. Una prueba de centinela `0xA1B2C3D4` conserva byte por byte `RenderInfo.color` y alpha `0xA1`; en almacenamiento inicialmente cero queda alpha 0. Esto confirma que ni el initializer ni `setSequence/setPose` fijan el alfa.

El ctor se ejecuta sobre storage de objeto provisionado en cero y se observan dos asignaciones cdecl de 12 bytes para nodos internos. El color blanco se establece por la ruta original de construcción del sprite; la fábrica/gestor de handles aún no se han ejecutado. La prueba conserva además un centinela no blanco antes de `setAction` y demuestra que los setters/initializer lo preservan. Las nuevas pruebas de contrato son `tests/test_suwako_808_action_probe.py`; no cambió el runtime Vita.
