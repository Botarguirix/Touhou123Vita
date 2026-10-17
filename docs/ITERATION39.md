# Iteración 1.35: contrato de ráfaga de Suwako 418

## Hallazgo del PE

La ruta del dispatcher de Suwako en `0076f3b4` no crea el objeto 808 en un único frame. El PE 1.10a, fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`, establece estas condiciones:

- El handler ajusta el campo de movimiento `+0x0f4` mientras el índice de pose `+0x140` está entre 5 y 17, ambos incluidos. Ese rango no es una condición para crear objetos.
- La creación del objeto `0x328` (808) usa por separado el contador `+0x7d0`: debe estar entre 1 y 19 y ser impar. El handler lo incrementa en cada actualización mientras se encuentra en ese rango.
- El handler incrementa el contador en uno por llamada elegible y lo vuelve a sembrar en 1 en su transición final.
- Esa resiembra ocurre en la transición cuyo frame es 10: los campos `+0x13e` y `+0x142` deben coincidir con `DI`, y `+0x140` debe valer 10. El handler llama entonces a `00464980(6)`, llama a `00487870(30)` y escribe 1 en `+0x7d0`. No atribuyo un efecto de “seleccionar secuencia” a la primera llamada: `00464980` despacha por índice mediante una tabla en `object+0x164`. La segunda función acumula un valor escalado en `object+0x5e4`; la unidad de ese valor todavía se debe resolver.
- El kernel confirma que `+0x13e` es el índice de secuencia, `+0x140` el índice de pose y `+0x142` los ticks transcurridos en esa pose (`00464bf0`, `00464b70`, `00438c60`). El valor de `DI` en esta ruta aún no se ha recuperado; el runtime relaciona la resiembra con secuencia 0/pose 10/subframe 0 como hipótesis explícita.

`tools/analyze_object_motion.py` verifica los bytes de ambas condiciones, la rama de paridad, el incremento, el frame 10, los argumentos de las llamadas y los efectos de sus helpers. Sigue faltando resolver el callback despachado por `00464980` y la escala temporal de `+0x5e4`.

## Consecuencia para el port

En esta iteración el runtime aún tenía un spawn único provisional cerca del frame 1, que no representa el contrato de ráfaga descrito arriba. El siguiente paso era conectar el contador a la transición del PAT y comprobarlo por separado antes de ajustar posición, altura, vida y daño.

## Aplicación del trabajo de Touhou75Vita

Esta iteración usa el patrón útil de ese proyecto —análisis por unidad con evidencia fija y fallo explícito si cambia el binario— sin importar su runtime ni mezclar direcciones de otro juego. La revisión de métodos y el helper diferencial de entrada ya constan en [ITERATION25.md](ITERATION25.md) y [ITERATION26.md](ITERATION26.md).

## Verificación

- `tools/analyze_object_motion.py original/th123.exe` validó los contratos contra el ejecutable local con el hash esperado, incluida la separación entre ventana de ajuste y gate de creación.
- Python: 8/8; `git diff --check` limpio. No se reconstruyó el VPK en esta iteración.

## Siguiente paso

Portar el contrato de diez creaciones y comprobarlo en una prueba aislada; después resolver coordenadas PAT, velocidad, vida, colisión y daño contra la referencia.
