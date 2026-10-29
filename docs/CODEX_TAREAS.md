# Tareas para Codex

Cada tarea es independiente y se puede pegar tal cual en Codex. Antes de empezar, Codex debe leer [AGENTS.md](../AGENTS.md): entorno, worktree propio, reglas e informe final. Claude trabaja en paralelo en `recomp/` (descubrimiento de funciones y lifter); ninguna de estas tareas toca ese directorio.

Encabezado común para pegar antes de cada tarea:

```
Repositorio: C:\Users\Andy PC\Documents\Chatgpt\Touhou_123\Touhou123Vita
Lee AGENTS.md completo y síguelo: crea tu worktree y rama codex/<N>, no hagas push,
edita solo los archivos que indica la tarea y termina con el informe final.
```

## Estado

| # | Tarea | Prioridad | Estado |
|---|---|---|---|
| T1 | Flags de `CreateDevice` y modo x87 | Alta, bloquea el modelo x87 del lifter | Hecha (21 oct 2026), integrada en `main`: [X87_MODE.md](X87_MODE.md) |
| T2 | Efectos D3DX embebidos | Media | Hecha (21 oct 2026), integrada en `main`: [D3DX_EFFECTS.md](D3DX_EFFECTS.md) |
| T3 | Censo de métodos COM usados | Media | Hecha (22 oct 2026), integrada: [COM_USAGE.md](COM_USAGE.md) |
| T4 | zlib, libpng y vorbis nativos para Vita | Media | Hecha (22 oct 2026), integrada: `third_party/vita-libs/` |
| T5 | Peticiones de fuente y sustituto de `GetGlyphOutlineA` | Baja | Hecha (22 oct 2026), integrada: [FONT_RENDERING.md](FONT_RENDERING.md) |
| T6 | Arreglar los fallos de prueba previos de `legacy/` | Baja | Hecha (22 oct 2026), integrada: ver `legacy/README.md` |
| T7 | Conversión Shift-JIS (CP932) ↔ UTF-16 | Alta, texto del juego | Hecha (24 oct 2026), integrada: `recomp/host/sjis.c` (falta conectarla a `MultiByteToWideChar`) |
| T8 | Rasterizador de glifos `GGO_GRAY4_BITMAP` | Alta, necesaria para H3 | Hecha (24 oct 2026), integrada: [GLYPHS.md](GLYPHS.md) (fuera de los builds hasta enlazar FreeType) |
| T9 | Teclado SDL → códigos DIK de DirectInput | Media | Hecha (24 oct 2026), integrada: [INPUT_MAP.md](INPUT_MAP.md) (falta conectarla a `GetDeviceState`) |
| T10 | Pruebas del heap guest | Media | Hecha (24 oct 2026), integrada; sus dos desbordamientos están corregidos en `support.c` |
| T11 | Diagnóstico del fallo de Vita3K en la carga | — | Cancelada (24 oct 2026): era la textura sin memoria (`memcpy` desde NULL); con las texturas comprimidas Vita3K llega a 3 600 fotogramas |

| T12 | Mezclador de audio para DirectSound | Alta, audio | Pendiente |
| T13 | Informe de trazas (`trace_report.py`) | Media, medición de la carga en Vita | Pendiente |
| T14 | Recursión infinita al cerrar tras fallar `CreateDevice` | Baja | Pendiente |
| T15 | Análisis de la traducción al inglés `th123e` (v1.1a) | Alta | Pendiente |

### Reglas comunes de T7–T14 (fases H2–H4)

- Claude es dueño de `recomp/`. Estas tareas **crean archivos nuevos** dentro de `recomp/host/` con una interfaz C fija. **No edites** `kernel32.c`, `other.c`, `media.c`, `win32.h` ni ningún archivo existente: Claude conecta tu módulo con la capa Win32 al integrarlo. Si tu módulo necesita algo de otro archivo, explícalo en el informe.
- El C de `recomp/host/` es C11 (`-std=gnu11 -Wall`), portable a PC (MinGW, `C:\msys64\ucrt64\bin\gcc.exe`) y a Vita (`C:\vitasdk\bin\arm-vita-eabi-gcc.exe`). No uses `_Thread_local`, porque en VitaSDK no es local a cada hilo; tampoco uses APIs de Windows.
- Las pruebas `tests/test_<nombre>.py` compilan el C con el GCC host, ejecutan el binario y comprueban su salida. Si falta GCC, se saltan con `skipUnless`.
- Comprueba además que el módulo compila para ARM: `arm-vita-eabi-gcc -std=gnu11 -O1 -Wall -c <archivo>.c`.

