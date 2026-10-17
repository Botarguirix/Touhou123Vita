# Iteración 1.29: conservar los bytes auxiliares de cada pose PAT

## Cambio

`T123Pose` ahora conserva, sin interpretarlos, los 30 bytes que siguen a las cajas de cada pose en el PAT. Antes el decoder comprobaba que existieran y los descartaba. Guardarlos permite estudiar después el efecto/estado asociado a poses como Alice 418 o Suwako 418 sin perder información del recurso ni atribuirles una semántica inventada.

Se agregó un fixture en `tests/pattern_tests.c` que llena esos 30 bytes con una secuencia conocida y comprueba que el decoder los preserva. La compilación VitaSDK incorpora el nuevo campo y el VPK decodifica los 20 PAT en Vita3K sin fallos.

## Validación

- Build VitaSDK y runner Vita3K SDL: aprobado, schema 16, 600 frames, 35 impactos directos PAT, 3 acciones sin caja directa, 20/20 PAT y recursos, 137 texturas, BG34, cero fallos de textura.
- VPK: [Touhou123Vita-roster-hits.vpk](../artifacts/Touhou123Vita-roster-hits.vpk), SHA-256 `1a8836b9d040c162800bbbf956d422b770bb12c934a1186026062a3407c9d3b4`.
- Suite Python: 8/8 y `git diff --check` limpio.
- El test C `pattern_tests` queda añadido, pero no se pudo ejecutar como host porque CMake y un compilador C host no están disponibles. Para verificar el contrato en ejecución, el autotest del propio VPK construye el mismo fixture, comprueba byte por byte los 30 valores y exige `pat_effect_fixture=1`; Vita3K pasó esa prueba.

## Próximo paso

Interpretar el payload byte a byte comparando PAT fuente, campos XML y el parser x86 del juego; sumar la creación/actualización de objetos solo cuando las llamadas y datos fuente confirmen su contrato. La prueba diferencial del decoder sigue pendiente.
