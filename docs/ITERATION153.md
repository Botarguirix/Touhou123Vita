# Iteración 2.53: respuesta x86 de Remilia 801, campos separados por objeto

La captura dinámica dentro de `0x47b660` corrigió la interpretación anterior del offset. En el hit, `ESI` es el proyectil 801 y `EBX` el defensor. La rutina escribe en el proyectil `+0x194 = +0x1bc - 1` (prioridad 4→3), copia `PAT frame +0x2a` a `+0x196` (0 para este cuadro), marca `+0x190=9` y resta 120 HP al defensor (1000→880). En el defensor, `+0x194=20` y `+0x1bc=20` ya estaban presentes al entrar a la respuesta y no son valores escritos por el hit.

El objeto todavía tiene `+0x34c=1` al salir de la respuesta, pero la actualización siguiente del manager falla en el callback no inicializado `0x82370a`; por tanto el ciclo de vida visual posterior al impacto continúa pendiente. El probe x86 prueba la asignación de campos y la prueba enfocada pasa.

Ver [ITERATION155.md](ITERATION155.md) para el cambio Vita: conservar el 801 tras su primer impacto, avanzar su PAT y bloquear golpes repetidos hasta que termine. El VPK actualizado pasa la regresión específica en Vita3K. SHA-256 `158166ff94bdd7eec3ceb10d7646578aef009a8a2d80c687ba6cf4f9eec1c031`.