---

## T1 — Flags de `CreateDevice` y modo x87 que deja D3D9

**Objetivo.** Saber con qué precisión x87 corre el juego. `IDirect3D9::CreateDevice` (slot 16 de la vtable, offset `0x40`) pone la FPU en precisión simple (24 bits) salvo que `BehaviorFlags` incluya `D3DCREATE_FPU_PRESERVE` (`0x2`). Esto decide si el lifter emula x87 con `float` o con `double`.

**Pasos.**
1. Localiza la llamada a `Direct3DCreate9` (importación de `d3d9.dll`), el global donde se guarda el `IDirect3D9*` y la llamada indirecta `call [reg+0x40]` que hace `CreateDevice`.
2. Recupera el valor de `BehaviorFlags`: inmediato, rama o valor leído de config. Si hay varias rutas (por ejemplo, vértices por hardware o por software), documenta todas. Si puedes, confírmalo ejecutando el fragmento en Unicorn, como hacen las sondas `tools/x86_*_probe.py`.
3. Inventaría los 290 `fldcw` y las llamadas a `_controlfp`/`_control87` del CRT: qué control word se carga, en qué funciones y si cambian la precisión (bits PC) o solo el redondeo (bits RC, típico de `_ftol`).

**Archivos que puedes crear:** `tools/x87_mode_probe.py`, `tests/test_x87_mode_probe.py`, `docs/X87_MODE.md`.

**Verificación.** `python -m unittest tests.test_x87_mode_probe -v` pasa, y `python tools/x87_mode_probe.py` escribe su informe en `artifacts/pe-inventory/<sha>/x87-mode.json`.

**Entrega.** En `docs/X87_MODE.md`: valor de `BehaviorFlags` con su dirección, si se usa `FPU_PRESERVE`, tabla de control words por tipo de uso y una recomendación (`float`, `double` o mixto) con su justificación.

---

## T2 — Efectos D3DX embebidos

**Objetivo.** Saber qué hacen los 3 efectos compilados (blobs con firma `0xFEFF0901` dentro del PE) para reescribirlos a mano en vitaGL.

**Pasos.**
1. Localiza los blobs, su tamaño y quién los pasa a `D3DXCreateEffect` (dirección del llamador y para qué se usa el efecto).
2. Parsea el formato binario de efecto `fx_2_0` lo necesario para listar parámetros (nombre, tipo, semántica), techniques, passes, estados de render y shaders.
3. Desensambla el bytecode de los shaders (`vs_1_1` y el perfil `ps` que aparezca) a texto asm de D3D9.

**Archivos que puedes crear:** `tools/extract_d3dx_effects.py`, `tests/test_extract_d3dx_effects.py`, `docs/D3DX_EFFECTS.md`.

**Salidas locales (no en git):** `artifacts/pe-inventory/<sha>/effects/` con los blobs y el asm.

**Entrega.** En `docs/D3DX_EFFECTS.md`, para cada efecto: llamador, propósito inferido, parámetros, número de instrucciones de cada shader y una descripción en prosa de lo que calcula, suficiente para reimplementarlo. **No copies el asm completo** al documento.

---

## T3 — Censo de métodos COM usados

**Objetivo.** Acotar las capas de compatibilidad: qué métodos de `IDirect3DDevice9`, `IDirect3D9`, `IDirect3DTexture9`/`Surface9`/`VertexBuffer9`, `ID3DXEffect`, `IDirectSound8`, `IDirectSoundBuffer8`, `IDirectInput8A` e `IDirectInputDevice8A` llama el juego, y desde cuántos sitios.

**Pasos.**
1. Identifica los globales o campos donde se guardan los punteros de interfaz: salidas de `CreateDevice`, `CoCreateInstance`, `CreateTexture` y demás.
2. Detecta los patrones `mov reg,[iface]; mov reg2,[reg]; call [reg2+off]` y similares. Traduce el offset a nombre de método con el orden de las vtables de los SDK públicos (`d3d9.h`, `dsound.h`, `dinput.h`); incluye esas tablas de nombres en la herramienta.
3. Marca cada sitio con su nivel de confianza (alto si el puntero viene directamente del global conocido).
4. Para `SetRenderState`, `SetTextureStageState` y `SetSamplerState`, recoge los estados constantes que se pasan.

**Archivos que puedes crear:** `tools/com_usage_census.py`, `tests/test_com_usage_census.py`, `docs/COM_USAGE.md`.

