# Iteración 2.16: constructor de personaje y elegibilidad en pares

La búsqueda de escritores de `object+0x1ac` localizó su ciclo de vida: el constructor base de personaje empieza en `0x46b7f0` y escribe 1 en `0x46b8db`; la limpieza `0x46b9a0` lo pone a cero en `0x46b9c8`. Entrar directamente en `0x46b800` omitía el prólogo y desbalanceaba el retorno; la sonda ahora ejecuta el prólogo completo. Los bytes de ambas escrituras quedaron fijados en el analizador estático y el constructor se ejecuta en el fixture del defensor.

Con ese campo producido por el PE (`+0x1ac=1`) y la hurtbox PAT neutral Remilia (`frameFlags=0x31`), el pair dispatcher llega al resolver pero no causa daño. Al diferencial sintético solo se modifica `frameFlags |= 0x40`; entonces la ruta original recorre `0x47ce20 → 0x47c990 → 0x47b660 → 0x47a5b0`, confirma el solapamiento y aplica 120 de daño antes del callback nulo. Esto aísla el guard de PAT pendiente, pero el override no se considera un impacto natural.

La suite Python completa se ejecuta antes de integrar esta iteración. Siguiente: encontrar una acción/pose original con hurtboxes y `frameFlags&0x40`, enlazarla al personaje con actualización x86 auténtica y confirmar daño sin tocar flags. Después queda resolver callback de presentación, reacción/guardia, hitstop y una corrida de combate natural end-to-end. Sin cambios de runtime ni VPK.
