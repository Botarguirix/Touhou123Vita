# T8: glifos GDI sobre FreeType

Se entregan `recomp/host/glyph.h` y `glyph.c` con la interfaz solicitada. No se
modifican `other.c`, `win32.h` ni el build: Claude debe conectar CreateFont,
GetGlyphOutline y la conversión CP932 de T7 al integrar. El módulo no usa Win32
ni almacenamiento local de hilo. FreeType y la caché global se protegen con un
mutex pthread, incluida la sustitución de fuente mediante glyph_init.

## Fuente y procedencia

Elegida **Noto Sans Mono CJK JP Regular**, SIL OFL 1.1. Mantiene avance de medio
em para ASCII y de un em para japonés; esto es preferible al ASCII proporcional
para sustituir MS Gothic. No garantiza métricas ni píxeles idénticos.

- Repositorio oficial: https://github.com/notofonts/noto-cjk
- Commit fijado: `f8d157532fbfaeda587e826d4cd5b21a49186f7c`.
- Archivo: `Sans/Mono/NotoSansMonoCJKjp-Regular.otf`, 16 424 156 bytes.
- SHA-256: `4d01725be822d144cf9a56ade981e6fb920cd7a610b8fc24cc601a920beea5b9`.
- Licencia: `Sans/LICENSE`, SHA-256 `6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2`.

`python tools/fetch_font.py` descarga ambos a `local/fonts/`; `--check` verifica
sin red. Una copia alterada falla en lugar de sustituirse automáticamente. Los
hashes se midieron sobre la descarga oficial HTTPS, no son firmas del editor.
La fuente y licencia descargadas no se añaden a git. Al distribuir la fuente,
acompañar la licencia OFL; no sustituirla por MS Gothic en un paquete público.

## Contrato y rasterización

- Altura negativa: tamaño nominal/em (FT_SIZE_REQUEST_TYPE_NOMINAL).
- Altura positiva: ascender menos descender (FT_SIZE_REQUEST_TYPE_REAL_DIM),
  la aproximación de celda de esta fuente; altura cero usa 16 por decisión
  explícita del módulo, no reproduce el default dependiente del dispositivo GDI.
- Se conserva el signo en la clave; se rechazan alturas fuera de -4096..4096.
- Peso >=600: FT_GlyphSlot_Embolden antes de renderizar. Se conservan sus avances.
- Render gris normal sin bitmaps embebidos. Cobertura: `(c*16+127)/255`, de 0..16.
- Filas superiores primero, pitch `(width+3)&~3`; padding cero.
- GLYPHMETRICS: caja del bitmap, bitmap_left/top y avances redondeados a píxeles.
- Consulta con buf nulo o size cero: devuelve tamaño y métricas. Buffer corto:
  UINT32_MAX, sin escritura parcial. Espacio: cero bytes, avance válido.
- Sin fuente o argumentos inválidos: UINT32_MAX. Surrogates aislados se rechazan.
  Un carácter BMP ausente usa el glifo .notdef de la fuente.

