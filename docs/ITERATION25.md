# Iteración 1.21: revisión de Touhou75Vita y matcher C inicial

Esta página conserva el estado de cierre de esa iteración; la integración y validación diferencial posteriores están en [ITERATION26.md](ITERATION26.md).

## Qué encontré en el otro proyecto

Revisé el chat **Configurar Touhou75Vita** y el estado del repositorio `Botarguirix/Touhou75Vita`. Incluye herramientas para proponer límites de funciones, extraer llamadas/ramas, aproximar CFG y reachability, contar instrucciones, levantar una representación intermedia y generar C semántico. También tiene un runtime pequeño de registros/memoria virtual y un smoke test host.

El alcance observado es importante: el VPK de ese repo solo reconoce los encabezados PE32 del ejecutable/parche de Touhou 7.5 y escribe un log. Su prueba host confirma algunos contratos de registros/stack/globales, no carga ni juega TH075. La compilación Vita quedó pendiente en aquel entorno porque el proxy devolvía HTTP 403 durante la instalación de VitaSDK.

## Qué adoptamos aquí

- Registrar hashes/versiones de cada binario y producir evidencia reproducible por función y opcode.
- Hacer lifting en verticales pequeñas, con lista explícita de instrucciones/imports no soportados y fixtures comparadas contra el x86 original.
- Mantener smoke tests host separados de pruebas en Vita3K y evitar confundir que un VPK abre con paridad de juego.
- Usar el análisis TH075 para proponer preguntas sobre estructuras comunes; volver a demostrar cada respuesta sobre `th123.exe`.

No compartí direcciones entre los ejecutables ni copié código. El repositorio consultado no declara una licencia clara en la raíz revisada; aclararla sería requisito antes de reutilizar código fuente.

## Trabajo aplicado al matcher de TH123

El oráculo x86 pasó 17/17 vectores sintéticos, incluidos `X` para A/B/C/D. Añadí `T123InputHistory`, un buffer circular de 90 muestras, traducción de tokens y un matcher C independiente del combate en [input.c](../src/input.c), junto con contratos en [input_tests.c](../tests/input_tests.c). El compilador VitaSDK acepta ambas unidades con `-Wall -Wextra -Werror`.

Este helper es un primer port experimental, no paridad establecida: los tests C aún no se ejecutaron como programa host ni se compararon automáticamente vector a vector contra el oráculo. El matcher no está integrado al dispatch de combate y el dash de la demo no cambió. Tampoco se empaquetó VPK.

## Siguiente paso

Conseguir una ejecución de tests host disponible y ajustar una exportación común de los vectores para que C y el x86 se prueben con exactamente los mismos casos. Después trazar entradas reales del productor `0046d5d0`, cubrir direcciones diagonales/botones sostenidos y replays, y solo entonces reemplazar el gate aproximado del dash.
