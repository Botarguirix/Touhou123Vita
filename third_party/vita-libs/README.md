# Dependencias nativas para Vita (T4)

Este directorio contiene únicamente el constructor y una prueba propia. Los fuentes
de terceros, cabeceras instaladas, licencias, bibliotecas y ejecutables se generan
en `artifacts/vita-libs/`, ignorado por git. No se instala nada en `C:\vitasdk`.

## Identidad del PE y versiones

El constructor exige el SHA-256
`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`
antes de analizar el ejecutable. Guarda la evidencia en `pe-evidence.json`.
Las direcciones siguientes son VA del PE en su base `0x00400000`.

| Biblioteca | Evidencia medida | Conclusión y confianza |
|---|---|---|
| zlib | `deflate 1.2.3 Copyright 1995-2005 Jean-loup Gailly` en `0x00861be9`; `inflate 1.2.3 Copyright 1995-2005 Mark Adler` en `0x008651e9` | Versión **1.2.3**, alta |
| libpng | `1.2.5` en `0x00865368`, seguida del diagnóstico `Application built with libpng-%.20s but running with %.20s` en `0x00865370` | Versión **1.2.5**, alta |
| libvorbis | Firma `vorbis` en `0x00885af0`; tabla `FLOOR1_fromdB_LOOKUP` de 1024 bytes en `0x00893ac8` | Familia del decodificador de referencia, alta; release exacta **no identificada** |
| libogg | Tabla `crc_lookup` de 1024 bytes en `0x008965f0` | Coincidencia con libogg, media por sí sola; release exacta **no identificada** |

No se encontró `Xiph.Org` ni `libVorbis` en ASCII, ni `Xiph.Org` en UTF-16LE.
La ausencia es compatible con haber enlazado únicamente rutas de decodificación;
eso es una inferencia, no una demostración de las opciones del enlazador.

Se compararon los 1024 bytes completos de las tablas con releases oficiales:

| Tabla | Candidatos comparados | SHA-256 de la tabla; resultado |
|---|---|---|
| `FLOOR1_fromdB_LOOKUP` | libvorbis 1.0.1, 1.1.0, 1.1.2, 1.2.0, 1.3.2 | `3d48051a5d8e88104ebe447e328147ebbffa53e8b8e907878b77739ac5dc4b7d`; todos coinciden |
| `crc_lookup` | libogg 1.0, 1.1, 1.1.2, 1.1.3, 1.2.0, 1.2.2 | `0053f121cdcaf9f510a940ba891fb2bccd41487953c5a4c0048c4a3ccdec782e`; todos coinciden |