Referencias primarias: [altura de CreateFontA](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-createfonta),
[modelos de tamaño FreeType](https://freetype.org/freetype2/docs/reference/ft2-sizing_and_scaling.html),
[síntesis de negrita](https://freetype.org/freetype2/docs/reference/ft2-synthesis.html).

## Métricas medidas frente a MS Gothic

T5 midió argumentos y transformaciones del juego con métricas GDI sintéticas;
**no había medido la fuente Windows real**. T8 añade una medida GDI real local:
CreateFontW con charset 128, calidad 2 y peso 400; GetTextFaceW confirmó
`MS Gothic`, sin sustitución. Resultados en `artifacts/t8-gdi-metrics.json`.
Noto tiene units_per_EM=1000, ascender=1160, descender=-288.

| Altura | Glifo | MS Gothic caja / avance X | Noto caja / avance X |
|---:|---|---|---|
| 14 | A | 7x11 / 7 | 5x8 / 5 |
| 14 | espacio | 1x1, 0 bytes / 7 | 0x0, 0 bytes / 5 |
| 14 | U+6F22 | 13x14 / 14 | 10x12 / 10 |
| 24 | A | 12x19 / 12 | 8x13 / 8 |
| 24 | espacio | 1x1, 0 bytes / 12 | 0x0, 0 bytes / 8 |
| 24 | U+6F22 | 22x23 / 24 | 16x17 / 17 |
| -17 | A | 9x13 / 9 | 9x13 / 9 |
| -17 | espacio | 1x1, 0 bytes / 9 | 0x0, 0 bytes / 9 |
| -17 | U+6F22 | 15x16 / 18 | 17x17 / 17 |

Las celdas positivas de Noto son sensiblemente menores por su relación
ascender/descender frente al em. **No afirmar compatibilidad visual exacta**.
Recomiendo Mono como fuente libre de arranque; la integración debe evaluar un
ajuste de descriptores/avances, o conservar una caché GDI local como oráculo de
paridad. No se altera silenciosamente la semántica de altura dentro del módulo.

## Caché y memoria

LRU por (altura, peso, código), hasta 4096 entradas y 8 MiB de metadatos más
máscaras. Se invalida tras un glyph_init correcto; un init fallido conserva la
fuente y caché previas. El tamaño no incluye overhead de malloc, estructuras
internas de FreeType, fuente, mutex ni stacks. La rasterización temporal de una
entrada nueva puede preceder al desalojo y aumentar el pico sobre el límite.

Para medir **los 2000 kanji de mayor frecuencia de KANJIDIC2**, se ordenó el campo
freq de [KANJIDIC2 oficial](https://www.edrdg.org/kanjidic/kanjidic2.xml.gz) y se
seleccionaron los primeros 2000 (de 2501 con rango). La descarga gzip midió
1 488 582 bytes, SHA-256 `42db060b56231dec632f8b9f8805738559fab9724f347a16db7299deac2e6414`.
El conjunto queda solo en `artifacts/t8-common-kanji.txt`; no se incorpora al repo.
No es una frecuencia medida sobre los diálogos del juego.

A altura +24 y peso 400: **587 176 bytes de máscaras** y **683 176 bytes en la
caché host** (2000 entradas de 48 bytes). En ARM sizeof(Entry) se espera 40 por
sus punteros de 32 bits: estimación 667 176 bytes, pendiente de medir al ejecutar.
No multiplicar este número por todas las alturas sin aplicar el límite LRU.

## Dependencias y verificación

PC: FreeType está instalado en `C:/msys64/ucrt64` (pkg-config freetype2 informa
26.6.20, versión de interfaz libtool; no se presenta como release del motor).
En MSYS2 UCRT64 se instala con `pacman -S mingw-w64-ucrt-x86_64-freetype`.
Enlazar `-lfreetype -lpthread` y añadir include/freetype2.

VitaSDK: no se encontró libfreetype.a ni sus cabeceras. Instalar el paquete
freetype mediante vdpm según la distribución VitaSDK utilizada; no se vendoriza.
**El objeto ARM sí compiló** usando las cabeceras públicas FreeType de PC:

```powershell
python tools/fetch_font.py --check
python -m unittest tests.test_glyph -v
C:/vitasdk/bin/arm-vita-eabi-gcc.exe -std=gnu11 -O1 -Wall -Wextra -Werror -I C:/msys64/ucrt64/include/freetype2 -c recomp/host/glyph.c -o artifacts/t8-glyph-arm.o
```

Resultado: **4 pruebas, OK**; comprobación de hashes y compilación ARM pasaron.
Las pruebas verifican los dos pasos, padding, coberturas, límites de buffer,
espacio, kanji, negrita, cuatro hilos, cache hit, invalidación y desalojo.
La ausencia de GCC, FreeType o fuente salta solo las pruebas de rasterización.
El harness compilado con T123_GLYPH_TEST permite los modos metrics, measure e
image; sus contadores adicionales no forman parte de la interfaz de producción.

Imagen propia renderizada y revisada: `artifacts/t8-glyphs.png`, desde el PGM
producido por `glyph_harness ... image artifacts/t8-glyphs.pgm`. No contiene texto
ni imágenes del juego. No se enlazó FreeType para ARM, no se produjo un VPK de
T8 y no se verificó en Vita3K/hardware ni se conectó al renderer del juego.
