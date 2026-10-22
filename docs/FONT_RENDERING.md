# T5: fuentes GDI y sustituto para Vita

PE 1.10a fijado a SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. La herramienta verifica el hash antes de leer sus estructuras. Publica metadatos, direcciones y conclusiones; el texto comercial, los bitmaps y los DAT permanecen locales.

## Peticiones de fuente recuperadas

Hay un sitio de `CreateFontA`, `0x411C75` (IAT `0x85700C`). Lo alimenta el descriptor de fuente, no una lista global inmutable de tamaños. Se ejecutó el fragmento de preparación original hasta la importación con descriptores controlados; Windows/GDI no se ejecutó.

| Argumento | Valor o procedencia |
|---|---|
| Face | Por defecto `ＭＳ ゴシック` (MS Gothic), CP932 en `0x858764`; nombre almacenado en `SWRFont+0x0C` |
| Height | Campo dinámico del descriptor; se ejercitaron 14, 24 y −17 |
| Weight | Campo dinámico; perfiles normales medidos 300, script por defecto 400; también se ejercitó 700 |
| Italic | Byte dinámico; se probaron 0 y 1 |
| Width, escapement, orientation | 0 |
| Underline, strikeout | 0 |
| Charset | 128, `SHIFTJIS_CHARSET` |
| OutPrecision | 4, `OUT_TT_PRECIS` |
| ClipPrecision | 0, `CLIP_DEFAULT_PRECIS` |
| Quality | 2, `PROOF_QUALITY` |
| PitchAndFamily | `0x31`, `FIXED_PITCH | FF_MODERN` |

No convertir sin más Height a puntos tipográficos: el signo tiene significado para el mapper GDI. Los valores positivos seleccionan altura de celda y los negativos altura de carácter; la fuente física y sus métricas se seleccionan posteriormente. [CreateFontA, Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-createfonta).

El barrido encuentra 14 llamadas directas a `SWRFont::setIndirect` (`0x411840`) y 19 a creación de textura de texto (`0x4050A0`). Las direcciones completas están en el JSON local. Se ejecutaron estos inicializadores concretos sin sustituir sus instrucciones:

| Callsite de descriptor | Contexto | Altura / peso medidos |
|---|---|---|
| `0x434DE1` | Perfil/layout | `14 − edi`, con edi=0: 14 / 300 |
| `0x438611` | Menú | 14 / 300 |
| `0x43D883` | Descriptor local de escena | 14 / 300 |
| `0x444142` | Global `0x89A4F8` | 14 / 300 |
| `0x44BA52` | Miembro de escena | 14 / 300 |
| `0x450B52` | Variante de sombra global | 14 / 300 |
| `0x462990` | Script, valores iniciales | 24 / 400 |
| `0x453CD1` | Nombre de perfil | `14 − max(trunc((longitud_en_bytes−16)/2),0)`; descriptor heredado |
| `0x453DBD` | Otro nombre de perfil | Misma fórmula con umbral 15; descriptor heredado |
| `0x46202A` | Registro de fuente de script | Nombre y tamaño configurables; registro sintético confirma override a altura 18, peso heredado 400 y espaciados 0/2 |
| `0x4126AD` | Ruby/furigana | Altura base truncada a un tercio del padre: 14→4, 24→8, 17→5; peso 400 |

El ajuste posterior de ruby por espacio disponible no se ejecutó en esa sonda. Los nombres y tamaños personalizados del script impiden tratar la tabla como un inventario finito de todas las fuentes posibles. Los ensayos de perfiles usan longitudes en bytes, incluidos casos impares para distinguir truncamiento de redondeo hacia abajo.

## Contrato de GetGlyphOutlineA y copia a textura

IAT `GetGlyphOutlineA=0x857014`; cuatro sitios:

| Función del camino | Consulta de tamaño | Obtención del bitmap |
|---|---|---|
| Glifo normal | `0x411E53` | `0x411F1A` |
| Punto usado por el layout | `0x4120C2` | `0x41213B` |

En los cuatro, el formato es **5, `GGO_GRAY4_BITMAP`**, con matriz identidad de 16.16 en `0x896EC4`. Primero se pide el tamaño con buffer nulo y longitud cero; después se reserva el tamaño devuelto y se pide el bitmap. Son bytes de cobertura entre 0 y 16, **17 niveles**, con filas alineadas a cuatro bytes; no son píxeles empaquetados de cuatro bits ni `GGO_GRAY8_BITMAP`. [GetGlyphOutlineA, Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-getglyphoutlinea).

Se ejecutaron las rutas normal/punto con y sin tabla de color, sustituyendo solo GDI y reserva/liberación. El bitmap sintético tiene caja 3×2 y cuatro bytes por fila: sus bytes de padding deliberadamente no nulos no se copian como píxeles. Con origen Y=2 y `tmAscent=8`, la primera fila de destino queda en Y=6. El avance suministrado de cuatro unidades desplaza el cursor cuatro en el camino normal; el punto usa otro anclaje y no produce ese avance.

La conversión de cobertura observada equivale a `alpha=floor(255*cobertura/16)`: muestras 0, 8 y 16 producen 0, 127 y 255; muestras 1 y 15 producen 15 y 239. Se conserva el RGB solicitado aunque el alpha sea cero. Los enteros de salida tienen formato `0xAARRGGBB`; una transferencia de bytes en little endian conserva el orden BGRA correspondiente. Las métricas de la sonda son sintéticas: prueban la copia y el layout, no que MS Gothic tenga esa caja o ese avance.

El camino de creación de texto usa `D3DXCreateTexture` en `0x409453`, desde el creador `0x409410`. Se ejecutaron sus ocho argumentos originales con dimensiones controladas: **formato 21 `D3DFMT_A8R8G8B8`, un nivel, usage 0, pool 1 (`MANAGED`)**. Después usa `LockRect`, copia con su pitch y hace `UnlockRect`. No se ejecutó la GPU; no se debe confundir el pitch de la máscara de glifo con el de la textura ARGB.

## Origen y codificación del texto

El PE referencia `data/csv/%s/spellcard.csv` y `data/scenario/%s/%03d.txt`, entre otras rutas. En los DAT locales sus representaciones empaquetadas incluyen `.cv1` y `.cv0`. La herramienta descifra todos los recursos de texto de las extensiones inspeccionadas y conserva solo conteos, hashes y nombres de archivo:

| Archivo local | Entradas revisadas | CP932 válidas | UTF-8 válidas | Caracteres japoneses al decodificar CP932 |
|---|---:|---:|---:|---:|
| `th123a.dat` | 101 (42 cv0, 59 cv1) | 101 | 21 | 62 548 |
| `th123b.dat` | 0 de las extensiones inspeccionadas | 0 | 0 | 0 |
| `th123c.dat` | 26 (20 cv0, 6 cv1) | 26 | 0 | 25 448 |

Las 127 entradas incluyen posibles reemplazos de archivos entre DAT; no se cuentan como 127 textos únicos del juego efectivo. Tampoco se interpreta cero entradas en b.dat como ausencia de texto dibujado dentro de imágenes.

La validez de una decodificación no identifica por sí sola una codificación. Aquí se combina con `CreateFontA/SHIFTJIS_CHARSET` y la ejecución del parser DBCS original: `82 A0` llega como `0x82A0`, consume dos bytes; ASCII consume uno; `B1` llega con extensión de signo `0xFFFFFFB1`. Se comprobaron los límites de sus rangos de bytes guía, incluidos los que no son caracteres CP932 válidos. No cambiar el conteo de bytes por un conteo Unicode sin adaptar el contrato.

