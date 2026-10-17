# Iteración 1.10: cadencia de animación BG34 recuperada

## Evidencia de referencia

Ghidra exporta la referencia del constructor `00474f70` hacia la vtable de BG34 en `0085afa4`. La tabla asigna seis métodos, todos decompilados en `artifacts/kernel/f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e/stage-layout/`. El TSV `bg34-vtable.tsv` conserva slots y direcciones; `bg34-constructor-references.tsv` conserva la referencia de instrucción.

El slot 1 (`00473f40`) incrementa el contador de escena en el offset `+0x64` cada actualización. El slot 4 (`00473fc0`) selecciona el recurso `objectFa` con índice `((contador % 60) / 2)`, que recorre los 30 sprites en orden y mantiene cada uno por dos ticks antes de repetir el ciclo. El constructor carga una secuencia de frames; no son treinta objetos independientes. La vista de recursos reproduce el índice activo y resalta la miniatura correspondiente.

## Validación

El VPK automático pasó 600 frames en Vita3K SDL. Gate: `stage=bg34`, ambas rejillas 30/30, bitmaps 4/4, secuencia 30/30 y relación reportada `frame=floor(tick/2)` con tick dentro del ciclo de 60. En la corrida reportó tick 47/frame 23 al terminar la escena; la captura `artifacts/screenshots/stage-assets.bmp` muestra tick 48/frame 23 durante el render. Recursos del roster 20/20 y cero fallos de textura.

VPK automático: `artifacts/Touhou123Vita-stage-animation-auto.vpk`, 80,782 bytes, SHA-256 `0d2449b8d8eefdc98026e35e25745243230f0c57ae500a08b32283fe46fefb35`. Reporte fresco: `artifacts/vita3k-result.json`.

VPK interactivo para revisión: `artifacts/Touhou123Vita-stage-animation.vpk`, 80,616 bytes, SHA-256 `18ee94516e268cf396c504fcca7cb807d050e8616ad9ea81a6f37ef8234c93e`. Está abierto en la Vita3K local del proyecto (PID 15400).

## Siguiente trabajo

El índice y ritmo del ciclo ya tienen evidencia estática; aún falta recuperar la transformación de cámara y condiciones de dibujo que determinan posición/escala, además de colisiones y lógica interactiva de BG34. Después se necesita comparar capturas y ticks contra el ejecutable PC y repetir la recuperación en cada uno de los otros 23 IDs de escenario.
