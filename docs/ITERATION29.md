# Iteración 1.25: ventana de cancelación de dash definida por moveLock

## Evidencia del ejecutable

El handler de Reimu `004ae670` y el de Cirno `006fb8b0` verifican estado actual `200`, dirección hacia delante y luego comparan el frame de animación actual (`sVar1`) con `getMoveLock(0x198)` para 66B o `getMoveLock(0x1a2)` para 66C. El salto al ataque ocurre mientras `sVar1 <= moveLock`. `00489610` obtiene el valor de la tabla de locks para la acción solicitada. El PAT ya parsea esos valores en `T123Move.move_lock`.

## Cambio

`choose_b()` y `choose_c()` solo autorizan 408/418 desde dash cuando existe la entrada PAT y `animation.current_frame <= move_lock` de la acción destino. La prueba conserva el frame del dash al comparar y reinicia el frame al iniciar el ataque, como en el flujo de acción de la demo.

La elección del índice 408/418 sigue usando cobertura de hitbox/daño como fallback. La evidencia de estos handlers prueba la ventana de acción para Reimu/Cirno, no que la puntuación de variante reproduzca la selección original de todos los personajes.

## Validación

- Probe guest sintético: `move_lock=6`; frame 6 permite 66B, frame 7 lo rechaza y deja intacto el estado de dash/HP.
- Probe guest con PAT reales cargadas de Reimu y Cirno: para cada personaje y para 408/418, acepta en el `move_lock` decodificado y rechaza en `move_lock+1`.
- VitaSDK build aprobada y Vita3K SDL `status=passed`: 600 frames, `dash_gate_probe=1`, 3 dashes, B/C=1/1, 20 PAT/tarjetas, cero errores de textura.
- VPK final de esta iteración: [Touhou123Vita-real-locks.vpk](../artifacts/Touhou123Vita-real-locks.vpk), SHA-256 `cbc8c8c098f55f2d892ad48158dad7724c15c784c260471d4497831ac383633b`. Reporte fresco: `artifacts/vita3k-result.json`.
- `fight_tests` host no se ejecutó porque CMake/gcc host no están disponibles y WSL devuelve `E_ACCESSDENIED`; el mismo borde está incluido en el probe ejecutado por ARM dentro de Vita3K.

## Siguiente

Recuperar las ramas restantes de los handlers para estados de vuelo, ataques en el suelo y locks de A/B/C, y construir pruebas con PAT reales para más personajes. La comprobación de lock ahora cubre los PAT de Reimu/Cirno; falta comparar sus trazas con una corrida dinámica PC y recuperar la política de variante del dispatch original.
