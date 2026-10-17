# Iteración 1.63: acotar el origen de offsets del descriptor PAT

Seguí el selector de pose hasta `00464ae0` (iteración 1.62) y revisé el pseudocódigo Ghidra del parser de secuencias/poses `004679e0`, guardado en `artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/resource-loader/004679e0.c`.

El parser consume el registro PAT por campos y llena directamente miembros y contenedores del descriptor de 168 bytes. En el pseudocódigo exportado no aparecen escrituras directas a descriptor `+0x98` ni `+0x9c`; las escrituras explícitas que pude seguir alcanzan estructuras hasta `+0x80`, incluidos arreglos de cajas dinámicos. Esto no prueba que los dos campos queden a cero: el constructor, callbacks indirectos o un procesamiento posterior aún podrían asignarlos.

Separé además coincidencias falsas del barrido global: `004432b0` aparece como constructor de arreglos con stride `0xa8` en varios sitios, pero el export `00450880.c` muestra uno de esos usos dentro de `CProfileDeckEdit`, una clase de menú, no el loader PAT. El stride compartido no basta para asignar ese constructor al descriptor de pose. La inicialización específica del arreglo PAT sigue sin localizarse.

La procedencia conocida queda así: PAT → parser `004679e0` → lista de frames `Player+0x15c` → selector `00464ae0` → descriptor actual `Player+0x158` → spawn de 808 lee `+0x98/+0x9c`. Falta una prueba de escritura de esos dos miembros dentro del flujo de carga, o evidencia de que el descriptor mantiene sus valores iniciales. No se cambiaron posiciones del runtime.

## Siguiente paso

Auditar el constructor/zeroing y los helpers/callbacks que el parser invoca al completar el descriptor, buscando específicamente escrituras a offsets `+0x98/+0x9c` con el objeto descriptor como destino. Si son constantes inicializadas, entonces medir esos valores para pose 418; si provienen de otra fuente, rastrear esa rama.
