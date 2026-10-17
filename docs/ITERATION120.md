# Iteración 2.20: update original en 5AAA y causa del caso 602

La Iteración 2.19 detectó `STATUS_INVALID_PARAMETER` al actualizar el defensor en acción 602, pero atribuirlo al constructor base era demasiado general. La traza nueva identifica la rama: `0x594009` llama a `0x46b370(6, 2)`, que consulta el contenedor de `Player+0x72c`; `0x44be10` rechaza el índice 6 porque el contenedor del objeto base está vacío. La referencia local de [Player.hpp](../local/SokuLib/src/Player.hpp) identifica ese miembro como `spellBgTextures`. El caso 602 requiere esa lista de recursos de spell background, que el harness de constructor base no prepara. El vtable derivado aislado no corrige la falta de datos.

La prueba diferencial selecciona la acción PAT 321 (`ACTION_5AAA` en [Action.hpp](../local/SokuLib/src/Action.hpp)) mediante el setter original y ejecuta el dispatcher de personaje `0x587bab`. El update termina en `0x599fb0`, mantiene acción 321/seq.0/pose0 y avanza subframe 0→1, sin entrar al handler CRT inválido. El PAT pose0 usa `stand000.bmp`, duración 2 y `frameFlags=0x41`. En la misma corrida el pair dispatcher original acepta la hurtbox y aplica 120 de daño: HP 1000→880.

Esto demuestra un tick original válido para una acción de combate y corrige el diagnóstico de 2.19; todavía no parte de una entrada natural: acción, posición y listas del manager siguen controladas. La respuesta de daño aún llega a un callback nulo de presentación. Siguiente: producir 5AAA con el matcher/input original desde el estado inicial, ejecutar el tick de impacto y recuperar reacción/hitstop. Para volver a correr 602 también habrá que construir `spellBgTextures` desde su fuente real, no inventar elementos.

Verificación focalizada: `tests/test_remilia_412_spawn_probe.py`; la prueba de acción 321 comprueba update, subframe, flags PAT y mutación de HP. La ejecución con Unicorn en Windows puede imprimir avisos nativos de acceso a memoria durante la inicialización aunque pytest finalice correctamente; esa salida sigue registrada como limitación del harness.

VPK/runtime sin cambios.
