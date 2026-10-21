# Iteración 2.183: ausencia de BG35 confirmada en los seis DAT indexados

Verifiqué la cobertura de los manifiestos fuente, no solo los archivos `a`: `th123-resource-manifest.tsv` contiene entradas de `th123a.dat`, `th123b.dat` y `th123c.dat` (10,625/49/609); `th105-resource-manifest.tsv` contiene `th105a.dat`, `th105b.dat` y `th105c.dat` (11,935/61/247). Ninguno de los seis conjuntos indexados tiene rutas bajo `data/background/bg35/`.

Esto amplía la conclusión de Iteración 2.51: los recursos BG35 no están en los DAT locales de 10.5 ni 12.3 que se indexaron. El PE sí despacha BG35 por el constructor genérico de cuadrícula 5×6; el loader de recursos devuelve nulo si el lookup falla y no dibuja tiles nulos. No se concluye que toda distribución comercial carezca de BG35 ni que el fondo vacío sea una decisión artística. No hay base para fabricar tiles.

`tests/test_bg35_pe_contract.py` ahora exige que ambos manifiestos incluyan sus tres archivos DAT antes de comprobar la ausencia de rutas BG35. Pruebas PE/manifiesto y los contratos de auditoría relacionados pasan 7/7. Sin cambio de runtime/VPK.

Siguiente: comparar BG35 elegido en el juego original con la salida del PE y buscar un DAT de otra edición solo si la referencia carga recursos. En paralelo, continuar la integración de los escenarios que sí tienen assets locales y contratos de renderer.
