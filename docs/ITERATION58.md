# Iteración 1.55: timing de la skill Reimu 540

Fecha: 2026-10-16.

La sonda real de Vita3K ahora conserva el conteo de updates desde la activación de carta 102 hasta el primer impacto de acción 540. El PAT de Reimu fija la suma de duraciones para alcanzar el primer cuadro dañino: seq. 0 (`3+3+3+3+10=22`), seq. 1 (`5`) y seq. 2 (`2+2+2+2+2+7+2+2=21`). La secuencia 3 comienza así en la actualización 48 contando la llamada que activa la skill. El reporte cuenta los updates posteriores a esa primera llamada: `skill_102_followup_ticks=47`.

La corrida fresca de Vita3K SDL (schema26, 600 frames) observa ese mismo límite: acción 540, imagen de inicio 774, hit en sec. 3/imagen39 y daño exacto 1100 en la actualización 48 inclusive. El runner falla si cambian tick, secuencia, imagen o daño. Esto demuestra consistencia del runtime con la línea temporal codificada en PAT y el avance de poses x86 ya probado por los helpers `nextPose`; no es una captura temporal comparativa del ejecutable PC en una partida real. Falta ejecutar la acción completa en el PC o en Unicorn con su handler y entorno de combate para probar el contrato end-to-end.

El VPK automático es `artifacts/reimu-skill540-timing.vpk`, SHA-256 `e527bd8b088c5915c7b0782efdee9c434c388e2d2adf28ef1dcfbeb7693f1539`. Conserva las regresiones 103→560, roster20/20 y BG34.
