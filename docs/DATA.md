# DAT externos y VPK de motor

El VPK contiene el ejecutable ARM, `param.sfo` y un atlas de fuente propio. El VPK automático añade el indicador de autoprueba. No contiene sprites, escenarios, sonidos, archivos DAT ni el ejecutable de Windows.

En PS Vita colocar los archivos de la instalación del usuario aquí:

```text
ux0:data/touhou123vita/th123a.dat
ux0:data/touhou123vita/th123b.dat
ux0:data/touhou123vita/th123c.dat
```

No se necesita extracción en PC para jugar esta iteración. El runtime abre el índice de cada paquete, lo descifra con el stream de MT19937 y claves de byte, y lee solo el recurso solicitado. La prioridad es `c > b > a`. Descifra el recurso con la clave derivada de su offset. Los paquetes completos permanecen en disco; solo índices, PAT y texturas usadas se alojan en memoria.

Formatos implementados:

- DAT: índice, límites de entradas, rutas ASCII sin distinción de mayúsculas y separadores Windows/Unix.
- CV2: imágenes indexadas de 8 bits y BGRA de 24/32 bits; filas con padding.
- PAL: paletas de 16/32 bits, conversión de canales y transparencia.
- PAT v5: tablas de imágenes, secuencias, duraciones, offsets, daño, flags, cajas de cuerpo/hurt/attack y aliases. Las redefiniciones posteriores reemplazan la acción completa.

Los sprites se descifran/decodifican bajo demanda y se guardan en una caché RAM de 64 texturas. Los nombres del paquete no se usan para crear rutas de extracción en el filesystem. Los binarios malformados/truncados se rechazan. CV2 de 16 bits, payloads con `altSize` y transformaciones especiales de blend/rotación todavía requieren implementación; no se consideran cubiertos.

Validación independiente contra Shady Packer:

- Reimu: 4436 poses (duración, daño, offset y cantidades de cajas) sin diferencias.
- Cirno: 3429 poses sin diferencias.
- Sprites de prueba de Reimu y Cirno: RGBA idéntico píxel a píxel a la conversión independiente.
- Archivos indexados en la instalación 1.01: A=10625, B=49, C=609.

El reproductor actual usa poses originales de reposo, caminar, salto/caída, aterrizaje, guardia y 5A. Usa las cajas y daño de 5A de los PAT. El algoritmo de resolución de colisiones, física, reacción al golpe y selección de estados aún requieren reconstrucción contra PC. No es todavía el motor completo.
