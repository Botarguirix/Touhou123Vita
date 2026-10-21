# Iteración 2.131: Suika 623B nivel 9 crea y conecta el burst PAT 821

Se portó al combate el efecto de Suika 623B nivel 9. El probe x86 ahora correlaciona el evento con el update 20 de la acción 530, transición a pose 7. Ahí la rutina original solicita el objeto `0x335`, cuyo factory crea PAT 821/seq.0. La llamada ejecuta cuatro rangos de la MT19937 original: `60→48`, `5→0`, `5→4`, `360→300`. La implementación Vita replica MT19937 y el divisor de rangos del PE, calcula el spawn mediante los argumentos PAT y mantiene activa la caja authored durante el update de creación; el objeto tiene vida 1 y alpha 0, como el estado observado en el probe.

La prueba x86 verifica pose, frame, llamadas aleatorias, parámetros del factory, anchor y coordenadas. La prueba C ejecuta el comando 623B, espera la transición PAT y comprueba creación/impacto. Vita3K SDL pasó schema 46 y 600 cuadros: máscara 623B `63`, una instancia 821, daño `800` y coordenadas `(350.62018,81.13176)` en el fixture integrado. También pasó el resto de regresiones de combate, objetos, sprites y escenarios. Los contratos C pasaron 10/10 y la suite Python pasó 115/115.

VPK reconstruidos:

- Interactivo: `artifacts/Touhou123Vita-suika623b-burst.vpk`, SHA-256 `C9A6DF8E060549840B46CF8D3704F8408283C65C3D2F45D780EDEF38478A89A7`.
- Autotest: `artifacts/Touhou123Vita-suika623b-burst-auto.vpk`, SHA-256 `EA4BE5D75826BC628EDD150EF43959632178487346A3A8FD831B98770DDB38E6`.
- Evidencia guest fresca: `artifacts/vita3k-result.json`, status `passed`, schema 46, 600 frames.

El combate de esta prueba mantiene al defensor en el área del spawn para verificar la conexión; no afirma que el alcance acierte a un rival móvil durante una partida natural. El RNG se inicializa con 5489 en el estado aislado de `Fight`, que reproduce la primera secuencia del PE. El juego original tiene una secuencia MT global y otros consumidores todavía no portados, por lo que queda pendiente compartir su avance global cuando se integren más efectos aleatorios. La paridad completa de roster, cartas, mecánicas de escenario y replays sigue abierta.
