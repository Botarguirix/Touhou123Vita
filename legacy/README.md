# Motor reimplementado a mano (congelado)

Este directorio contiene el motor C escrito a mano durante las iteraciones 1.0–2.199: lector de DAT/CV2/PAL/PAT, kernel de animación, combate parcial, escenarios BG02–BG38, replays y la app Vita con framebuffer por software.

**Está congelado desde el 21 de octubre de 2026** (etiqueta `legacy-reimpl-2.199`). La ruta principal es ahora la recompilación estática del PE original ([docs/ROADMAP_RECOMP.md](../docs/ROADMAP_RECOMP.md)). Aquí solo se aceptan correcciones para que siga compilando o para reutilizarlo como oráculo o herramienta de inspección.

Se sigue construyendo con los mismos comandos desde la raíz del repositorio (`CMakeLists.txt` y `tools/build-vita-native.ps1` apuntan a `legacy/`).

| Ruta | Contenido |
|---|---|
| `src/`, `include/t123/` | Motor y app Vita (`vita_main.c`, `soft2d.c`) |
| `tests/*.c` | Pruebas C nativas y `auto-test.txt` del autotest de Vita3K |

Las pruebas Python de `tests/` y las sondas x86 de `tools/` siguen en la raíz: sirven tanto al motor congelado como de oráculos para el código recompilado.

## Correcciones de regresión T6 (21 de octubre de 2026)

Se reprodujeron los tres fallos asignados antes de modificar el código. La
aserción `patterned_states()==0` era la propagación del primer fallo de Suika,
no una segunda causa independiente.

- **Suika 530/821:** había un fallo de código y una expectativa de fase antigua.
  La ejecución del PE fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`
  confirma que `0x47ce20` deja `objeto+0x34c=1` tras el impacto y escribe
  `objeto+0x190=9`; el siguiente update `0x7876d0` lo retira. Se conserva activo
  el burst hasta ese update mediante `persist_after_hit`, que también impide
  resolver dos veces el daño. El estado observado por la prueba C ya incluye
  la colisión del cuadro de creación: `age=1`, `hit_done=1`. Se mantienen las
  comprobaciones de daño 800, reacción 50, timer 20 y un único impacto.
- **Remilia 412/801:** la sonda terminaba el barrido geométrico con `dx=200` y
  dejaba X=203 en lugar del spawn X=403. Ahora restaura los ocho bytes de X/Y
  y sincroniza las cajas antes de medir el ciclo de vida. El primer paso vuelve
  a X=391,72369384765625; el manager original `vtable[4] -> 0x633ce0` completa
  73 updates y 25 retornos del factory (un principal y 24 estelas), conservando
  seis estelas al retiro. Se actualizan los conteos antiguos 55/19; las pruebas
  de trayectoria, geometría y retiro siguen siendo estrictas.
- **Cámara:** la comprobación textual aún exigía la selectora anterior, que
  usaba coordenadas fraccionarias solo para 821. Se exige la selectora vigente
  para 821 y 801, manteniendo todas las comprobaciones de proyección.
- **Fixture Reimu 505/811, antes oculto por el primer aborto:** X=286 solapaba
  cuatro proyectiles con las cajas en unidades completas. X=380 sitúa el borde
  izquierdo de la hurtbox en 360, entre los bordes derechos 369 y 359 de los
  dos primeros proyectiles. Esto aísla el impacto de 550 que pretendía medir
  la prueba; además se comprueba que los otros tres objetos siguen activos.
  No se modificó el comportamiento de Reimu.

Confianza alta para los estados medidos de Suika y Remilia y para las causas
de los fixtures. El registro local está en `artifacts/t6-c-before.log`,
`artifacts/t6-targeted-before.log`, `artifacts/t6-suika-pair-active.json` y
`artifacts/t6-remilia-after.json`; estas salidas permanecen fuera de Git.

Verificación: la compilación de `fight_tests.c` con GCC host
`-std=gnu11 -O1 -Wall -Wextra -Werror` y su ejecución terminaron con código 0.
`python -m unittest discover -s tests -p "test_*.py"` terminó con
`Ran 151 tests in 120.216s` y `OK` (código 0). No se compiló un VPK ni se
ejecutó Vita3K o una consola para esta tarea de regresión host.
También pasaron los diez contratos C (`core`, `fight`, `arena`,
`collision_world`, `animation`, `resource`, `pattern`, `input`, `stage` y
`replay`), compilados con esas mismas flags; registro:
`artifacts/t6-native-contracts.log`.
