# Iteración 1.79: frontera terminal del probe 808 y gate del owner

## Probe de actualización

El probe del factory/dispatcher deja de llamar al update cuando observa `object+0x34c==0`, que coincide con el consumidor ya localizado en el manager. Corrida fresca del PE fijado y PAT local con `--ticks 40`: el dispatcher termina tras 32 callbacks; al último, alpha es 7, `+0x34c` es 0 y EAX es 7. Ya no se provocan callbacks artificiales que subdesbordan el campo. El reporte mantiene `manager_removed_object: null`: esta prueba todavía no ha ejecutado la lista del manager ni demuestra baja dinámica del handle.

## Reclasificación del helper `0x48ce90`

La lectura del cuerpo completo corrige el nombre previo de “colisión”: el helper lee el action del owner a través de `object+0x364`, verifica un rango de estados y, si coincide, crea objetos auxiliares `0xc8` y `0xc9` según sus contadores; después devuelve true. La llamada de la secuencia 0 del action 808 pasa `[0,0,3]`, así que el action del owner en `0x32..0x95` puede generar tres efectos `0xc9` y suprimir el split. La consulta de suelo es otro helper: `0x4397f0`. Ninguno de estos dos datos resuelve por sí solo la hitbox de seq.1.

El analizador valida vtable/rango del owner, IDs de efectos y argumentos de 808 con bytes del EXE. Se actualizó la prueba de análisis y también el probe de objeto para exigir parada en cero. Suite Python: 37/37. `git diff --check` limpio. No cambia el runtime Vita, por lo que no se recompila VPK.

## Siguiente gate

Resolver la integración pool/handles/lista para llamar al slot4 del manager con una instancia legítima y observar el unlink al mismo tick terminal. El intento anterior de factory bajo manager completo cayó en excepción por estado de fixture y no cuenta como resultado. Después localizar la ruta de bounds e impacto de los hijos 808, especialmente seq.1, antes de modificar el combate Vita.
