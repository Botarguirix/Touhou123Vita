# Iteración 2.51: contrato de carga original de BG35

La inspección del dispatcher PE `FUN_00470e40` confirma que el ID `0x23` (BG35) usa `FUN_00477550`, el constructor común `BGCommon`, y no un constructor de escenario especializado. Este llama a `FUN_0046fe40`; con el modo grid (`param_4 > 0`) construye una cuadrícula 5×6 y solicita los nombres `data/background/BG35/0000[01..05][01..06].bmp`.

La auditoría de los índices locales `th123-resource-manifest.tsv`, `th105-resource-manifest.tsv` y `resource-manifest.tsv` no encuentra entradas bajo `data/background/bg35`. `FUN_00405030` devuelve un recurso nulo al fallar la búsqueda; el cargador genérico almacena ese resultado y solo llama al constructor del quad si el puntero no es nulo. Así, con esta copia local de DAT el camino de fondo no dibuja tiles BG35. No se generó contenido sustituto ni se alteró el runtime. La evidencia todavía no descarta que otra distribución del juego aporte estos archivos.

Validación: `tests/test_bg35_pe_contract.py` contrasta dispatcher, constructor/cargador, retorno nulo del loader y los tres manifiestos. `python -m unittest discover -s tests -p 'test_*.py'` pasa 83/83. Las pruebas C no se pudieron correr en esta sesión: `ctest` no está instalado en Windows y WSL respondió `E_ACCESSDENIED`; los artefactos host existentes son ELF/Linux. El VPK permanece sin cambios.

Siguiente acción específica: consultar el juego original en Vita3K/PC con BG35 seleccionado y observar si el fondo queda vacío o registra fallos de carga; si aparece con arte, localizar esa versión/DAT y volver a indexarla antes de dibujar una etapa en el port.
