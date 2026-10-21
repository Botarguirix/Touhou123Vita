# Iteración 2.129: factory original y PAT 821 de Suika 623B nivel 9

Se extendió el probe x86 de Suika para ejecutar el factory original `0x784020` desde la acción 530. La ruta del PE (`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`) invoca el objeto `0x335` en la posición `(420,180)`, facing 1, con `customData=(-80,25,0)`. El factory crea PAT 821, secuencia 0, nueve poses y caja `[-50,-50,50,50]`; el cuadro PAT atribuye 800 de daño.

El probe ahora puede dejar correr el RNG xorshift original del PE. Con su inicialización predeterminada, la instancia aparece en `(344.6202,261.1317)`, alfa 0, y termina tras dos actualizaciones en el fixture. La regresión conserva también el caso de contacto alineado para comprobar el daño authored. La Iteración 2.130 añade un barrido del defensor alrededor del spawn natural sin mover el objeto 821.

Validación original de la iteración: `python -m unittest discover -s tests -p test_x86_suika_action_setter_probe.py -v`, 2/2; suite Python completa, 115/115. La prueba existente de 623C/PAT 821 continúa pasando. Evidencia posterior del barrido, rebuild y Vita3K: [ITERATION230.md](ITERATION230.md). No se cambió `src/fight.c`, así que 530 todavía no genera este objeto en Vita; el VPK reconstruido verifica regresiones ya integradas, no la ruta nueva de 530.

El análisis sigue limitado a una instancia del PE y DAT local, sin replay con Suika; no es paridad completa, una ronda jugable ni validación física de Vita. Ver [ITERATION228.md](ITERATION228.md), `tools/x86_suika_action_setter_probe.py` y `tests/test_x86_suika_action_setter_probe.py`.
