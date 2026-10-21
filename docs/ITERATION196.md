# Iteración 2.96: estado inicial WRAP en sampler Direct3D

La configuración Direct3D aclara la hipótesis de la iteración 2.95. En `0x41e1bb–0x41e1eb`, el PE invoca el wrapper genérico `0x404ad0` cuatro veces para fijar sampler 0 y 1: `SetSamplerState(0, ADDRESSU, WRAP)`, `SetSamplerState(0, ADDRESSV, WRAP)`, y lo mismo para sampler 1. En D3D9, los enums de direccionamiento son `ADDRESSU=1`, `ADDRESSV=2`, `WRAP=1`.

`0x404ad0` reenvía sus tres argumentos a la vtable D3D9 en el slot `+0x114`. Los callsites de `0x404af0` usan ese mismo método para `MAGFILTER` (tipo 5) y `MINFILTER` (tipo 6), con point o linear; esos cambios no modifican U/V. El wrapper del camino directo de jugador `0x4389d0→0x4075d0` liga la textura y dibuja, pero no llama a `0x404ad0`, así que consume el estado activo del dispositivo.

Hay otras rutas de dibujo genéricas que sí cambian sampler 0 U/V a partir de campos de su objeto (por ejemplo, `0x4571a4/0x4571b6` antes de continuar a `0x4075d0`). Esto significa que el arranque fija WRAP, pero todavía no demuestra que ningún objeto dibujado antes haya alterado el estado cuando aparece uno de los ocho frames PAT extremos. No se debe codificar clamp, omisión ni WRAP permanente en el renderer Vita basándose solo en el valor inicial.

Los callsites directos de `0x404ad0` quedan en [`d3d9-sampler-generic-callers.tsv`](../artifacts/kernel/d3d9-sampler-generic-callers.tsv) (30 referencias); la rutina que selecciona filtros y el camino que asigna U/V están en [`d3d9-sampler-mode-manager.tsv`](../artifacts/kernel/d3d9-sampler-mode-manager.tsv) y [`d3d9-sampler-active-paths.tsv`](../artifacts/kernel/d3d9-sampler-active-paths.tsv). Todos fijan el mismo SHA-256 del PE.

Seguimiento: la Iteración 2.97 inventarió los 30 callers directos del setter y encontró restauraciones a WRAP en los grupos SpriteEx y de escenario revisados. Queda verificar en runtime el orden de callbacks y capturar los cuadros PAT extremos; ver [ITERATION197.md](ITERATION197.md).