**Entrega.** En `docs/COM_USAGE.md`: una tabla por interfaz (método, número de sitios, confianza), los estados de render y textura usados, y una lista de lo que la capa D3D9 de Vita debe implementar sí o sí.

---

## T4 — zlib, libpng y vorbis nativos para Vita

**Objetivo.** El PE lleva embebidos **zlib 1.2.3** y **libpng 1.2.5** (cadenas de versión en `.rdata`), además de libogg/libvorbis. Para reemplazar esas funciones por código nativo hacen falta las mismas versiones compiladas para Vita. `C:\vitasdk` no trae ninguna de las tres.

**Pasos.**
1. Confirma en el PE la versión exacta de libogg y libvorbis (cadena del vendor `Xiph.Org libVorbis ...`). Si no aparece, documenta la mejor estimación y su evidencia.
2. Escribe un script que descargue los tarballs oficiales de esas versiones exactas, **verifique un SHA-256 fijado en el script** y los compile con VitaSDK como bibliotecas estáticas en `artifacts/vita-libs/` (fuera de git).
3. Haz una prueba de humo para Vita (compress/uncompress de zlib, decodificar un PNG pequeño generado por la propia prueba, versión de vorbis) que compile en un `.self` con VitaSDK. Ejecutarla en Vita3K es opcional; si no lo haces, dilo.

**Archivos que puedes crear:** `third_party/vita-libs/build.ps1`, `third_party/vita-libs/README.md`, `third_party/vita-libs/smoke_test.c`.

**Entrega.** Versiones confirmadas con su evidencia, hashes de los tarballs, resultado de la compilación y tamaño de cada `.a`.

---

## T5 — Peticiones de fuente y sustituto de `GetGlyphOutlineA`

**Objetivo.** El juego rasteriza el texto con GDI (`CreateFontA` y `GetGlyphOutlineA`). Para Vita hace falta saber exactamente qué pide para poder sustituirlo.

**Pasos.**
1. Localiza todas las llamadas a `CreateFontA`: nombre de fuente (puede estar en Shift-JIS), altura, peso, charset y calidad. Localiza también las llamadas a `GetGlyphOutlineA`: formato (`GGO_GRAY8_BITMAP`, etc.), matriz y cómo se usa el bitmap resultante (copia a una textura y con qué formato).
2. Comprueba si el texto sale de los DAT (por ejemplo `.cv1`/`.csv`) o del propio PE, y qué codificación usa.
3. Compara dos opciones de sustituto: (a) FreeType en Vita con una fuente japonesa de licencia libre, de tamaño y métricas compatibles; (b) una caché de glifos generada en PC a partir de la fuente del usuario. Considera memoria, fidelidad y licencias.

**Archivos que puedes crear:** `tools/find_font_requests.py`, `tests/test_find_font_requests.py`, `docs/FONT_RENDERING.md`.

**Entrega.** Tabla de peticiones de fuente con direcciones, formato de glifo, origen del texto y una recomendación justificada.

---

## T6 — Arreglar los fallos de prueba previos de `legacy/`

**Objetivo.** Dejar en verde el motor congelado, sin ampliarlo. Hay 3 fallos que ya existían en la etiqueta `legacy-reimpl-2.199`:

- `legacy/tests/fight_tests.c`: línea 132 (`burst.objects[0]...hit_done==0`) y línea 498 (`patterned_states()==0`).
- `tests/test_remilia_412_spawn_probe.py`, `test_real_factory_hitbox_reaches_original_pair_geometry`: X=191,72 frente a 391,72 esperado.
- `tests/test_stage_camera_oracle.py`, `test_player_sprite_renderer_uses_camera_translation_then_zoom`: no encuentra la cadena `float object_x=o->action==821?o->world_x:(float)o->x` en `legacy/src/vita_main.c`.

**Pasos.** Para cada fallo, averigua si está mal la prueba (expectativa desactualizada tras la iteración 2.199, que pasó las cajas a unidades de mundo completas) o el código. Corrige lo mínimo y justifícalo. No cambies comportamiento que otras pruebas cubran.

**Archivos que puedes editar:** `legacy/**`, `tests/test_remilia_412_spawn_probe.py`, `tests/test_stage_camera_oracle.py` y, si hace falta, `tools/x86_remilia_412_spawn_probe.py`.

**Verificación.**

```powershell
$env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"
$core = 'core','fight','animation','resources','pattern','input','stage','replay' | % { "legacy/src/$_.c" }
gcc -std=gnu11 -O1 -Wall -Wextra -Werror -Ilegacy/include @core legacy/tests/fight_tests.c -lm -o $env:TEMP\fight.exe; & $env:TEMP\fight.exe
python -m unittest discover -s tests -p "test_*.py"
```

