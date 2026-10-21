# Iteración 2.73: auxiliares de BG37/BG38 según el constructor x86

La auditoría de recursos atribuía a BG36, BG37 y BG38 el mismo conjunto de cuatro auxiliares (dos nubes y dos torii). El manifiesto local mostraba BG37 3/4 y BG38 2/4, pero los exportes Ghidra del PE fijado (`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`) contradicen ese denominador:

- El constructor `0x476990` de BG37 carga exactamente `tori1.bmp`, `clowd_l.bmp` y `clowd_s.bmp`, y reserva tres sprites auxiliares. No pide `tori2`.
- El constructor `0x477310` de BG38 carga exactamente `clowd_l.bmp` y `clowd_s.bmp`, y reserva dos sprites auxiliares. No pide `tori1` ni `tori2`.
- BG36 conserva cuatro recursos: `tori1`, `tori2`, `clowd_l` y `clowd_s`.

`tools/audit_stage_resources.py` ahora define los auxiliares esperados por constructor, y la prueba nueva fija estos tres contratos. Se regeneraron `docs/STAGE_RESOURCE_AUDIT.tsv` y `artifacts/stage-resource-audit.json`: BG36 4/4, BG37 3/3 y BG38 2/2, sin auxiliares requeridos faltantes. Las pruebas de auditoría pasan 4/4 y la suite Python completa, 96/96.

Esto corrige la clasificación de recursos; no cambia el loader/runtime, la composición visual ni el VPK. La ventana del juego de referencia no pudo capturarse en esta sesión, así que no se afirma paridad visual live. Véanse los decompilados de los constructores bajo `artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/stage-layout/00476990.c` y `00477310.c`.
