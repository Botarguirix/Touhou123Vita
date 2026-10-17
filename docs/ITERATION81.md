# Iteración 1.81: consumidores de cajas y fases de pares

## Hallazgo estático en el PE fijado

La lectura del manager resuelve parte del camino que faltaba después de sincronizar `BoxInfo`. En `0x47d5c9` llama `0x47cb70` y en `0x47d5d0` llama `0x47ce20` para procesar fases de pares del objeto manager. La segunda recorre objetos candidatos y despacha a `0x47ca70` o `0x47c990` según la clase/flags del par.

El helper `0x47a5b0` contiene la comparación de cajas ofensivas contra defensivas: usa el conteo hit en `object+0x1cb`, hit boxes en `+0x220` y punteros auxiliares/rotados desde `+0x320`; el otro objeto aporta hurt count `+0x1cc`, hurt boxes `+0x1d0` y punteros rotados desde `+0x334`. Cada pareja toma la prueba rotada `0x47a110` cuando hay un puntero alternativo o la prueba axis-aligned `0x479e10` en el caso directo. `0x47a740` recorre hurt boxes contra hurt boxes con los mismos predicados de forma.

Los bytes exactos de dispatch, conteos, arrays y llamadas de prueba se validan desde `tools/analyze_object_motion.py`; el test `tests/test_object_motion_analysis.py` comprueba que el reporte conserva ese contrato para el EXE con SHA-256 fijado.

## Límites de la evidencia

Esto identifica consumidores y filtros de parejas, no demuestra todavía qué pareja alcanza una pelea natural de Suwako 808. Tampoco establece por sí solo el orden de prioridad entre daño, guardia, invulnerabilidad, hitstop, cancelación y destrucción de objetos. El helper `0x47a110` hace pruebas geométricas y deriva respuesta/penetración; hay que ejecutar la ruta con dos GameObjects válidos y observar la cadena siguiente para identificar el efecto de combate.

El action 808 seq.0 sí publica una hit box desde PAT; seq.1 declara daño 150 en PAT, pero no contiene cajas de ataque/hurt explícitas. Falta seguir su trayectoria real de frames para averiguar si la interacción usa otros datos, callbacks o estado heredado del objeto.

## Siguiente prueba diferencial

Preparar dos objetos con lista/handle válidos y poses cuyos bounds se toquen y se separen por un píxel. Ejecutar el manager desde su fase de pares bajo Unicorn, guardar las llamadas a `0x47a5b0/0x47a740`, `0x47a110/0x479e10` y la rutina de respuesta que siga al primer hit. Repetir con hitbox PAT 808 seq.0 y con el objeto recién creado en seq.1. Capturar frame, flags, daño, guard, hitstop, y razón de retiro. No cambiar el runtime Vita hasta que estos resultados puedan expresarse como contrato reproducible.

No se modificó el runtime ni el VPK. La suite Python integral previa a esta iteración fue 37/37; el contrato nuevo debe pasar la misma suite antes de integrar.