Ambos deben terminar sin fallos (la suite Python tarda unos 7 minutos).

**Entrega.** Causa de cada fallo y qué se cambió (la prueba o el código), con su justificación.

---

## T7 — Conversión Shift-JIS (CP932) ↔ UTF-16

**Objetivo.** Hoy `MultiByteToWideChar` y `WideCharToMultiByte` convierten cualquier carácter no ASCII en `?`. El juego guarda nombres, menús y diálogos en CP932, así que hace falta una conversión exacta, compatible con la de Windows, que corra también en Vita.

**Interfaz que debes entregar** (`recomp/host/sjis.h`):

```c
#include <stddef.h>
#include <stdint.h>
/* Igual que MultiByteToWideChar(932, 0, ...): out == NULL o out_len == 0 -> devuelve
   el número de unidades UTF-16 necesarias. in_len < 0 -> la entrada termina en NUL,
   que se cuenta y se copia. Bytes inválidos o truncados -> U+30FB, como Windows. */
int sjis_to_utf16(const uint8_t *in, int in_len, uint16_t *out, int out_len);
/* Igual que WideCharToMultiByte(932, 0, ...) con el carácter por defecto '?'.
   *used_default (si no es NULL) indica si hubo sustituciones. */
int utf16_to_sjis(const uint16_t *in, int in_len, uint8_t *out, int out_len, int *used_default);
```

**Pasos.**
1. Genera las tablas con el códec `cp932` de Python, no con descargas, para cubrir los 7 915 caracteres de doble byte, el katakana de un byte (0xA1–0xDF) y las extensiones NEC/IBM. Ojo: `cp932` de Python y Windows difieren en algunos puntos (por ejemplo, 0x5C y 0x7E se quedan en ASCII en los dos, y algún carácter IBM tiene varias codificaciones). Documenta cada diferencia que encuentres y sigue a Windows.
2. Emite tablas compactas en C, por ejemplo por byte inicial. Mide su tamaño: debe quedar por debajo de unos 64 KiB entre las dos direcciones.
3. Compara el C con Python en todos los valores de 1 y 2 bytes y en todos los puntos de código de 16 bits.

**Archivos que puedes crear:** `tools/gen_sjis_table.py`, `recomp/host/sjis.h`, `recomp/host/sjis.c` y `recomp/host/sjis_table.h` (generado, pero se sube a git porque es una tabla de un estándar y no un recurso del juego), además de `tests/sjis_harness.c` y `tests/test_sjis.py`.

**Verificación.** `python -m unittest tests.test_sjis -v` pasa. `python tools/gen_sjis_table.py --check` confirma que la tabla subida coincide con la regenerada. Además, `sjis.c` compila para ARM.

**Entrega.** Tamaño de las tablas, diferencias entre Python y Windows con su evidencia, y el resultado literal de las pruebas.

---

## T8 — Rasterizador de glifos `GGO_GRAY4_BITMAP`

**Objetivo.** `GetGlyphOutlineA` devuelve hoy `GDI_ERROR`, así que el juego no tiene texto. [FONT_RENDERING.md](FONT_RENDERING.md) (T5) midió lo que pide: formato 5 (`GGO_GRAY4_BITMAP`), matriz identidad y la llamada en dos pasos (primero el tamaño con buffer nulo, luego los datos), con bytes de cobertura de 0 a 16 y filas alineadas a 4 bytes. La fuente por defecto es MS Gothic. Hay que sustituirla por una fuente libre rasterizada con FreeType.

**Interfaz que debes entregar** (`recomp/host/glyph.h`):

```c
#include <stdint.h>
typedef struct {            /* mismo orden que GLYPHMETRICS de GDI */
    uint32_t black_box_x, black_box_y;
    int32_t origin_x, origin_y;   /* gmptGlyphOrigin: esquina superior izquierda respecto al origen */
    int16_t cell_inc_x, cell_inc_y;
} GlyphMetrics;
/* Carga la fuente (ruta en el host). 0 = ok. */
int glyph_init(const char *font_path);
/* height y weight como en CreateFontA (height < 0 = altura de carácter, > 0 = altura
   de celda). code es UTF-16. Con buf == NULL o size == 0 devuelve el tamaño necesario;
   si no, escribe filas alineadas a 4 bytes de cobertura 0..16 y devuelve los bytes
   escritos. 0xFFFFFFFF = error. Un espacio devuelve 0 bytes y métricas válidas. */
uint32_t glyph_gray4(int height, int weight, uint16_t code, GlyphMetrics *gm,
                     uint8_t *buf, uint32_t size);
```

