# Iteración 2.97: inventario de cambios de sampler y restauraciones

Se examinó cada referencia directa al wrapper `0x404ad0` en el PE fijado (SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`). El barrido Capstone de la sección ejecutable devuelve 30 callers, y se contrastaron las ventanas de instrucciones con los dumps Ghidra/renderer que existen. En `SetSamplerState`, el primer argumento es sampler, el segundo tipo (`ADDRESSU=1`, `ADDRESSV=2`) y el tercero valor (`WRAP=1`, `CLAMP=3`).

| Callers | Escritura | Salida/restauración comprobada |
|---|---|---|
| `0x41e1bb/1cb/1db/1eb` | Inicializa U/V a WRAP en samplers 0 y 1 | Configuración inicial persistente |
| `0x4571a4/1b6` | SpriteEx asigna U/V desde `[obj+0x6c/+0x70]` al sampler 0 antes de dibujar | `0x45723c/24c` restaura U/V a WRAP al terminar el lote |
| `0x46f3a9/3b9` | Callback BG02 fija U/V de sampler 0 a CLAMP | `0x46f4d0/4e0` repone ambos a WRAP antes del retorno |
| `0x472047` | Callback BG02 fija V de sampler 0 a CLAMP | `0x47220f` repone V a WRAP |
| `0x472f19` | Callback BG02 fija U de sampler 0 a CLAMP | `0x47322f` repone U a WRAP |
| `0x473649/659` | Callback de etapa fija U/V de sampler 0 a CLAMP | `0x473ac8/ad8` repone ambos a WRAP |
| `0x473fe9/ff9` | Callback de etapa fija U/V de sampler 0 a CLAMP | `0x474ced/cfd` repone ambos a WRAP |
| `0x474e9c/eac` | Callback de etapa fija U/V de sampler 0 a CLAMP | `0x474f22/f32` repone ambos a WRAP |
| `0x47782a` | Callback de escenario fija V de sampler 0 a CLAMP | `0x4779e8` repone V a WRAP |

La agrupación cubre los 30 callsites. Además, el callback directo de jugador `0x4389d0→0x4075d0` no contiene escritura local del sampler. Con la evidencia estática actual, las rutas de escenario identificadas y SpriteEx restauran WRAP antes de retornar; ninguna ruta conocida deja CLAMP persistente al terminar su callback. Esto da una base fuerte para esperar WRAP al dibujar jugador si el orden del frame respeta los límites de callback. Aún falta comprobar el orden dinámico completo y los valores/resultado visual de los ocho recortes PAT extremos; por eso no se cambia el renderer Vita todavía.

La referencia y los DAT comerciales están en `F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law`, y hay un replay story disponible. Intenté iniciar inspección visual automatizada con el runtime de Computer Use, pero falló antes de enumerar ventanas: `failed to write kernel assets: El sistema no puede encontrar la ruta especificada (os error 3)`. No se lanzó ni modificó el juego. Reintentar la captura cuando ese runtime esté disponible; el análisis estático no depende de ese bloqueo.

Evidencia: callers completos en [`d3d9-sampler-generic-callers.tsv`](../artifacts/kernel/d3d9-sampler-generic-callers.tsv), instrucciones SpriteEx en [`spriteex-sampler-complete.tsv`](../artifacts/kernel/spriteex-sampler-complete.tsv), contexto de BG02 en [`bg02-manager-windows.tsv`](../artifacts/kernel/bg02-manager-windows.tsv) y BG33 en [`bg33-render-full.tsv`](../artifacts/kernel/bg33-render-full.tsv), más ventanas combinadas en [`sampler-stage-callers-full.tsv`](../artifacts/kernel/sampler-stage-callers-full.tsv). Estos TSV están ignorados por Git y conservan el hash del PE en la cabecera.
