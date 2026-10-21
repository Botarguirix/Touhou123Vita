# Iteración 2.199: cajas PAT en unidades de mundo

El resolvedor de contactos reducía entre dos las cajas PAT aunque el dibujo y la cámara usan unidades completas. El helper original `0x4640b0`, ejecutado sin sustituir instrucciones sobre el PE fijado `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`, transforma la caja local (-40,-120,80,0) en (440,-145,560,-25) para posición (480,25), y en (400,-145,520,-25) mirando a la izquierda. No interviene el zoom. Con posición fraccionaria el PE aplica ceil antes de sumar los extremos locales, también para valores negativos. La sonda reproducible es `tools/x86_box_transform_probe.py`.

`overlap` y `overlap_world` usan ahora unidades completas; el segundo aplica ese redondeo a posiciones fraccionarias. Se ajustó el ancho de separación corporal a las mismas unidades. La prueba nativa `collision_world_tests` verifica contacto/daño en ambas orientaciones, ausencia de contacto con una separación clara, independencia del zoom y separación de dos cuerpos simétricos. Esto no prueba todavía el algoritmo original completo de empuje asimétrico, restricciones en paredes, cajas rotadas o flags especiales.

Las sondas de colocación y diagnóstico también calculan cajas completas. El fixture Suika que fija al dueño en X=320 ahora deja al defensor fuera del cuerpo: con la separación antigua de 31 unidades, el empuje lo desplazaba 8 unidades antes del spawn. La referencia de RNG/spawn se conserva y el gate vuelve a confirmar (350.62018,81.13176), daño y reacción.

La corrección reveló un error del contador de impactos naturales: no observaba HP durante la actualización del comando. Ahora registra ese contacto como frame 0. Udonge conecta primero con 408:1, 800 de daño; una sonda dedicada sigue probando 409:1, 400 de daño. Ambas primeras poses tienen caja ofensiva en el PAT y fueron ejecutadas con la geometría y helper de daño originales. Eso demuestra contacto/daño de esas poses controladas, no una línea de tiempo de inputs completa del PC. El nuevo contrato guest/runner `udonge_409_contract` conserva la cobertura aérea independientemente del orden de búsqueda del inventario.

Validación: 27 pruebas Python focales aprobadas; pruebas nativas de arena/reinicio y colisión aprobadas. Vita3K SDL pasó schema46/600 con regresión 1, inicio 1, Udonge aéreo 1, Suika 623B/C, cinco sondas de objetos y cuatro rutas ofensivas por objetos. Ambos VPK pasan check_vpk.py sin errores/advertencias:

- Interactivo: 109,203 bytes; SHA-256 `07ab11910eb57d99d86705962d0ec5adc465846a9ecf923257c700b5851d3bec`.
- Auto: 109,369 bytes; SHA-256 `e1a03ed923c6e2655d05c7ef7a6d5a7fae926022f7fcdd6eb37f9a8d866be15e`.

La suite Python completa final pasó 146/146 en 110 segundos; su log se conserva en `artifacts/python-full-tests.log`. La suite C general mantiene su fallo previo del fixture Suika 530 (nivel reiniciado por el segundo bind), reproducido en `artifacts/fight-current-tests.log`; no se declara verde. No se alteró ese fixture para ocultarlo.

Pendiente próximo: migrar los objetos que aún conservan offsets/velocidades de la antigua media escala, especialmente Remilia 801. Sus cajas ya usan mundo completo, pero su spawn y movimiento todavía están reducidos; el gate actual conserva ese contrato histórico y no demuestra paridad de trayectoria. Siguen pendientes la comparación visual PC y la reconstrucción integral del resto del motor. Avance global: 27%.