**Pasos.**
1. Elige la fuente: Noto Sans Mono CJK JP o Noto Sans CJK JP (OFL). La fuente **no va en git**: el script la descarga a `local/fonts/` con un SHA-256 fijado y documenta la licencia. Mide sus métricas frente a las de MS Gothic que dio T5 y recomienda una.
2. FreeType: comprueba si está en MSYS2 (`mingw-w64-ucrt-x86_64-freetype`) y en VitaSDK (`C:\vitasdk\arm-vita-eabi\lib\libfreetype.a`, o con `vdpm freetype`). Si falta en alguno, documenta cómo instalarlo; **no** lo vendorices.
3. Implementa la conversión de alturas de GDI (celda frente a carácter, con el signo como explica T5), la negrita (peso ≥ 600 → `FT_Outline_Embolden` o similar) y la cuantización de la cobertura de 0–255 a 0–16.
4. Caché: guarda los glifos ya rasterizados por (altura, peso, código). Mide la memoria para los 2 000 kanji más comunes.

**Archivos que puedes crear:** `recomp/host/glyph.h`, `recomp/host/glyph.c`, `tools/fetch_font.py`, `tests/glyph_harness.c`, `tests/test_glyph.py`, `docs/GLYPHS.md`.

**Verificación.** `python -m unittest tests.test_glyph -v` pasa: cubre los tamaños del primer y segundo paso, la alineación de filas, el rango 0..16, el espacio y un kanji, y se salta si falta la fuente o FreeType. `glyph.c` compila para ARM si FreeType está en VitaSDK; si no está, dilo.

**Entrega.** En `docs/GLYPHS.md`: la fuente elegida y sus métricas comparadas con MS Gothic, cómo instalar FreeType en PC y en Vita, la memoria de la caché y una imagen de prueba (el texto de prueba renderizado, guardado en `artifacts/`, no en git).

---

## T9 — Teclado SDL → códigos DIK de DirectInput

**Objetivo.** `IDirectInputDevice8A::GetDeviceState` devuelve hoy todo a cero, así que el juego no recibe teclas. Hace falta una tabla de scancodes SDL2 a códigos `DIK_*` (`dinput.h`) y el mapeo por defecto de los botones de la Vita a las teclas que usa Soku por defecto.

**Interfaz que debes entregar** (`recomp/host/input_map.h`):

```c
#include <stdint.h>
/* Código DIK_* (0..255) para un SDL_Scancode, o 0 si no tiene equivalente. */
uint8_t dik_from_sdl_scancode(int scancode);
/* Botones de la Vita (máscara SCE_CTRL_*) -> teclas pulsadas en un estado de 256 bytes
   (0x80 = pulsada), según la configuración de teclado por defecto de Soku. */
void dik_state_from_vita_buttons(uint32_t buttons, uint8_t state[256]);
```

**Pasos.**
1. Escribe la tabla completa a partir de los valores públicos de `SDL_scancode.h` y `dinput.h`. Están en `local/SokuLib/directx` y en MSYS2. No incluyas SDL en el `.c`: copia los valores numéricos como constantes con comentario.
2. Averigua la configuración de teclado por defecto de Soku (las teclas de arriba, abajo, izquierda, derecha, A, B, C, D, cambio de carta, uso de carta y pausa). Puedes sacarla de su documentación, de SokuLib o del PE: busca la tabla de teclas por defecto y su dirección. Indica el origen y la confianza. Propón un mapeo de la Vita (cruceta, ×, ○, □, △, L, R y Start).

**Archivos que puedes crear:** `recomp/host/input_map.h`, `recomp/host/input_map.c`, `tests/input_map_harness.c`, `tests/test_input_map.py`, `docs/INPUT_MAP.md`.

**Verificación.** `python -m unittest tests.test_input_map -v` pasa. Comprueba al menos las letras, los números, las flechas, Enter, Escape, Shift, los códigos sin equivalente (que dan 0) y el mapeo de la Vita. El `.c` compila para ARM.

**Entrega.** La tabla de teclas por defecto de Soku con su origen y dirección, y el mapeo propuesto para la Vita.

---

## T10 — Pruebas del heap guest

