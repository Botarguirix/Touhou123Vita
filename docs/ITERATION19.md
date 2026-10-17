# Iteración 1.15: productor y bloques del historial de input

## Evidencia estática

Un barrido Capstone del PE 1.10a, SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`, encontró las referencias al ring del jugador. `0046c43d–0046c455` inicializa `this+0x7b0`; `0046cc90` lo consulta; `0046d78f` agrega el estado actual. El helper genérico `0042cf90` escribe una muestra de 16 bits al final de `start + count` y aumenta count. Reserva bloques de `0x10` bytes, por lo que cada bloque almacena 8 palabras. `0046d79d–0046d7bd` avanza el inicio circular y reduce count después del append.

La palabra de estado se arma antes, en `0046d5f0–0046d69b`, a partir de flags de botones y direcciones derivados de campos del jugador. El comparador `0046cc90` lee el byte bajo para dirección y botones, y aplica máscaras por token. No se inventó una equivalencia de bits con controles físicos todavía.

Dump focalizado: `artifacts/kernel/<sha>/input-state/ring-writer.capstone.txt`. La búsqueda de offsets está en `ring-field-refs.txt`; su barrido lineal produce candidatos falsos y solo se tomaron como evidencia los bloques de código confirmados en contexto.

## Estado y siguiente trabajo

Queda por resolver cómo se inicializa/repone `count` y por qué se reduce después de cada actualización. El campo `this+0x104` se identificó después como `AnimationObject::direction`, cuyo signo selecciona la numeración numpad relativa ([fuente de layout](https://github.com/SokuDev/SokuLib/blob/master/src/AnimationObject.hpp#L17-L25)); ese hallazgo se registra en el estado actual de [INPUT_STATE.md](INPUT_STATE.md). El código Vita mantiene todavía el gate aproximado de doble toque, así que no se recompiló un VPK en esta iteración: no hubo cambio de runtime. Al continuar, se identificó `0046d5d0` como la ruta de update de entrada y `0046d050` como rutina genérica de deque; véase [ITERATION21.md](ITERATION21.md). El análisis futuro debe explicar la inicialización y el conteo antes de implementar el ring portable.
