# Iteración 1.71: `object+0x113` es alpha, no subframe

## Corrección del modelo

El layout local de SokuLib identifica `AnimationObject::renderInfos` en `+0x110` como `RenderInfo`: color RGBA, shader, colores, escala y rotaciones. Por tanto `object+0x113` es el byte alpha del color RGBA. La secuencia 1 en `0x788d60–0x788da8` lee ese byte, termina si es menor que 8; si no, le resta 8, reduce otros componentes de color y llega a la integración común. No hay reloj de subframe en ese offset. Las interpretaciones de Iteraciones 1.67/1.69/1.70 que llamaban a `+0x113` subframe o reloj externo quedan supersedidas.

El oracle conserva alpha devuelto entre callbacks. La versión inicial de este informe trataba `0xff` sólo como entrada controlada. En la Iteración 1.72 se ejecutó el constructor original `0x783a70`; su cadena transitiva de construcción del sprite (`4adcc0→46b7f0→4232f0→438bb0`) escribe `RenderInfo.color=0xffffffff`, confirmando alpha inicial 255 para una instancia recién construida. `0x799000` no escribe ese canal. El handler reduce alpha `255→247→...→7`; posición avanza en los primeros 31 callbacks y queda fija desde el 32, mientras `vy` continúa cambiando. Cada callback resta 0.2 de `vy` y suma 0.005 a `+0x11c/+0x120`.

Con secuencia 1 obtenida de `customData[2]`, el estado tras 32 callbacks controlados es:

- `[-20,12,1]`: `(172.7683,650.3658)`, `vy≈4.8763`, alpha 7.
- `[-30,14,1]`: `(83,676.6552)`, `vy≈5.7244`, alpha 7.

Reporte: `artifacts/x86-suwako-808-child-trajectories.json`. El alpha inicial está confirmado por constructor en Iteración 1.72; esas coordenadas siguen siendo una trayectoria controlada, pues el factory/manager completo, consulta de escenario, colisión/cajas y gestión de vida aún no corren en el harness.

## Validación

La prueba de regresión verifica `alpha=247` tras el primer callback y que x/y ya no cambian al pasar de alpha 15 a 7. Oracle enfocado y suite Python se ejecutan por separado; el runtime Vita permanece sin cambio hasta cerrar creación, colisión y vida del objeto.
