# Iteración 2.22: CollisionType y límite del daño aislado

El layout de `GameObjectBase` en `local/SokuLib/src/GameObject.hpp` identifica `+0x190` como `CollisionType`: 0 ninguno, 1 impacto, 2 bloqueo, 3 estado que no permite cancelar; los valores 4–8 son estados de interacción entre proyectiles/armadura. El handler Remilia `0x59c010` habilita su transición 5AA→5AAA si este campo no vale 0 ni 3, por lo que los estados de impacto/bloqueo son relevantes.

La sonda existente ahora registra el campo tras el pair dispatch original. El fixture de Remilia 321 frente al proyectil Remilia 801 reduce HP de 1000 a 880, pero `defender+0x190` queda en 0. La prueba correspondiente exige ese resultado y conserva la distinción entre pérdida de HP y confirmación de golpe. Esta ruta aislada no ejecuta el ciclo completo de respuesta del `Player` y no puede demostrar el cancel natural.

Siguiente: crear una interacción de ataque cuerpo a cuerpo con dos objetos `Player` inicializados por sus constructores originales; ejecutar el resolver y la respuesta del defensor para observar `CollisionType`, hitstop y estado de acción; después pasar el `Player+0x190` resultante al `handleInputs` original en el tick siguiente y verificar que llama el setter con 321. El VPK/runtime no cambia.
