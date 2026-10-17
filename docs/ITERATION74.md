# Iteración 1.74: loop PAT auténtico en la corrida Suwako 808

La iteración anterior reveló que el probe escribía el byte `loop` en `SequenceData+0x10`, pero el layout usado por las rutinas x86 y por el oracle de animación sitúa ese flag en `+0x14`. En consecuencia, el resultado anterior de secuencia 4/alpha 175 a 32 ticks era inválido y queda supersedido.

Se amplió `tools/extract_pat_pose_metadata.py` con `action_sequence_metadata`, que lee los records directamente del PAT desencriptado, conserva modo loop, nombres de imagen y duración por frame. `tools/x86_suwako_808_factory_probe.py` ahora aplica prioridad de DAT `th123c.dat`, luego b/a, y alimenta la factory/dispatcher desde el recurso local `data/character/suwako/suwako.pat`. La selección efectiva fue `th123c.dat`, SHA-256 `1e7e06920e9a7a0e8b0ee0fc160a5b2dd3a19f2cdba2ba8144ab969d0a9dc906`.

La acción 808 contiene dos secuencias: seq.0 tiene loop=1 y diez frames `bulletEa000.bmp`–`bulletEa009.bmp`, cada uno con duración 2; seq.1 tiene loop=1 y un frame `bulletAb000.bmp` con duración 10. Tras escribir el loop en `SequenceData+0x14`, el factory retorna con action 808/seq.1, `(300,400)` y color `ffffffff`. El dispatcher original completa 32 callbacks y mantiene seq.1; el subframe rota 0–9 conforme a duración 10. El alpha termina en 7 y la posición en `(172.7683,650.3658)`, consistente con el handler que reduce alpha en 8 y detiene la integración espacial por debajo de 8. Esto valida secuencia/duración y una trayectoria bajo los servicios controlados, no ciclo de vida completo: el callback gráfico está interceptado, el suelo es constante, la colisión siempre responde “sin contacto”, RNG es fijo y no se recorrió el manager de borrado ni se comparó una traza nativa.

El reporte contiene el hash de PAT y todos los frames/flags: `artifacts/x86-suwako-808-factory-probe.json`. Regresión: `tests/test_suwako_808_factory_probe.py` comprueba hash, flags, duraciones, secuencia estable y alpha del primer tick. La extraída es metadata de secuencias y duración; los descriptors de frame siguen siendo mínimos, sin decodificar cajas/efectos en la memoria guest.

## Próximos pasos

1. Construir frame descriptors completos (incluidas cajas/flags necesarios para colisión) a partir del PAT y cotejar offsets con `0x4679e0`/loader x86.
2. Ejecutar los callbacks de colisión/terminación reales con una escena reproducible, registrando asignación, update, hit y destrucción del objeto.
3. Portar al runtime Vita únicamente cuando los contratos de movimiento, hitbox y vida estén comparados contra la referencia.
4. Añadir la regresión a un VPK de juego y validar en Vita3K; esta iteración no reconstruyó el VPK.
