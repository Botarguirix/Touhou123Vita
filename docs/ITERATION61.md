# Iteración 1.61: oracle x86 para el spawn de Suwako 418

Añadí `tools/x86_suwako_418_spawn_oracle.py`, que ejecuta el handler original `0076f3b4` del PE 1.10a fijado por hash y captura la llamada `0046eb30`. El oracle inicializa explícitamente el registro `Player+0x158` con valores de prueba y solo sustituye las llamadas externas de consulta de suelo y actualización de animación. No presupone quién produce los offsets en una partida real.

Resultados observados: con jugador `(190,420)` y registro `(0x98=37, 0x9c=24)`, mirando a la derecha el PE crea 808 en `(227,396)`; mirando a la izquierda, en `(153,396)`. Un tercer caso con ambos offsets negativos confirma que el signo del facing afecta solo el offset horizontal y que el vertical se resta con signo. Los dos resultados están guardados como JSON bajo `artifacts/x86-suwako-418-spawn-*.json`.

Esto convierte la fórmula estática de la iteración 1.60 en evidencia dinámica de la aritmética real del handler. Aún no reconstruye el productor del registro ni sus valores para una partida normal, y tampoco demuestra trayectoria, colisión o daño completos del objeto 808.

## Verificación

- `tests/test_suwako_418_spawn_oracle.py` ejecuta tres casos diferenciales del handler x86.
- Suite Python completa: 25 pruebas aprobadas.
- No se recompiló el VPK: el cambio añade un oracle de referencia y no altera el runtime Vita.

## Siguiente paso

Localizar el método que enlaza el registro `Player+0x158` con el movimiento activo y extraer los offsets reales de 418. Usar esos valores en el runtime, y validar spawn, avance, aterrizaje e impactos en Vita3K.
