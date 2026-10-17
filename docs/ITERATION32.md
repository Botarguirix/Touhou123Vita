# Iteración 1.28: daño directo de dash y revisión de Touhou75Vita

## Resultado de combate

El probe carga las variantes PAT seleccionadas para los dashes 408/418 de los 19 personajes que las tienen. En 35 de 38 casos encontró una caja ofensiva directa, colocó al rival en contacto y verificó que la reducción de HP coincidiera con el daño escrito en PAT. Los otros tres casos no tienen caja directa en la variante seleccionada; pueden requerir objetos/efectos, cuya ruta todavía no se ha implementado ni probado. Remilia conserva su ruta propia 2C/412 y no forma parte de estos 38 dashes.

La primera build de esta iteración pasó la cobertura de combate reportada abajo. El VPK vigente también verifica el payload auxiliar PAT en el autotest Vita3K; véase [ITERATION33.md](ITERATION33.md).

Esta prueba valida la simulación nativa con datos PAT y la aplicación local del daño; no demuestra paridad por frame contra el ejecutable de PC ni un combate completo.

## Revisión del otro proyecto

En el chat **Configurar Touhou75Vita**, el estado registrado es un prototipo: herramientas para recuperar funciones, ramas/llamadas, reachability, lifting a IR y generación semántica C; un runtime mínimo de registros/memoria; y una prueba smoke host que comprobó algunos registros, stack y globales. El VPK solo inspecciona encabezados PE32. La compilación VitaSDK no se validó allí porque el proxy respondió HTTP 403 al bootstrap.

La metodología transferible a TH123 queda aplicada como análisis incremental con hashes, cobertura por función/opcode, pruebas diferenciales y errores explícitos ante rutas no entendidas. No conviene importar direcciones, runtime ni código C generado entre juegos. La raíz revisada de Touhou75Vita no declara licencia; no se copió código. La evaluación de D2Vita y repentogxm y sus diferencias de licencia/arquitectura permanecen en [PORT_REFERENCES.md](PORT_REFERENCES.md).

## Revisión de las tres rutas sin caja ofensiva

El reporte agrupa estas filas como `dash_no_direct_boxes`, que solo significa que el PAT seleccionado no tiene la pareja de daño y caja ofensiva que ejercita el probe directo. La inspección del XML fuente refina el diagnóstico:

| Personaje/acción | Datos del PAT fuente | Estado |
|---|---|---|
| Alice 408 | 16 poses, todas con daño 0; sprites incluyen `spellAa`/`shotAa` | No hay golpe directo definido en esta acción; comprobar en el handler si los sprites activan un objeto aparte. |
| Alice 418 | 15 poses; pose 4 (`spellGa004.bmp`) declara daño 1000, secuencia de impacto 72 y `onhiteffect=7`, pero carece de caja `<attack>` | Hay datos de daño sin geometría ofensiva directa. Resolver el mecanismo x86 que aplica el contacto. |
| Suwako 418 | 23 poses; daño 0; secuencia visual `dashBack` y luego `shotCd` | No asumir que sea ofensiva: determinar si es movimiento defensivo, cancelación o disparo secundario en ejecución. |

El reporte vigente (schema 16) denomina el contador `dash_no_direct_boxes` para no insinuar que esos casos usan efectos confirmados. El VPK valida 35 impactos directos; las tres filas anteriores siguen fuera de la cobertura de daño. El contador de rutas sin caja verifica la clasificación del fixture, no que el juego haya ejecutado un objeto o efecto.

## Próximo paso

Seguir el handler de Alice/Suwako y sus callbacks de update de personaje/objetos para identificar las llamadas de creación de objetos y la rutina de colisión que consume estas poses; contrastar con una corrida x86. Después modelar la semántica confirmada. Mantener la ruta especial de Remilia separada hasta modelar su objeto 2C.
