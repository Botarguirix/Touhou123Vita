# Iteración 2.166: loader PAT original confirma el enlace singleton de action96

Se verificó el caso de una secuencia en el loader real de personajes `FUN_004679e0`, identificado por la cadena `data/character/%s/%s.pat` en el manifest Ghidra. En el bloque nativo `0x467df2–0x467df9`, Capstone decodifica:

```text
00467df2  mov dword ptr [esi + 0x18], 0
00467df9  mov dword ptr [esi + 0x1c], esi
```

Es decir, el primer nodo se inicializa con enlace `next=0` y `prev=self`. Action96 de Suika tiene exactamente una definición efectiva: seq0 de diez frames en `th123c.dat`. Por lo tanto, en el loader original ese nodo único también se autocicla por `+0x1c`; `setSequence(1)` y `setSequence(3)` siguen al mismo nodo y reutilizan legítimamente el payload de seq0. La fixture modela este caso real, no lo inventa. La decodificación se corroboró con el pseudocódigo `artifacts/kernel/<sha>/resource-loader/004679e0.c` y el test nuevo verifica los bytes/instrucciones originales, además del PAT y el enlace construido.

Con action96, el dispatch PE comparte el update `0x485115` con action97. El flujo de 60 ticks observado se explica así: action96 inicia seq0; al avanzar, el handler pone el índice de secuencia en 1 y luego pide 3 desde `0x4851e7`, pero ambos seleccionan el mismo nodo/frame range de diez poses. No hace falta postular un segundo PAT oculto para explicar ese resultado.

Esto es evidencia fuerte de cómo se resuelve el descriptor, pero no asigna todavía semántica visual/gameplay a action96 ni prueba quién la activa en combate natural. Sigue pendiente completar la transición con estado real de suelo, manager de ronda, timers/knockdown y determinar cuándo la acción sale o se repite en una pelea normal. La actualización corrige la conclusión de Iteración 2.165, que atribuía el autociclo solo a la fixture.

Verificación: test de tablas action96/97, construcción del singleton, carga PAT action96 y dos instrucciones del loader del PE: 3/3 tests focalizados. Sin cambios al runtime Vita ni VPK.
