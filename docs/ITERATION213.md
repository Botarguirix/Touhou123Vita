# Iteración 2.113: la selección de Story y el loader replay son pasos distintos

Se amplió la sonda estática fijada al `th123.exe` 2009 proporcionado (SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`).

El método `CTitle` en `0x447c0c` lee el elemento seleccionado. En la rama donde el índice es 0 (`0x447c23–0x447c25`) escribe estado título 12, valor asociado 6 y llama `0x447310` para cambiar de pantalla. La Iteración 2.112 demuestra que el handler CTitle de estado 12 solicita manager modo 6 y estado de ciclo 2, que activa el callback Story. Esto apunta a una entrada de Story desde la selección del título.

Un método separado `0x44a120` construye una cadena/path, obtiene el objeto global mediante `0x43cec0`, llama al loader genérico `0x42e030` y, si la carga devuelve éxito, escribe estado título 6. La lectura es coherente con una carga de replay separada de la entrada a Story; todavía no se probó que la ruta cargue el archivo `090815_2219_sanae_story.rep`, ni qué etiqueta visible corresponde al índice cero.

La sonda verifica las instrucciones y ambos métodos en el PE original. `python -m unittest tests.test_replay_manager_selection_probe` pasa (1/1). No se modificó el runtime ni se generó un VPK en esta iteración.

Siguiente: recuperar los callers de `0x44a120`, la construcción concreta del nombre/ruta `.rep` y la función que actualiza el índice de selección; contrastar esos resultados con una sesión o captura frame-step del juego original para conectar el replay Sanae con el manager Story.
