# Iteración 1.24: selección de variantes PAT de ataques de dash

## Cambio

La entrada del dash B/C ya usa la variante PAT devuelta por `t123_pattern_best_attack()` para las acciones 408/418. Antes el combate prefería el índice cero y solo avanzaba al primer índice con hitbox si la base era placeholder. Ahora compara las variantes presentes y prefiere la que tiene mayor suma de `daño × número de hitboxes` en sus poses. Si no hay variante dañina, conserva el índice cero.

Este criterio aprovecha datos reales del PAT, pero aún es una política de fallback de la demo. La referencia local no ha confirmado que el motor seleccione índices con esa puntuación; los objetos, condiciones de ruta y move locks por personaje siguen sin reconstruirse. No se presenta como selector fiel.

## Verificación

- Agregué un probe al VPK que crea tres variantes 408: índice 0 sin hitbox, índice 1 con daño 100 e índice 2 con daño 250. Ejecuta la secuencia de dash y B, exige índice 2, una colisión y 250 puntos aplicados.
- Compilación VitaSDK aprobada.
- Vita3K SDL: `status=passed`, 600 frames, `dash_gate_probe=1`, 3 dashes, B/C=1/1, 20 PAT/tarjetas y cero errores de textura. Reporte fresco: `artifacts/vita3k-result.json`.
- VPK: [Touhou123Vita-attack-variant.vpk](../artifacts/Touhou123Vita-attack-variant.vpk), SHA-256 `7bf586ab0bfd246220a16fd83fc4316c6245cec2ab369154338c249726448ce7`.
- La suite host no corrió: no hay compilador host/CMake ejecutable en Windows y WSL devuelve `E_ACCESSDENIED`. El probe equivalente se ejecutó dentro del guest ARM en Vita3K.

## Próximo trabajo

Recuperar del dispatcher x86 cómo se elige cada índice 408/418, cuándo se instancian objetos y qué locks/cancelaciones autorizan el ataque. Después ampliar las pruebas con PAT reales para el elenco entero y contrastar trazas por frame contra PC; la puntuación local no debe sustituir esa evidencia.
