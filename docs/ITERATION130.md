# Iteración 2.30: hit-confirm original de Suika 623C

Fecha: 2026-10-17.

Se amplió `tools/x86_player_pair_hit_probe.py` para ejecutar hit-confirm x86 entre dos Players contra frames PAT reales de Suika, además de conservar el caso Remilia. El PE de referencia está fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.

Resultados del resolver original `0x47c770`:

- Suika 521, secuencia PAT 1 pose 0: 400 de daño PAT, overlap original confirmado por `0x47a5b0`, el hit response toma la rama especial de Suika, selecciona reacción 74 y resta 533 HP (1000→467).
- Suika 526, secuencia PAT 0 pose 7: 500 de daño PAT, overlap original confirmado, reacción 74 y resta 666 HP (1000→334).
- Control Remilia 320 pose 3 sigue aplicando 200 (1000→800), para verificar que la generalización no cambió la corrida existente.

El factor `4/3` sale del código original del hit response; se conservaron los multiplicadores de jugador en 1.0, incluidos `stats+0x544/+0x548`, que los flags PAT de Suika consultan. El fixture mantiene controlados el lookup PAT, estado de pelea, posiciones, multipliers, contadores y factory de efectos; el objeto de efecto es sintético y no se renderiza. No es una corrida conducida por input/replay ni completa el constructor de `PlayerSuika`.

La sonda separada de setter sigue mostrando que acción, secuencia inicial y conteo PAT se escriben antes de llegar a la frontera Win32/SEH del constructor (`FS:[0]`), que Unicorn no configura en esta ejecución. Su regresión ahora afirma únicamente esos campos parciales y documenta la limitación; el hit-confirm de este documento se apoya en el constructor base de Player ya validado por la prueba de Remilia.

Pruebas focalizadas: 6/6 aprobadas. Suite completa pendiente de repetición. Sin cambios en runtime Vita o VPK. Próximo: resolver la ruta 531 de Suika, que no tiene daño/cajas en las variantes PAT examinadas; rastrear creación/update/colisión de objetos antes de integrarla al motor Vita.
