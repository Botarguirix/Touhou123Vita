# Iteración 2.77: anclajes de nubes BG36 desde constructor y renderer

El renderer x86 fija los dos pases de nube BG36 al mismo anclaje del escenario (`+0x44`, `+0x48`): el slot 2 (`clowd_l`) recibe origen local (0,0), y el slot 3 (`clowd_s`) se construye con pivote (ancho/2, alto). `t123_bg36_cloud_top_left` codifica el origen de dibujo correspondiente: `clowd_l` comienza en el anclaje y `clowd_s` queda centrada horizontalmente con su borde inferior en él. La evidencia se coteja en `00475eb0.c`, el renderer del PE desde `0x4757a0` y el helper `0x406d30`; el contrato de la prueba también fija los slots y argumentos del constructor.

La página de Vita muestra las dos nubes compuestas respecto al mismo anclaje y los torii con sus offsets medidos. La escala de nube en esa página se ajusta para diagnóstico; la cámara y la proyección de combate aún no están integradas, por lo que la captura confirma relación de pivotes/slots y presencia de recursos, no paridad visual de escena.

VPK interactivo: 93.700 bytes, SHA-256 `ad2c28c09faa489358411563eb1c95fcadb38ef8055c22f99400b4981b746536`. VPK automático: 93.866 bytes, SHA-256 `0d6a0905f6fffd4fed6d48acd540ce99a0e7a77b92a9740a6903e19ea324e222`. Vita3K SDL pasó schema46, gate de regresión y 600 cuadros; la captura fresca es [BG36](../artifacts/screenshots/stage-bg36-layout.bmp). Suite Python completa: 100/100.

Siguiente: derivar la transformación de cámara/viewport y escala exacta desde `FUN_00429440` y los argumentos del renderer BG36; integrar esas capas con el combate. Después repetir el método para BG37/BG38 y cerrar una secuencia de combate por escenario con comparación de referencia.
