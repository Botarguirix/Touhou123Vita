# Tareas para Codex (fase F1)

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
| T3 | Censo de métodos COM usados | Media | Pendiente |
| T4 | zlib, libpng y vorbis nativos para Vita | Media | Pendiente |
| T5 | Peticiones de fuente y sustituto de `GetGlyphOutlineA` | Baja | Pendiente |
| T6 | Arreglar los fallos de prueba previos de `legacy/` | Baja | Pendiente |

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
