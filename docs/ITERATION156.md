# Iteración 2.56: ciclo de vida x86 del objeto Remilia 801

La respuesta de parejas de `0x47ce20` llega a `0x47b680` y aplica el daño PAT de 120 (HP 1000→880). El fixture enlaza `EffectManager_Effect::CreateEffect` en `0x8985f0`/vtable `+0x0c`, con retorno sintético; por eso la llamada termina, pero el efecto no se carga ni se renderiza.

Se resolvió el fallo del manager sin ampliar regiones de memoria. La fixture de parejas reutilizaba `LIST+0x0c`, que pertenece al vector embebido del manager de objetos, y escribía allí el puntero del jugador. Al mover las listas de combate a un `PAIR_MANAGER` separado (`OWNER+0xd000`), la asignación `0x44a7ff` conserva el vector del manager y desaparece la copia inválida desde `PLAYER`.

El slot virtual 4 del manager (`0x633ce0`) ahora ejecuta 73 ticks consecutivos. Todos retornan; la pose PAT de 801 avanza desde pose 1 hasta pose 12; el callback común ve `object+0x34c=0` en el tick 73 y retira el nodo/handle. El objeto original deja de estar enlazado y quedan seis secundarios 801 activos. Es ciclo de vida dinámico del PE bajo listas, allocator, PAT y servicios de host controlados; no es un match/replay natural ni prueba el render de efectos.

Regresión de Remilia: 5/5; probe de update Suika: 1/1. No se modificó el runtime Vita, así que el VPK no necesitó recompilación. Próximo: validar el hit y el retiro dentro de una secuencia de combate/replay natural, luego reconstruir los callbacks/recursos visuales del manager. El reporte ampliado se genera con `tools/x86_remilia_412_spawn_probe.py`.
