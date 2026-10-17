# Iteración 1.49: aterrizaje de Reimu 560

## Implementación

Se portó a `src/fight.c` la condición demostrada por el ejecutable x86: en action 560, Reimu solicita la secuencia PAT 3 al hacer contacto con el suelo mientras desciende. La arena actual usa un suelo plano en `y=0` y aún no modela el flag separado de colisión del juego; por eso, la aproximación local es `y<=0 && vy<0`. En ese contacto mantiene action 560 y reinicia la animación en seq. 3 (recuperación `dashStop`) en vez de reemplazarla por action 10.

Se añadió un caso de regresión en `tests/fight_tests.c` y se extendió el auto-test incluido en el VPK para colocar al jugador en action 560/seq. 2, simular contacto descendente y exigir `skill_landing_ok=1` y `skill_landing_sequence=3`. El runner `tools/vita3k-test.ps1` ahora comprueba esos campos.

## Evidencia

- El PE x86 `th123.exe` fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` ya confirmó mediante Unicorn el gate de altura, velocidad descendente y flag sin colisión; casos de aire, velocidad cero y flag activo no seleccionan seq. 3. Ver [ITERATION52.md](ITERATION52.md).
- Build nativo VitaSDK: VPK automático compilado en `artifacts/reimu-landing-recovery.vpk`; SHA-256 `d6fd804fe1a1eb46fdc84c3fa4c9c2eebb6bd484219683258c35e4b1acfa95f8`.
- Vita3K aislado, corrida fresca SDL: schema 21, 600 frames, `status=passed`, `skill_landing_ok=1`, seq. 3, roster/cards/assets 20/20, escenario BG34 y regresiones existentes de dash, B/C y objetos sin fallo.
- Suite Python: 19/19. `git diff --check` sin errores.

## Límite pendiente

La prueba Vita3K ejecuta esta condición con un estado aéreo sintético; el runtime todavía no da a la carta 103 su impulso/entrada aérea real, por lo que el touchdown no se alcanza todavía mediante controles normales. Tampoco está reconstruida la salida posterior de seq. 3 ni el coste/cancelación de cartas. La transición es ahora parte del runtime y está cubierta por la sonda del VPK, pero no equivale a una skill completa ni a paridad del combate.

WSL continúa inaccesible (`E_ACCESSDENIED`), así que no se ejecutaron las pruebas C host de `tests/fight_tests.c`; la compilación ARM y la sonda Vita3K sí validaron el código integrado.
