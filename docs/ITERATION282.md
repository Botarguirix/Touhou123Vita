# Iteración 2.182: cinco tiles de borde ausentes en BG36 son tolerados por el PE

El constructor BG36 `0x475eb0` invoca `0x46fe40(0x24, 0x56, 1)`. El loader común recorre exactamente 30 nombres de la cuadrícula 5×6. En los dos manifiestos locales, BG36 tiene 25 tiles base y cuatro auxiliares; faltan `0000[01][01]`, `[01][02]`, `[01][06]`, `[02][01]` y `[02][06]`.

La implementación original trata una búsqueda fallida como recurso nulo (`0x405030`: `*out=0`) y el loader de cuadrícula solo llama al dibujador si el puntero del tile no es nulo. Por ello, esos cinco huecos no interrumpen el constructor ni producen una llamada de dibujo con textura nula. Su patrón está concentrado en el borde superior izquierdo/derecho; es compatible con huecos del contorno de la escena, pero no hay evidencia suficiente para asegurar que la distribución comercial los omitiera deliberadamente. El inventario los sigue mostrando como ausentes y no crea sustitutos.

Se agregó una regresión que fija el constructor BG36, el límite de 30 iteraciones, el retorno nulo del lookup y el guard previo al dibujo; también verifica la lista exacta ausente en ambos DAT locales. Junto con los contratos BG35 y el auditor general: 10 pruebas focalizadas pasan. `git diff --check` pasa. Solo cambia la documentación/prueba; sin runtime ni VPK.

Siguiente para BG36: reproducir la apariencia del borde en la versión PC/Vita3K original y comparar captures para decidir si estos huecos forman parte del contorno previsto. Después, seguir con la composición final y colisiones/mecánicas de cada stage.