Estos resultados no permiten preferir una release. La mejor estimación respaldada
es la **familia Vorbis I/libogg de referencia**, sin número exacto. El constructor
fija **libvorbis 1.1.2 + libogg 1.1.3 como base provisional para desarrollar las
llamadas nativas**: Xiph los publicó juntos en [su anuncio de noviembre de 2005](https://lists.xiph.org/pipermail/vorbis/2005-November/026129.html).
Esa elección no afirma identidad con el PE ni una ABI binaria compatible.
La comparación local adicional quedó en `audio-fingerprints.json`; el constructor
repite la comparación de las dos tablas de la base provisional con el PE.

## Fuentes oficiales y hashes fijados

| Paquete | Tarball oficial | SHA-256 |
|---|---|---|
| zlib 1.2.3 | [zlib.net/fossils/zlib-1.2.3.tar.gz](https://zlib.net/fossils/zlib-1.2.3.tar.gz) | `1795c7d067a43174113fdf03447532f373e1c6c57c08d61d9e4e9be5e244b05e` |
| libpng 1.2.5 | [tag v1.2.5 de pnggroup/libpng](https://codeload.github.com/pnggroup/libpng/tar.gz/refs/tags/v1.2.5) | `58ec845f95ff351c8a25bfbfa667a8f3924bb0f1a1ec572cc7e09b8817204d1e` |
| libogg 1.1.3 | [downloads.xiph.org/releases/ogg/libogg-1.1.3.tar.gz](https://downloads.xiph.org/releases/ogg/libogg-1.1.3.tar.gz) | `bae29e79fbc50bbedf1235852094b71c8c910a1ef0cd42fe4163b7b545630b65` |
| libvorbis 1.1.2 | [downloads.xiph.org/releases/vorbis/libvorbis-1.1.2.tar.gz](https://downloads.xiph.org/releases/vorbis/libvorbis-1.1.2.tar.gz) | `3f7135ccbda589c251017912f5f5ec9da626c976d2376bcfda19ad6b9c4a6050` |

Los hashes se midieron sobre los archivos descargados por HTTPS y están fijados
en el script; no se presentan como firmas independientes del editor. Se rechaza
un archivo distinto antes de extraerlo o ejecutar código de compilación.

[pnggroup/libpng es el repositorio oficial](https://github.com/pnggroup/libpng).
El tarball del tag contiene los fuentes de la versión 1.2.5; **no es el tarball
original publicado en 2002**. Se usa porque el enlace de SourceForge y los mirrors
consultados devolvieron HTML en este entorno. Su hash corresponde al archivo de
GitHub, que tiene un tamaño de 512039 bytes.

## Construcción reproducible en Windows

Requiere PowerShell 7, `tar` y VitaSDK. No requiere WSL, MSYS, autotools, CMake
ni nuevas dependencias Python. La prueba de host opcional requiere MinGW GCC.

```powershell
$env:VITASDK = 'C:\vitasdk'
./third_party/vita-libs/build.ps1
# Reusar descargas verificadas y ejecutar también la misma prueba en PC:
./third_party/vita-libs/build.ps1 -Offline -HostSmoke
```

`-Executable` permite indicar otro lugar para la copia del usuario; siempre se
exige el mismo hash. `-OutputDirectory` permite separar los resultados y cachés.
`-Offline` falla si falta algún tarball. Si un hash no coincide, se debe revisar
la descarga; el script no actualiza hashes ni sustituye versiones automáticamente.

Se compilan las listas explícitas de fuentes de los Makefiles oficiales como
archivos estáticos. Se genera `ogg/config_types.h` con enteros de 16/32/64 bits,
que normalmente produciría `configure`. Se desactiva ensamblador x86 de libpng
y se usan `-std=gnu11 -O2 -fno-strict-aliasing -ffp-contract=off`.
El archivador recibe `rcsD` para no guardar marcas de tiempo. El script devuelve
un error ante un fallo de compilación, enlace, conversión SELF o prueba de host.
La ejecución host tiene un límite de 30 segundos; si Windows deja el proceso
esperando un diálogo de error, el constructor termina únicamente ese proceso
propio y falla. Sus stdout/stderr se conservan en `host/smoke-result.txt` y
`host/smoke-error.txt`.

Salidas:

- `downloads/`, `src/`: caché verificada y fuentes originales extraídos.
- `include/`, `lib/`, `licenses/`: cabeceras, seis bibliotecas y licencias.
- `smoke.elf`, `smoke.velf`, `smoke.self`: ejecutable ARM y SELF.
- `pe-evidence.json`, `build-manifest.json`: versiones, evidencia, compilador,
  tamaños, hashes y estado de ejecución, sin marcas de tiempo.
- `host/smoke.exe`, `host/smoke-result.txt`: prueba de host si se solicita.

El futuro runtime debe incluir estas cabeceras al compilar sus adaptadores y
enlazar `-lvorbisfile -lvorbisenc -lvorbis -logg -lpng -lz -lm` desde `lib/`.
El motor solo necesitará `libvorbisenc` si codifica audio; aquí se construye para
generar datos propios durante la prueba. Estas bibliotecas no aceptan directamente
estructuras u objetos del guest x86: sigue pendiente adaptar punteros, callbacks,
estado y asignación de memoria en la capa de recompilación.

## Prueba de humo y alcance

`smoke_test.c` genera todos sus datos en memoria y comprueba:

1. zlib: versión real 1.2.3, compresión/descompresión de 4096 bytes exactos y
   rechazo de un checksum adulterado.
2. libpng: versión real 1.2.5, escritura y lectura de un PNG RGBA 2×2, dimensiones,
   tamaño de fila y los 16 bytes de color/alfa originales.
3. libvorbis/libogg: vendor real generado por la biblioteca
   `Xiph.Org libVorbis I 20050304`, codificación de una señal propia, encapsulado
   Ogg y decodificación mediante libvorbisfile de exactamente 1024 muestras mono
   a 8000 Hz, todas finitas y con energía distinta de cero.

libvorbis 1.1.2 no declara `vorbis_version_string()`. Por eso se consulta el
vendor generado por `vorbis_analysis_headerout()`, en vez de inventar esa función
o limitarse a imprimir un macro del constructor. Ese vendor también aparece en
otras releases y no identifica por sí solo la versión del PE.

Esta versión llama a `seek_func` al abrir incluso un flujo no posicionable y a
`close_func` desde `ov_clear`. Las ejecuciones con callbacks nulos fallaron; GDB
confirmó llamadas a dirección cero desde `_ov_open1` y `ov_clear`. La prueba
proporciona los cuatro callbacks: seek devuelve -1, tell devuelve la posición y
close marca el cierre de la memoria. Se comprueban `ov_seekable()==0` y el cierre
efectivo; no se modifica el código de libvorbisfile para ocultar los fallos.

En Vita la prueba reserva 16 MiB para newlib y escribe el resultado en
`ux0:data/touhou123vita/vita-libs-smoke.txt`; código de salida 0 indica éxito.
No necesita recursos del juego, shaders ni plugins adicionales.

### Resultado de la verificación

Comando ejecutado: `./third_party/vita-libs/build.ps1 -VitaSDK C:\vitasdk -Offline -HostSmoke`.
**Pasó, código 0**: los cuatro tarballs verificaron SHA-256, las seis bibliotecas
ARM compilaron y la prueba host imprimió `PASS vita-libs smoke`. Compilador:
`arm-vita-eabi-gcc` 15.2.0. `readelf -h smoke.elf` confirmó ELF32, ARM,
EABI5 y hard-float ABI.

| Biblioteca ARM | Bytes | SHA-256 |
|---|---:|---|
| `libz.a` | 80 116 | `92ae92c1f64868ca0b8110a00e10c4cd659f10bb8256e9794c3dbf95d5e91b35` |
| `libpng.a` | 207 276 | `175ea61d13bf9d1854224901a58a5454dd63cc9992f65e9e6777adf9ce11b50f` |
| `libogg.a` | 20 598 | `b2d036bc588fa929c425fc7ae355fa604b27aed6ca701d2d5a8946031acf83d4` |
| `libvorbis.a` | 186 278 | `05d642150dae1d25d9a3d5e76028f3a416d0d2e361848402367c297b31c74803` |
| `libvorbisfile.a` | 24 624 | `fe1220ecbaf2fb28eefd7c6b952ec1e2c65385e9d637c45ee2c34e39a966c545` |
| `libvorbisenc.a` | 1 478 394 | `b45281ec244cfd649e7b9cf4dab94c73aadc4c0ffae172ea0103e2b78e4f6365` |

El SELF final ocupa **316 653 bytes**, SHA-256
`4e059e2ad42f6c7128d76f268cdc3f42634876c472fec7074093873795849f54`.
El resultado host verifica 4096 bytes zlib, los 16 bytes del PNG RGBA generado
(82 bytes comprimidos), el vendor real del encoder y 1024 muestras de audio
decodificado con energía no nula. Los registros están en `build-final.log`,
`build-manifest.json` y `host/smoke-result.txt` bajo la salida local ignorada.

También pasaron dos sondas negativas: se rechazó un PE de cuatro bytes antes
de analizarlo y un tarball adulterado antes de extraerlo. `git diff --check`
pasó. Las ejecuciones iniciales con callbacks nulos fallaron, como se explica
arriba; el resultado anterior corresponde al código corregido.

El SELF no se ha ejecutado todavía en Vita3K ni en Vita física; pasar el humo
en PC no prueba equivalencia de audio frente al ejecutable original ni la
ejecución correcta en ARM. Las versiones exactas de audio siguen sin resolverse;
también quedan pendientes los adaptadores guest/host y su integración en el motor.