También hay texto en el PE: preparación ejecutada en `0x448880` pasa un puntero a `0x859338`, en `.rdata`, y una textura 256×256. El literal tiene 35 caracteres CP932 y no es UTF-8 válido; no se copia su contenido al informe ni a git.

## Sustitutos evaluados

| Opción | Fidelidad y métricas | Coste / memoria | Licencias y distribución |
|---|---|---|---|
| FreeType en Vita con fuente japonesa abierta | Flexible para nombres y tamaños nuevos; exige CP932→Unicode, métricas compatibles, bearings, baseline y conversión de cobertura. Su hinting y otra fuente no garantizan igualdad con GDI/MS Gothic. | Rasterización y caché bajo demanda; hay que medir CPU y presupuesto de atlas. | Noto Sans Mono CJK JP es una candidata abierta; sus métricas se deben medir, no presumir iguales. FreeType y la fuente conservan sus avisos. |
| Caché generada en PC con la fuente del usuario y GDI | Puede conservar bitmap, GLYPHMETRICS, ascent, avance y parámetros de la misma fuente física y configuración. Es la mejor referencia de paridad. | Preparación en PC; en Vita, lectura y caché paginada. Requiere regenerar entradas para descriptores/glifos nuevos. | Se genera y guarda localmente junto a los recursos del usuario; no se añade la fuente propietaria ni sus bitmaps a este repositorio. |

**Recomendación:** caché GDI de referencia para cerrar la paridad inicial, con FreeType y una fuente abierta como alternativa explícita. La clave de caché debe incluir la fuente física identificada, los parámetros reales de CreateFontA (incluido signo de altura), el carácter empaquetado y el modo/matriz de GetGlyphOutlineA. Guardar máscara de cobertura y métricas permite aplicar colores y gradientes posteriormente sin duplicar todos los glifos por color. El generador y el backend de esa caché corresponden a la futura capa de plataforma; no están implementados en T5.

Como estimación de planificación, no medición del juego: 4 096 celdas de 32×32 consumen 4 MiB a un byte por píxel o 16 MiB en RGBA; faltan packing, bordes y metadatos. No precargar todas las variantes de altura/peso sin medir. Las pruebas con tabla de color usan colores sintéticos constantes; no cierran la igualdad de gradientes variables ni el clipping de todos los bearings.

[FreeType documenta sus modos de rasterización](https://freetype.org/freetype2/docs/reference/ft2-glyph_retrieval.html) y ofrece [FTL o GPLv2](https://freetype.org/license.html). La elección debe ser compatible con la licencia final del runtime. [Noto Sans CJK](https://github.com/notofonts/noto-cjk/blob/main/Sans/README.md) ofrece variantes Mono japonesas con ASCII de medio ancho; su [licencia OFL](https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE) debe acompañar la distribución que la utilice. No se instaló ni empaquetó una fuente en esta tarea.

## Verificación y límites

```powershell
python -m unittest tests.test_find_font_requests -v
python tools/find_font_requests.py
python -m py_compile tools/find_font_requests.py tests/test_find_font_requests.py
git diff --check
```

Resultado medido: **15 pruebas, `OK`**. La CLI examinó el PE fijado y los tres DAT locales; salida `artifacts/pe-inventory/<sha>/T5-font-requests.json`, reproducible y sin marcas de tiempo. Las pruebas del PE usan skipUnless si falta y comprueban rechazo de un hash incorrecto antes de generar un informe. El informe publica metadatos y ejemplos sintéticos, no texto ni bitmaps comerciales.

Confianza alta para los argumentos y transformaciones de los fragmentos ejecutados; media para generalizar esos perfiles a todos los modos del juego. **Sin verificar:** rasterizador GDI real, fuente física seleccionada en Windows, igualdad visual de glifos/métricas, todas las opciones de scripts, ejecución en Vita3K y rendimiento en hardware. No se cambió `recomp/`, el renderer, ni se compiló un VPK nuevo para T5.
