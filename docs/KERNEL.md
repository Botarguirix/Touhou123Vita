# Recuperación de animación original

El kernel portable de `src/animation.c` se reconstruyó del control de poses/secuencias del ejecutable original. No es una temporización inventada para hacer que el sprite parezca moverse.

| Función | Ver1.10a | Ver1.01 |
|---|---|---|
| Avanzar un frame | `0x438c60` | `0x437d50` |
| Siguiente pose | `0x464b70` | `0x463b30` |
| Establecer pose | `0x464b50` | `0x463b10` |
| Siguiente secuencia | `0x464bf0` | `0x463bb0` |
| Refrescar frame | `0x464ae0` | `0x463aa0` |

El contador global incrementa como uint32; el contador de pose incrementa como uint16 y compara como int16 con la duración. Al terminar una pose se recarga su duración. Las secuencias no cíclicas avanzan y devuelven la terminación de la acción al regresar a la primera secuencia.

`tools/x86_animation_oracle.py` ejecuta código PE32 original en Unicorn con estado sintético. Conserva los bytes de las funciones originales; intercepta solamente el refresco de gráficos después de seleccionar el frame, que queda fuera del contrato. Compara resultado, secuencia, pose, duración y contadores con la implementación C. Incluye overflow de contadores y límites de duración.

Se probaron 2048 casos en cada referencia: 4096 comparaciones sin diferencias. Las referencias están protegidas por SHA256:

- 1.10a: `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.
- 1.01: `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`.

Esto valida el kernel de animación; no valida la máquina de estados completa de Reimu/Cirno, física, input buffering, cancelaciones o combate completo. El control de acción y física de la arena siguen siendo provisionales.

Las constantes de caminar de Reimu en 1.10a se identificaron como ±4.5, y se exportaron funciones de inicialización, inputs y física a evidencia local con Ghidra. Su adaptación completa todavía no está integrada; no se debe afirmar que caminar/saltar ya coincide con PC.