**Objetivo.** El heap del guest (`recomp/host/support.c`: `heap_alloc`, `heap_free`, `heap_realloc`, `heap_size`) se reescribió en H2. Ahora tiene clases de tamaño hasta 4 KiB y una lista de bloques grandes ordenada por dirección, que se parten al reservar y se fusionan con sus vecinos libres al liberar. No tiene pruebas.

**Pasos.**
1. Escribe un *harness* en C que enlace `recomp/host/support.c` y `recomp/runtime/guest.c` con los *stubs* mínimos que falten (`trace`, la tabla de APIs, etc.) en tu propio archivo. Si no se puede enlazar sin tocar `support.c`, no lo toques: explica qué haría falta.
2. Pruebas: alineación a 16 bytes; `heap_size` igual al tamaño pedido; un bloque grande liberado y vuelto a pedir reutiliza la misma dirección; la partición (pedir 1 MiB dentro de un hueco de 4 MiB deja 3 MiB reutilizables); la fusión en los dos sentidos (liberar A, C y luego B da un solo bloque); `realloc` que crece y que encoge, con los datos preservados; y agotamiento, que devuelve 0 sin corromper nada.
3. Una prueba aleatoria con semilla fija: 100 000 operaciones mezcladas que comprueban que ningún par de bloques vivos se solapa y que el contenido se conserva (rellena cada bloque con un patrón).

**Archivos que puedes crear:** `tests/heap_harness.c`, `tests/heap_stubs.c`, `tests/test_guest_heap.py`.

**Verificación.** `python -m unittest tests.test_guest_heap -v` pasa. Si encuentras un fallo del allocator, **no lo arregles**: descríbelo con la secuencia mínima que lo reproduce.

**Entrega.** Los casos cubiertos, los fallos encontrados con su secuencia mínima, y la fragmentación final de la prueba aleatoria (bytes vivos frente a `heap_top`).

---

## T11 — Diagnóstico del fallo de Vita3K en la carga

**Objetivo.** Con el VPK de H2 (commit `4c7abda`), Vita3K pasa por D3D9, DirectInput y DirectSound y entra en la carga de recursos (muchas aperturas de `th123a.dat` desde varios hilos). Después **se cae el propio emulador**: `logging::exception_handler: Read violation at address 0x0`. Hay que saber si es un fallo de Vita3K o de nuestro programa.

**Pasos.**
1. Compila y ejecuta con `python recomp/build_vita.py` (y con `--trace-calls`) y `tools/vita3k-recomp.ps1`. Los registros quedan en `artifacts/recomp/<sha>/vita/run/`: `vita3k.log`, `recomp-trace.log`.
2. Mira las últimas líneas de `vita3k.log` antes de la excepción: el hilo, el último *syscall* o NID y la versión de Vita3K. Si el registro no basta, sube el nivel de log de Vita3K en `local/vita3k-isolated` (solo la configuración del emulador aislado) y repite.
3. Busca en los issues de Vita3K en GitHub fallos parecidos: muchos hilos, `pthread`, E/S de archivos concurrente o `sceIoLseek`/`sceIoRead`.
4. Si encuentras un patrón sospechoso en nuestro lado (por ejemplo, el mismo descriptor usado desde dos hilos o un `pthread_cond_timedwait` con hora absoluta), propón el cambio. **No edites** `recomp/`.
5. ¿Es reproducible? Ejecútalo 3 veces y anota si se cae siempre en el mismo punto.

**Archivos que puedes crear:** `docs/VITA3K_LOAD_CRASH.md`.

**Entrega.** Las líneas relevantes del registro, la reproducibilidad, los issues relacionados con su enlace, una conclusión (emulador o nuestro) con su nivel de confianza y el cambio propuesto si lo hay.

---

## T12 — Mezclador de audio para DirectSound

**Objetivo.** Hoy `IDirectSoundBuffer` acepta `Lock`, `Play` y `SetVolume`, pero no suena nada: `GetCurrentPosition` siempre devuelve 0 (ver `recomp/host/media.c`). Hace falta un mezclador en C, sin dependencias, que Claude conectará a SDL2 en PC y a `sceAudioOut` en Vita.

**Interfaz que debes entregar** (`recomp/host/audio_mix.h`):

