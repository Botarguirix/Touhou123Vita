# Iteración 2.78: evidencia acumulada de las nubes BG36

La prueba automática de la iteración anterior mostraba ambas nubes en la captura fresca, pero el gate final informaba cero proyecciones. La causa era que la navegación reiniciaba el contador diagnóstico cada vez que se volvía a entrar en BG36, después de haber tomado la captura. Se eliminó ese reinicio para que la evidencia de renderizado permanezca acumulada durante la corrida; la inicialización del scroll y sus ticks sí se reinician al entrar al escenario.

Verificación: el contrato focalizado pasó 2/2; el VPK automático completó schema46 y 600 cuadros en Vita3K SDL con `regression_gate=1` y `stage_bg36_cloud_quads_projected=4`; la suite Python completa pasó 100/100. Se generó también el VPK interactivo sin `auto-test.txt`. Su `eboot.bin` coincide byte por byte (SHA-256 `6f0a8c382007c17bb9d1f6b841bc176627a5f9427bae82d23ee7f0e38a0981a`) con el binario que pasó Vita3K.

VPK automático probado: SHA-256 `273b0adf95fc51cc641ed4c3fd8c57e6ddfc1537427b640f3960cd3e3585503c`. VPK interactivo: SHA-256 `9f255debb4a27f64869e3f7ec0a0298d7b7f608d36257482d5f9d89a65e69f57`. La captura fresca [BG36](../artifacts/screenshots/stage-bg36-layout.bmp) conserva los torii y las dos nubes del visor. Esta validación cubre el contrato de proyección en el visor; no demuestra todavía cámara viva ni composición BG36 integrada al combate.

Siguiente: resolver cámara/proyección de escenario con el renderer x86 y reutilizar la transformación en el combate; extender una verificación equivalente a BG37/BG38 y cerrar escenarios en una ronda jugable.
