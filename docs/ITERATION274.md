# Iteración 2.174: la cola `GameDataManager` alimenta el factory de Player

La construcción de Namazu no es una ruta aislada: el código del ejecutable enlaza su constructor con el flujo común de creación de Players. SokuLib modela `GameDataManager` en `local/SokuLib/src/GameData.hpp` con `List<std::pair<int, PlayerInfo*>> createQueue` al offset 0, cuatro punteros `players[4]` en `+0x28` y colas de objetos auxiliares. El desensamblado es consistente con ese layout:

- `0x46ead0` recibe un slot 0..3, un `PlayerInfo*` y un flag. Su rama síncrona llama al factory `0x46da40`; la alternativa prepara el registro para el worker.
- `0x46e6e0` despacha `0x46e5c0`, que consume nodos de la cola y llama `0x46da40` por cada entrada.
- `0x46da40` lee el ID de personaje desde el `PlayerInfo`, despacha la jump table `0x46de64` y almacena el resultado en `players[index]` (`manager+0x28+index*4`). La entrada 21 llega al constructor `0x7ec4c0` de Namazu (Iteración 2.173).

Se registraron los callers visibles del helper `0x46ead0`: `0x4386e6`, `0x45f176`, `0x47fce0`, `0x47fcf3`, `0x4818d4` y `0x4818e7`. Los dos últimos grupos crean los slots 0/1 desde estructuras de jugador; `0x45f176` solicita el slot 3 con el flag asíncrono. Esto identifica varias rutas que pueden suministrar un `PlayerInfo`, pero no demuestra que alguna lo configure con ID 21 ni permite asignar aún esos callers a un modo de selección concreto.

Se añadió una regresión estática que fija la llamada helper→factory, el worker→queue-drain, el almacenamiento en el arreglo de cuatro Players y el layout local de `GameDataManager`. Las seis pruebas de `test_scan_player_field_884` pasan. Sin modificación de runtime Vita ni VPK.

Siguiente: rastrear los escritores de `PlayerInfo.character` y sus callers en los caminos que llevan a `0x46ead0`, buscando el valor 21. Luego comprobar si la ruta corresponde a Story/boss, selección normal o datos de replay. Mantener el inventario de recursos Namazu separado de la afirmación de que sea un personaje seleccionable.