```c
#include <stdint.h>
typedef struct AudioVoice AudioVoice;
/* Formato del buffer como WAVEFORMATEX: canales 1-2, 8 bits (sin signo) o 16 bits (con signo). */
AudioVoice *audio_voice_new(const uint8_t *pcm, uint32_t bytes, uint32_t rate, int channels, int bits);
void audio_voice_free(AudioVoice *v);
void audio_voice_play(AudioVoice *v, int looping);      /* DSBPLAY_LOOPING */
void audio_voice_stop(AudioVoice *v);
void audio_voice_set_position(AudioVoice *v, uint32_t byte_offset);
void audio_voice_set_volume(AudioVoice *v, int32_t centibels); /* DSBVOLUME: -10000..0 */
void audio_voice_set_pan(AudioVoice *v, int32_t centibels);    /* DSBPAN: -10000..10000 */
void audio_voice_set_frequency(AudioVoice *v, uint32_t hz);    /* 0 = la original */
/* Cursores en bytes del buffer, como GetCurrentPosition: play y write. */
void audio_voice_position(const AudioVoice *v, uint32_t *play, uint32_t *write);
int audio_voice_playing(const AudioVoice *v);
/* Mezcla todas las voces activas en out (estéreo intercalado, int16, out_rate Hz). Hilo seguro:
   el callback de audio llama a esto mientras el juego toca las voces desde otros hilos. */
void audio_mix(int16_t *out, uint32_t frames, uint32_t out_rate);
```

**Pasos.**
1. Remuestreo lineal de la frecuencia de cada voz a `out_rate`. La conversión de centibelios a ganancia sigue la de DirectSound (`10^(cB/2000)`), y el *pan* atenúa solo el canal contrario. Satura a int16.
2. Las voces en bucle dan la vuelta al final del buffer; las otras se paran solas. El juego escribe en el buffer mientras suena (streaming de música con `Lock` y `Unlock` por mitades): el mezclador lee siempre del puntero `pcm` que se le dio, sin copiarlo.
3. Un mutex propio (pthread). No uses `_Thread_local`.

**Archivos que puedes crear:** `recomp/host/audio_mix.h`, `recomp/host/audio_mix.c`, `tests/audio_mix_harness.c`, `tests/test_audio_mix.py`.

**Verificación.** `python -m unittest tests.test_audio_mix -v` pasa. Debe cubrir: un seno de 1 kHz a 22 050 Hz mezclado a 48 000 Hz que conserva la frecuencia (con cruces por cero o FFT simple), volumen -600 cB ≈ 0,5 de amplitud, *pan* extremo, bucle frente a no bucle, cursores que avanzan según los *frames* mezclados, y saturación. Además, compila para ARM.

**Entrega.** Decisiones de remuestreo y ganancia con su justificación, y el resultado literal de las pruebas.

---

## T13 — Informe de trazas (`trace_report.py`)

**Objetivo.** Cada prueba en la Vita produce un `recomp-trace.log`. Hace falta una herramienta que lo resuma igual para PC y para Vita y que compare dos ejecuciones, para medir cuánto mejora la carga entre builds.

**Formato de entrada** (líneas que ya existen; mira una traza real en `artifacts/recomp/<sha>/run/host-trace.log`):

- `# frame N: D draws so far (T ms)` cada 60 fotogramas;
- `# first busy frame (>= 10 draws, title reached): frame N at T ms`;
- `# before vitaGL: …`, `# after vitaGL: …`, `# memory: …`, `# frames presented: …; textures live … KiB, peak … KiB`;
- el resumen `#   <llamadas> <API> (<ms> ms)` y `#   <llamadas> <Clase>::<Método> (<ms> ms)`;
- `# thread N (start X): …` (fallos de hilos) y `# exit: …`.

**Salida.** En texto (por defecto) y en JSON (`--json`): tiempo hasta el título, *draws* por fotograma por tramos, las 15 APIs y métodos COM con más tiempo, memoria, fallos de hilos y motivo de salida. Con `--compare a.log b.log`, las diferencias. Lee el archivo como bytes y decodifica en Shift-JIS con `errors="replace"`, porque hay títulos en CP932.

**Archivos que puedes crear:** `tools/trace_report.py`, `tests/test_trace_report.py` (con trazas sintéticas pequeñas escritas por la propia prueba; no subas trazas reales).

**Verificación.** `python -m unittest tests.test_trace_report -v` pasa. Ejecuta además la herramienta sobre las trazas reales de `artifacts/recomp/<sha>/run/host-trace.log` y de `vita/run/recomp-trace.log` si existen, y pega la salida en el informe.

---

## T14 — Recursión infinita al cerrar tras fallar `CreateDevice`

**Objetivo.** Cuando `IDirect3D9::CreateDevice` falla, el juego muestra «D3Dデバイスの作成に失敗» y, al cerrarse, la función 0x43a880 (un borrado recursivo de árbol rojo-negro, el destructor de un `std::map`/`std::set` de MSVC) entra en recursión infinita. Recorre memoria a cero y desborda la pila del host. Pasó en Vita3K y en la Vita real (`psp2dmp`). Hay que entender por qué el árbol está mal en ese camino.

