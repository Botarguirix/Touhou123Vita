# Iteración 2.01: corrección del dispatch de update Remilia 412

La Iteración 1.95 atribuyó la acción 412 al update genérico `0x483f40` al no seguir la rama anterior del dispatcher. Esa conclusión queda supersedida: el dispatcher compara action con `0x12c` (300) y envía las acciones 301–512 al bloque especial `0x58a3a1`. Para 412, índice 111/grupo 23, el salto de tabla apunta a `0x58cce7`.

El handler dedicado primero ejecuta servicios de objeto y valida `+0x13e`, `+0x142` y `+0x140`. En la rama `+0x140 == 4`, ajusta el estado, llama `0x47a9e0` con 200/60, configura otro parámetro y llama `0x46eb30` con ID `0x321` (801) y parámetros de posición; luego llama al callback indexado `0x464980` con índice EBX. La Iteración 2.02 confirmó que `0x46eb30` es el wrapper de `Player::createObject`. Esto demuestra la solicitud de creación del objeto 801, pero no demuestra todavía que ese objeto aplique los 750 de daño PAT.

El hallazgo corrige el mapa de control, no completa la mecánica. Falta ejecutar la transición natural 412 seq.0 hasta pose5, identificar el callback de `object+0x164[EBX]`, seguir el objeto 801 por su initializer/update/collision y comparar el primer contacto con el juego x86. La sonda de input previa sigue siendo controlada y no prueba un combate natural.

Evidencia local fijada al PE SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`: `artifacts/kernel/remilia-412-update-branch.tsv` y `artifacts/kernel/remilia-412-specific-handler.tsv` (ignorados por Git). No se modificó runtime ni VPK en esta iteración.
