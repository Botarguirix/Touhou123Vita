# Iteración 1.1: auditoría de versiones PAT y rutas idle

## Resultado

Se añadió `resource_probe --pat-archive-idle`, que decodifica cada PAT directamente desde cada DAT y compara las imágenes de la acción idle con las rutas CV2 literales de los tres índices. Esto evita que la prioridad C>B>A oculte diferencias entre revisiones.

El manifest contiene 42 versiones PAT de personaje entre DAT A y C. Los PAT repetidos sí cambian de tamaño/contenido; por ejemplo Sakuya ocupa 629,815 bytes en A y 628,237 en C. El sondeo cubrió 446 poses idle: 18 revisiones no encuentran ningún CV2 idle en las rutas declaradas, 4 encuentran solo parte y 19 encuentran todas sus referencias. Sakuya, Youmu, Remilia, Yuyuko, Udonge, Aya, Komachi, Iku y Tenshi carecen de esas rutas en ambas revisiones. La auditoría está guardada en `artifacts/pat-archive-idle.tsv`.

Se confirmó además que los espacios dentro de nombres como `data/character/reimu/stand002 .cv2` son literales en el índice del DAT. Se conserva el nombre tal cual lo declara PAT; eliminar el espacio reduce la cantidad de texturas decodificadas y es incorrecto. El contrato PAT ahora protege este comportamiento.

## Validación

- Host: compilación y 8/8 pruebas aprobadas, incluidos oráculos x86 y contratos de formato.
- VitaSDK: VPK interactivo creado mediante `tools/build-vita-temp.sh`, que compila desde `/tmp` para evitar el fallo del empaquetador VitaSDK con rutas Windows que contienen espacios.
- Vita3K aislado: el guest completó 600 frames, menú, práctica, pelea y salto; cargó 20/20 PAT y tarjetas, 11/20 sprites idle, 93 texturas, `A=3`, `B=0`, `C=0`, CPU 9600/10000 HP, 7 DAT, digest `2562787365` y salida guest 0. La gate integral sigue fallando por cobertura de sprites y entradas B/C.
- VPK: `artifacts/Touhou123Vita-iter11.vpk`, SHA-256 `282eb8d9149673ba909c925c82a0843ad822aa500030a3399f1751b0f4566309`.

## Siguiente diagnóstico

Los PAT de A y C conservan referencias idle a nombres que no existen bajo esas rutas, así que el problema no se resuelve cambiando la prioridad entre archivos. El siguiente paso es exportar con Ghidra el loader de imagen y su caller de animación para recuperar la ruta de búsqueda, transformaciones de nombre y posible atlas compartido. Después se puede implementar el resolver y exigir que cada pose cuente solo cuando el recurso real se localiza y se decodifica.
