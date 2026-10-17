# Iteración 1.78: consumidor del campo de terminación de Suwako 808

## Contrato del manager

El EXE de referencia fija la vtable del manager en `0x85f28c`. Su slot4 apunta a `0x633ce0`: comprueba la condición de pausa del oponente y, si permite avanzar, invoca `0x633c10` sobre la lista con callback `0x4ae380`. El callback común ejecuta el método virtual del GameObject en `vtable+0x28` (el dispatcher de acción `0x7876d0`) y luego la lista lee `object+0x34c`.

Si el campo sigue distinto de cero, conserva el nodo y pasa al siguiente. Si vale cero, obtiene el handle de `object+0x350`, lo remueve del registro generacional mediante `0x45ed10`, desenlaza y libera el nodo, y resta uno al tamaño de la lista. Esto confirma que el decremento al final del fade 808 es una señal para que el manager retire el objeto. No equivale a HP/vida temporal, ni significa que el manager haya sido ejecutado por el probe anterior.

El analizador `tools/analyze_object_motion.py` valida la vtable, wrapper, callback, comparación del campo y llamada de retiro con firmas del PE fijado. La prueba de `tests/test_object_motion_analysis.py` exige que se mantenga ese contrato.

## Límite dinámico y siguiente gate

Se intentó incorporar el manager completo al harness. Su constructor reserva el pool de 256 entradas; bajo los servicios controlados el constructor vuelve correctamente, pero combinarlo con el factory requiere preservar el layout/handles reales de la lista. Un fixture manual con offsets desplazados cae a la ruta de excepción y produce nodos inválidos si se sigue iterando, por eso se descartó como evidencia. No se modificó el runtime Vita ni se generó otro VPK; el baseline de Iteración 1.77 permanece válido.

Próximo paso: modelar los servicios externos estrictamente observados en constructor/allocator, comprobar el sentinel, pool y mapa de handles, ejecutar un factory 808 en la lista real y llamar slot4 por tick. Criterio: en el tick que el objeto pone `+0x34c` en cero, manager reduce la lista a cero y elimina el handle sin otra invocación manual del dispatcher. Luego seguir la fuente de bounds/cajas de seq.1 y su ruta de impacto antes de portar daño.
