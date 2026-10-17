# Iteración 1.53: rutas terrestres de skills de Reimu

Fecha: 2026-10-16.

## Implementación

Generalicé el selector de activación terrestre en `src/fight.c` para usar la tabla del `handleInputs` x86 de Reimu `004AE670`: cartas 100–111 seleccionan acciones `500, 520, 540, 560, 505, 525, 545, 565, 510, 530, 550, 570`. La acción solo inicia si el PAT del personaje tiene secuencias válidas dentro del límite del runtime; la entrada sigue usando el slot fijo de prueba. Las rutas aéreas y selección/costo/consumo de la mano siguen pendientes.

La carta 102 activa acción 540. El VPK carga el PAT real de Reimu, obtiene imagen inicial 774 y comienza en secuencia 0. Para la prueba de contacto el fixture elige la variante PAT de mayor cobertura ofensiva y coloca al rival dentro de sus cajas. Vita3K avanza la acción real hasta secuencia 3, imagen 39, y aplica exactamente 1100 de daño según PAT. `tests/fight_tests.c` conserva además un caso de regresión mínimo para despacho 102→540. La corrida añadida en Iteración 1.55 confirma el primer hit en el update 48 contando la activación, igual a la suma de duraciones PAT 22+5+21; la limitación de esa comparación está descrita en [ITERATION58.md](ITERATION58.md). La trayectoria y touchdown de la skill aérea se siguen cubriendo por separado con carta 103 → acción 560.

## Verificación

- Build VitaSDK: correcto.
- VPK de combate: `artifacts/reimu-skill540-hit.vpk`, SHA-256 `d5607f984c60b0ce1c2959c1a0f42259d1234db4e6a8a2b8a58bbd147ca47507`.
- Vita3K SDL, reporte fresco schema 25, 600 frames: `passed`; carta 102 → acción 540, imagen inicial 774, hit PAT en seq. 3/imagen 39, daño exactamente 1100.
- Regresión: carta 103 → acción 560, impacto en secuencia 1, lanzamiento/aterrizaje y motion x en ambos sentidos; roster/PAT/sprites 20/20; BG34 con 30 tiles y 30 objetos; dash directo 35/38; B/C y fixtures anteriores pasan.
- El oracle x86 ya ejecuta los 20 despachos terrestres/aéreos; los tests Python completos se mantienen separados de la verificación ARM/Vita3K.

El build automático no reemplaza el VPK interactivo de controles manuales. Esta iteración solo generaliza las rutas terrestres y valida el golpe PAT de 540; elegir cartas en mano, pagar costo, descarte, mejora en partida, gates completos, cancelaciones, efectos/objetos y comparación temporal PC/Vita para cada acción requieren implementación y pruebas adicionales.
