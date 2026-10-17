# DAT externos y VPK de motor

El VPK contiene el ejecutable ARM, `param.sfo` y un atlas de fuente propio. El VPK automático añade el indicador de autoprueba. No contiene sprites, escenarios, sonidos, archivos DAT ni el ejecutable de Windows.

En PS Vita colocar los archivos de la instalación del usuario aquí:

```text
ux0:data/touhou123vita/th105a.dat
ux0:data/touhou123vita/th105b.dat
ux0:data/touhou123vita/th123a.dat
ux0:data/touhou123vita/th123b.dat
ux0:data/touhou123vita/th123c.dat
```

El runtime requiere `th123a.dat` y carga los otros cuatro archivos si están presentes. Para mostrar los 20 idle PAT también hacen falta `th105a.dat` y `th105b.dat`, que contienen recursos heredados referenciados por los PAT 12.3. La prioridad de búsqueda es `th123c > th123b > th123a > th105b > th105a`, igual al orden de montaje del ejecutable de PC. Los DAT permanecen fuera del VPK; solo índices, PAT y texturas usadas se alojan en memoria.

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

Auditoría de imágenes PAT ejecutada dentro de Vita3K con el kernel ARM: 22 PAT, 13,210 entradas de imagen, 12,444 imágenes referenciadas decodificadas, 765 sin uso por poses y una referencia faltante no ofensiva en `common`. Las 12,189 imágenes pose-referenciadas de los 20 personajes candidatos decodificaron correctamente. Ver [PAT_IMAGE_DECODE.md](PAT_IMAGE_DECODE.md); el TSV detallado queda en `artifacts/pat-image-decode.tsv` (ignorado por Git).

Para repetir en Vita3K aislada: `tools/run-pat-image-audit-vita.ps1`. Para una ejecución host, el mismo modo es `resource_probe <carpeta-dat> --pat-image-decode [salida.tsv]`; `tools/summarize_pat_image_decode.py auditoria.tsv [salida.md]` genera el resumen. La salida registra personaje, PAT, índice/nombre, referencias desde poses, usos dañinos, bpp, dimensiones y estado (`decoded`, `unreferenced`, `missing_resource`, `missing_palette` o `unsupported_or_invalid_cv2`).

Para correrla tras un build host, desde la raíz del repositorio:

```powershell
.\build-host\resource_probe.exe .\artifacts\vitafs\ux0\data\touhou123vita --pat-image-decode .\artifacts\pat-image-decode.tsv
```

El TSV no se debe agregar a Git: contiene nombres brutos de recursos de la instalación. La evidencia consolidada por personaje sí se conserva en [PAT_IMAGE_DECODE.md](PAT_IMAGE_DECODE.md); es más estricta que el manifiesto [PAT_RESOURCE_COVERAGE.md](PAT_RESOURCE_COVERAGE.md), pues mide decodificación real.

El reproductor usa poses y tiempos PAT para reposo, caminar, agacharse, salto direccional, caída, aterrizaje, guardia, reacciones básicas, ataques A de suelo/aire y la cadena 5A→5AA→5AAA→5AAAA en la demo de Reimu/Cirno. B/C registran impactos en una ruta experimental forward+B/C, pero aún falta recuperar el doble toque, move locks, cancelaciones y tiempos de la referencia. Los PAT contienen acciones dañinas específicas del personaje; el mapeo entre input, acción y objetos debe recuperarse con trazas. Se catalogaron 22 PAT con imágenes, bloques, aliases, poses y poses con daño; ver [PAT_COVERAGE.md](PAT_COVERAGE.md) y el inventario completo [RESOURCE_INVENTORY.md](RESOURCE_INVENTORY.md). Cargar el PAT no significa que todas sus poses sean alcanzables. La máquina de estados completa, física fiel, objetos/proyectiles y especiales todavía requieren reconstrucción contra PC.
