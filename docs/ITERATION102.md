# Iteración 2.02: contrato de creación del objeto 801 en Remilia 412

Se verificó el destino `0x46eb30` llamado por el handler dedicado de Remilia 412. Es un wrapper que toma el ID de objeto y parámetros de posición/transformación, obtiene el manager en `Player+0x6f8` y hace una llamada virtual al método `[vtable+4]`; por la convención documentada en los callsites del PE, corresponde a `Player::createObject`. El bloque de `0x58cce7` pasa el ID `0x321` (801) y valores de posición derivados de `Player+0xec/+0xf0` y facing.

Esto confirma que el update especial solicita un objeto de juego 801 en el subestado `+0x140 == 4`, seguido por `0x464980` con índice EBX. Aún no prueba que ese objeto sea el responsable de los 750 de daño de pose5: falta resolver el initializer/update/collision de 801 y demostrar su conexión temporal con 412 en ejecución.

La evidencia desensamblada del wrapper y del callsite está en `artifacts/kernel/remilia-412-object801-trace.tsv` (ignorados; PE SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`). No cambia el runtime ni el VPK.
