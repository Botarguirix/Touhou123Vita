# Iteración 2.175: el roster persistente admite solo los IDs 0–19

Se revisó la ruta de persistencia para distinguir el roster normal de la capacidad de construcción del factory. `SaveDataManager::enableCharacter` en `0x42ee80` obtiene el ID, lo compara con `0x14` (20) y salta sin escribir para `ID >= 20`; solo el tramo `0..19` llega al store `[this + 0x30 + id] = 1`. El factory de Player llama a esta rutina en `0x46de48` después de crear y almacenar cada instancia.

La estructura de referencia `local/SokuLib/src/GameData.hpp` declara `enabledCharacters[20]`. `Character.hpp` enumera `CHARACTER_RANDOM=20` y `CHARACTER_NAMAZU=21`. Por tanto, aunque el factory puede construir Namazu por ID 21, el registro de desbloqueos guardados no lo trata como uno de los 20 personajes seleccionables habituales. Esto apoya que la ruta de Namazu sea especial (por ejemplo, un actor Story/boss), pero no demuestra cuál modo lo solicita ni descarta un selector oculto fuera del array persistente.

Se añadió una regresión que fija el límite `0x14`, el branch de rechazo, el store del flag, la llamada desde el factory y los tamaños/IDs declarados en SokuLib. La prueba individual pasa; la suite focalizada se amplía de seis a siete pruebas. No cambia el runtime Vita ni el VPK.

Siguiente: localizar productores de `PlayerInfo.character=21`, con prioridad en las estructuras `PlayerInfo` que entran por los callers Story/replay del helper `0x46ead0`. Eso debe determinar cuándo se crea Namazu y qué subconjunto de sus recursos PAT usa su ruta real.
