# Iteración 2.11: fase de actualización del manager sobre el 801

La probe ejecuta la factory 801 desde el handler de Remilia 412 y después llama al slot de actualización del manager (`0x633ce0`), que recorre la lista con `0x633c10`, callback común `0x4ae380` y update virtual del objeto (`0x7876d0`). El hijo avanza desde pose0 hasta pose17 en 17 llamadas administradas completas. Esto valida que la factory enlaza una entrada que el iterador puede visitar y que el callback común alcanza el GameObject real.

La llamada 18 falla en `0x4ae3b7`: el iterador entrega `ESI=1`, que no es un GameObject, y el fetch de vtable produce lectura inválida. El hijo sigue con `+0x34c=1`; no se observó la ruta de retiro ni la liberación correcta. El estado lista/handle en el fixture/adaptador sigue siendo incompatible con el sentinel que el iterador espera después de estas visitas. Se conserva como fallo reproducible, no como lifecycle válido.

La prueba geométrica de `0x47a5b0` permanece: hijo PAT 801 contra hurtbox neutral PAT de Remilia contacta a distancias 0/40/60 y no desde 70. No se ejecuta la fase completa de pares `0x47cb70/0x47ce20`, resolución de guardia ni aplicación de daño.

Siguiente: instrumentar el nodo raíz/sentinel y allocator de `0x633c10`, comparar los punteros y handles antes/después de cada callback y reproducir la convención de inserción/deleción de la lista; luego recorrer hasta `+0x34c=0` sin dispatch inválido. Sin cambios Vita/VPK.
