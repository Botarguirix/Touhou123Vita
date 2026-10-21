# Iteración 2.58: estado de los objetos secundarios de Remilia 801

Amplié `x86_remilia_412_spawn_probe.py` para registrar, después de los updates del manager original, secuencia, selector/pose, cantidad de poses, duración del descriptor activo, contador `+0x144`, modo `+0x190`, posición y campo de vida `+0x34c` de cada nodo activo.

Con la fixture controlada y `--real-factory --resolve-damage`, el manager completa 73 ticks: retira el objeto inicial y deja seis nodos 801 enlazados. La traza registra 25 retornos de factory; los seis supervivientes son seq.1, tienen 8 poses, duración 4, `+0x190=0` y `+0x34c=1`. Sus contadores son `[16,13,10,7,4,1]`; cada paso entre ellos cambia X en aproximadamente `-33.8289` y Y en `+12.3127`, consistente con emisiones espaciadas cada tres updates. Esto amplía la observación de Iteración 2.13 (19 solicitudes durante 55 ticks).

La regresión `tests.test_remilia_412_spawn_probe` verifica el conteo, los campos PAT activos y el espaciamiento de posiciones. Resultado: 5/5. Reporte: `artifacts/kernel/remilia-412-object-manager-live-nodes.json`.

El runtime Vita aún solo emite el objeto raíz seq.0; no reproduce las emisiones seq.1 ni el culling/retirada de secundarios. No cambié código Vita ni regeneré el VPK. Próximo: ejecutar updates aislados sobre un secundario y determinar la condición/tiempo exactos que ponen `+0x34c` a cero antes de portar su trayectoria visual.
