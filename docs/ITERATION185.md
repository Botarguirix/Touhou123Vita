# Iteración 2.85: target vertical dependiente del zoom

De `FUN_00428e20` se aisló el objetivo Y automático con el zoom vigente: cuando `min(y0,y1) <= 270`, `targetY = -0.2 * abs(y0-y1) * (2*currentZoom-1)`, con piso `-420`; cuando el mínimo supera 270, `targetY = -min(minY,420)`. La diferencia respecto a la media vertical es intencional: el método encuadra la separación vertical con una ponderación que cambia al acercar/alejar. La doble evaluación del constructor hace que el target inicial y el target recalculado difieran.

Se implementó `t123_stage_camera_y_target` con zoom explícito, comparación del oracle x86 en cuatro niveles de zoom y casos del umbral 270/límite 420. La suite completa pasó 108/108. El VPK auto-test compiló y pasó Vita3K SDL durante 600 cuadros, schema46, `regression_gate=1` y `stage_camera_pair_contract=1`.

VPK automático: `artifacts/Touhou123Vita-camera-y-target-auto.vpk`, SHA-256 `891c560e54c5f22d9ed923113f4402b19f0aced8206576860198ed4fe0a36cc2`. Interactivo: `artifacts/Touhou123Vita-camera-y-target.vpk`, SHA-256 `cd5b4a7dc17271d1cd5e3524088255ee65e79e2caf02365c3527a3bebd6d7ff8`. Ambos comparten `eboot.bin` SHA-256 `2fb8dd1986b0ba4ed2e862e369791983627e3c308a89097ed8a3ac321a48fa30`; solo el auto-test se ejecutó en Vita3K.

El easing vertical de `FUN_00429040` aún no está portado: además del target intervienen el estado Y actual, el mínimo de ambos jugadores y límites de viewport. Tampoco se alimenta aún el renderer de pelea. Ver la corrección metodológica [ITERATION184.md](ITERATION184.md) y el oracle `tools/x86_stage_camera_oracle.py`.