**Pasos.**
1. Encuentra en el PE quién llama a 0x43a880 en el camino de salida tras el error (`MessageBoxA` del error y luego `ExitProcess` o el retorno de `WinMain`): el destructor global, el objeto y la dirección del árbol.
2. Mira si el árbol se usa antes de construirse (orden de inicialización de globales, `atexit`) o si depende de algo que nuestro host no hace (por ejemplo, `MessageBoxA` devuelve al instante, o `HeapAlloc` devuelve memoria que Windows pondría a cero).
3. Si puedes, reprodúcelo en PC forzando el fallo. Tienes permiso para añadir **solo en tu rama** una variable `T123_FAIL_CREATEDEVICE` en `recomp/host/d3d9.c`; Claude decidirá si se queda.

**Archivos que puedes crear o editar:** `docs/EXIT_CRASH.md` y, solo para reproducirlo, `recomp/host/d3d9.c`.

**Entrega.** La cadena de llamadas con direcciones, la causa con su nivel de confianza y el arreglo propuesto en el host.


---

## T15 — Análisis de la traducción al inglés `th123e` (v1.1a)

**Objetivo.** El usuario tiene la traducción no oficial al inglés v1.1a (2011-10-19, para la 1.10a) en el paquete «Soku»: `F:\Download\Touhou\TOUHOU 123\Touhou 12.3 - Hisoutensoku\Soku\` (`th123e.exe` 8 KiB, `th123e.dll` 243 200 bytes, `th123e.dat` 2 073 690 bytes). `th123e.exe` arranca el juego suspendido e inyecta `th123e.dll` (`CreateRemoteThread`). El DLL parchea código en memoria (`VirtualProtect`), registra una fuente propia (`AddFontMemResourceEx`, `CreateFontW`, `GetGlyphOutlineW`) y lee `th123e.dat`. En nuestra recompilación estática los parches en memoria del código no tienen efecto, así que hay que reproducir su comportamiento en la capa del host. Esta tarea **solo analiza**: decide el diseño, pero no lo implementa.

**Pasos.**
1. **Copia de trabajo.** Copia los tres archivos a `artifacts/th123e/` (ignorado por git) y trabaja sobre la copia. No ejecutes nada del paquete.
2. **Formato de `th123e.dat`.** Documenta cabecera, índice, cifrado o compresión y una lista de los recursos que contiene, con nombre, tipo y tamaño. ¿Usa el mismo formato y los mismos nombres que `th123a/b/c.dat`, de modo que cada entrada sustituye a un recurso del juego? Escribe un lector que liste las entradas.
3. **Parches del DLL.** Desensambla `th123e.dll` (MinGW, i386) y enumera cada escritura sobre la imagen de `th123.exe` 1.10a (SHA-256 `f0db9366…a16731e`): dirección, bytes originales y nuevos, y a qué función del DLL desvía. Clasifícalas:
   - (a) búsqueda o apertura de recursos: dónde engancha para dar prioridad a `th123e.dat`;
   - (b) texto y fuentes: cambio a W/Unicode, anchos o espaciado;
   - (c) correcciones de diseño, como el recorte del lado izquierdo del texto;
   - (d) otras.
   Para cada una indica si se podría hacer desde el host: interceptar una función del juego, servir otro recurso o cambiar un valor en GDI.
4. **Propuesta.** Explica cómo lo haría la capa del host. Por ejemplo, interceptar la función de apertura de recursos del juego y servir primero desde `th123e.dat`, y usar la fuente libre de T8 para el texto en inglés. Estima qué parte del parche quedaría cubierta y qué no.

**Archivos que puedes crear:** `tools/th123e_dat.py`, `tests/test_th123e_dat.py` (se salta si falta `artifacts/th123e/th123e.dat`), `docs/TH123E_ANALYSIS.md`. No subas ni el DAT, ni el DLL, ni nada extraído: solo nombres, direcciones, conteos y conclusiones.

**Verificación.** `python -m unittest tests.test_th123e_dat -v` pasa. `python tools/th123e_dat.py artifacts/th123e/th123e.dat` lista las entradas y escribe el informe en `artifacts/th123e/index.json`.

**Entrega.** El formato del DAT, la tabla de parches con direcciones y clasificación, y la propuesta de implementación con su nivel de confianza.
