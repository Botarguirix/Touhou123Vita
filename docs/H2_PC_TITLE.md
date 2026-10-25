# H2: pantalla de título en PC

**Estado: conseguido el 23 oct 2026.** El código original de `th123.exe` 1.10a, recompilado a C, dibuja la pantalla de título de Hisoutensoku (cielo, logotipo «東方非想天則» y la línea de copyright) en una ventana SDL2 con OpenGL de función fija. No hay ningún código del juego reescrito a mano: lo que se ve sale de la lógica y los recursos originales.

La captura se guarda en `artifacts/recomp/<sha>/run/last-frame.bmp` y no se sube a git, porque es arte del juego (regla 1 de [AGENTS.md](../AGENTS.md)).

## Medido (PC, GTX 1660 Ti, GL 4.6)

| Medida | Valor |
|---|---|
| Fotogramas presentados (límite `T123_FRAMES=600`) | 600, salida limpia con código 0 |
| Llamadas Win32 | 258 083 |
| Tiempo hasta el límite | 21,4 s (con `-DT123_TRACE_CALLS` y vsync) |
| *Draw calls* | ~27 por fotograma en el título; 10 238 en total |
| Heap guest al final | 34 MiB (pico vivo por debajo de 40 MiB) |
| Texturas creadas (`D3DXCreateTexture`) | 445, con sus píxeles en memoria del host |
| Hilos guest | 11 creados; varios terminan y su hueco se reutiliza |

Comando:

```powershell
$env:T123_FRAMES = '600'; python recomp/build_host.py --run
```

## Qué hizo falta (F2.1–F2.2)

- **Hilos reales** ([threads.c](../recomp/host/threads.c)): cada hilo guest es un pthread con su `Cpu`, su TIB (`fs:`) y su pila guest. Hay 24 huecos; un hilo que termina libera el suyo. Con 10 huecos fijos, `CreateThread` devolvía 0 y el juego escribía en la dirección 0.
- **COM en memoria guest** ([com.c](../recomp/host/com.c)): las vtables salen de las cabeceras públicas (`gen_vtables.py`). Un método sin implementar detiene el programa y lo nombra.
- **D3D9 → OpenGL** ([d3d9.c](../recomp/host/d3d9.c), [render_gl.c](../recomp/host/render_gl.c)): dispositivo, *swap chain*, texturas y superficies, `DrawPrimitiveUP`, estados de render, *sampler* y etapas. Los efectos D3DX se aceptan, pero se dibujan con la función fija.
- **DirectInput y DirectSound mínimos** ([media.c](../recomp/host/media.c)): `QueryInterface` devuelve un objeto con la vtable pedida (Buffer8, 3DBuffer, 3DListener). Si devolvía el mismo buffer, `SetMinDistance` (3 argumentos) caía en `SetFrequency` (2) y rompía la pila.
- **`memcpy`/`memmove` nativos** ([crt_native.c](../recomp/host/crt_native.c), [natives.txt](../recomp/host/natives.txt)): sus tablas de salto no se podían acotar. El lifter llama a esas direcciones por `guest_call` para que gane la versión nativa.

## Fallos encontrados por el camino

| Síntoma | Causa | Arreglo |
|---|---|---|
| Escritura en 0x0 durante la carga | El heap guest de 96 MiB se agotaba: las texturas vivían en él y los bloques grandes ni se partían ni se fusionaban | Píxeles de textura en memoria del host, con una copia guest solo mientras dura `LockRect`; bloques grandes con partición y fusión; `Release` de texturas y superficies libera |
| `STATUS_BAD_STACK` al salir | El juego presenta desde su propio hilo de render y `host_exit` hacía `longjmp` a `main` desde otro hilo | Desde un hilo secundario se cierra con `exit(finish())` |
| Fotograma negro | El contexto GL solo estaba activo en el hilo que creó el dispositivo, pero dibujan otros dos hilos | Cada llamada de render toma el contexto bajo un cerrojo y lo suelta al salir |

## Texto y teclado (24 oct 2026)

Los módulos de Codex ya están conectados a la capa Win32:

- **Shift-JIS (T7):** `MultiByteToWideChar` y `WideCharToMultiByte` usan `sjis.c` para las páginas de códigos ACP/OEM/932.
- **Glifos (T8):** `CreateFontA` guarda la altura y el peso de la fuente, y `SelectObject` asocia la fuente al DC. `GetTextMetricsA` deriva las métricas de Noto. `GetGlyphOutlineA` (`GGO_GRAY4_BITMAP`) convierte el código Shift-JIS a UTF-16 y rasteriza el glifo con FreeType. La fuente se busca en `T123_FONT`, junto a los DAT o en `local/fonts/`. En 900 fotogramas se rasterizaron 312 glifos sin errores. En PC, FreeType se enlaza de forma estática desde MSYS2. En Vita todavía no hay FreeType: `recomp/vita/glyph_none.c` devuelve `GDI_ERROR`, como antes.
- **Teclado (T9):** `IDirectInputDevice8A::GetDeviceState` del teclado (`GUID_SysKeyboard`) se rellena con `render_keyboard_state`. En PC usa los scancodes de SDL traducidos a códigos DIK; en Vita, los botones (`sceCtrlPeekBufferPositive`) se traducen a las teclas por defecto de Soku.

**Comprobado en PC:** con `T123_PRESS=700-706:29`, la tecla Z queda pulsada en los fotogramas 700–706. En el fotograma 1 200 se ve el **menú principal** (Story Mode, Arcade Mode, Vs Com…). En la misma ejecución sin pulsación, sigue el título.

## Primera pelea en PC (24 oct 2026)

Ejecución sin intervención manual, con pulsaciones por script:

```powershell
$z = (1150..1900 | ? { $_ % 60 -eq 10 } | % { "$_-$($_+5):29" }) -join ','
$env:T123_FRAMES = '2600'
$env:T123_PRESS = "700-706:29,900-904:81,940-944:81,1000-1006:29,$z"   # Z, ↓, ↓, Z y luego Z cada segundo
$env:T123_CAPTURE = '1100,1300,1500,1700,1950,2200,2400,2599'           # guarda frame-<n>.bmp
```

**Recorrido:** título → menú → Vs Com → selección de personaje (Reimu contra Sanae, controlada por la CPU) → **pelea** en el escenario del santuario. La pelea tiene el HUD completo: vida, reloj de clima (黄砂, 梅雨, 極光, 快晴), orbes de espíritu, cartas y contador de combo («4 HIT, Damage 714, Rate 78 %»). La CPU ataca y los golpes hacen daño. Salida limpia en el fotograma 2 600, con unas 120 *draw calls* por fotograma en pelea.

Dos fallos encontrados por el camino:

| Síntoma | Causa | Arreglo |
|---|---|---|
| El juego se quedaba congelado en el fotograma ~1 440 (selección de personaje) | El hilo de carga 0x43e5e0 moría con una división entre cero en 0x411e6a. El juego divide los bytes de `GetGlyphOutlineA` entre la altura del glifo, y para un espacio nuestro rasterizador daba una caja de 0×0 | Como GDI, se informa una caja de 1×1 sin bits ([other.c](../recomp/host/other.c)) |
| Bloqueo mutuo posible entre el hilo que dibuja y el que libera texturas | `upload` toma el cerrojo GL y luego el de texturas; `Release` los tomaba en el orden contrario | `Release` libera la textura GL antes de tomar el cerrojo de texturas ([d3d9.c](../recomp/host/d3d9.c)) |

En pelea quedan 301 MiB de texturas vivas en PC, porque se precargan todos los personajes. En la Vita eso cabe solo comprimido; hay que medirlo allí.

## H3: primera imagen en la Vita real (24 oct 2026)

- `render_gl.c` compila en las dos plataformas; en Vita usa vitaGL (instalado con `vdpm`, junto con vitaShaRK, mathneon, taihen y SceShaccCgExt). Los shaders se compilan en la consola con `ur0:data/libshacccg.suprx`.
- **Error encontrado:** `vglInitWithCustomSizes` no devuelve si tuvo éxito, sino si tuvo que bajar la resolución (`GL_FALSE` tras un arranque normal). Al tratarlo como un fallo, el juego reintentaba `CreateDevice`, el segundo `vglInit` sí fallaba porque vitaGL ya estaba iniciado, y aparecía «D3Dデバイスの作成に失敗».
- **Memoria (medido en la Vita):** antes de vitaGL quedan libres 32 MiB de RAM, 110 MiB de CDRAM y 26 MiB de memoria física contigua; después, 11, 14 y 10 MiB. vitaGL recibe *pools* fijos: 16 MiB de RAM, 80 MiB de CDRAM y 16 MiB de memoria contigua. El *pool* de texturas comprimidas es de 24 MiB y llega a un máximo de 13,1 MiB en 60 s.
- **Resultado:** 3 600 fotogramas y salida limpia. La captura muestra la pantalla de carga («東方Project / 12.3th Project Shrine Maiden / Presented by…»), centrada en 4:3.
- **Pendiente:** en 60 s todavía no llega al título (1 *draw* por fotograma). En Vita3K, que corre en un PC más rápido, llegaba hacia el fotograma 1 200. Falta medir dónde se va el tiempo de carga: lectura de los DAT, compresión zlib o código traducido.

## Carga en la Vita real (24 oct 2026)

Medido con el tiempo de host por API y método COM, y con la marca `first busy frame` en la traza:

| Ejecución | Primer fotograma | Título | Mayores costes |
|---|---|---|---|
| `-O1` | 26 s | no llega en 60 s: `pthread_create` falla (EAGAIN) en 3 hilos de carga | `ReadFile` 44 s, `UnlockRect` 18 s, `CreateFileA` 7 s |
| `-O2`, pilas de hilo de 1 MiB, *pool* RAM de vitaGL de 8 MiB, búfer de lectura de 32 KiB, reutilización de archivos | 18,9 s | **72 s** | `UnlockRect` 25 s, `ReadFile` 11,7 s, `CreateFileA` 8,7 s |
| Traza volcada una vez por segundo (antes, un `fflush` por línea, unos 10 ms cada uno) | 15,4 s | **63 s** | `UnlockRect` 30,7 s, `ReadFile` 13,6 s, `SetFilePointer` 7,6 s |

| Compresión de texturas en dos hilos de trabajo; la textura se lee de su copia sin comprimir hasta que termina | 13,1 s | **41,9 s** | `ReadFile` 18,9 s, `SetFilePointer` 8,8 s (unos 7 ms por posicionamiento) |

Siguiente cambio, todavía sin medir en la Vita: los archivos de solo lectura ya no pasan por stdio, porque stdio vaciaba y rellenaba su búfer en cada `fseek`. Ahora el posicionamiento solo cambia un número, las lecturas pequeñas salen de un bloque de 32 KiB en caché y las grandes van directas a la tarjeta (`sceIoPread`). Los archivos ociosos se siguen reutilizando. En PC, hasta la pelea: `SetFilePointer` 0 ms y 413 000 `ReadFile` en 210 ms. Para probar en PC la ruta de texturas de la Vita existe `python recomp/build_host.py --packed-textures`.

**Problema abierto:** con compresión asíncrona, 2 de 6 ejecuciones en PC hasta la pelea fallaron con «invalid parameter» del CRT dentro de `free` (0x81ff7c, llamado desde 0x402970), en los fotogramas 2074 y 2286. Las ejecuciones sin compresión (0 de 6) y con compresión síncrona (`T123_PACK_SYNC=1`, 0 de 1) no fallaron. Es una carrera que aún no he localizado. `HeapFree` y `HeapSize` registran ahora cualquier puntero que no sea un bloque vivo, con su cabecera.

## Pendiente (no forma parte de H2)

- Efectos D3DX reales (la función fija basta para el título), FreeType en Vita y salida de audio.
- **Vita:** el VPK compila con un *backend* de render vacío ([render_vita.c](../recomp/vita/render_vita.c)); vitaGL llega con H3.

## Vita3K con hilos reales

- **Medido:** en VitaSDK, `_Thread_local` da la misma dirección en todos los hilos (sonda en Vita3K: `0x8400066c` en el principal y en los hilos 1–4). Los hilos se pisaban `guest_current_target`, así que un `ReadFile` se despachaba como otra API. El arranque fallaba de forma no determinista justo después de abrir `th123a.dat`: con una excepción C++ o con un parámetro inválido de `strcat_s`/`strcpy_s`.
- **Arreglo:** el estado por hilo del runtime está en un bloque `GuestThread`. En PC es `_Thread_local`; en Vita, una clave pthread ([guest.h](../recomp/runtime/guest.h)). La `Cpu` de cada hilo vive en su `Thread`.
- **Resultado:** Vita3K pasa ahora por D3D9, DirectInput y DirectSound y entra en la carga de recursos. Después se cae **el propio Vita3K** (lectura de la dirección 0 en su manejador de excepciones del host), no el código guest. Queda sin diagnosticar; hay que probar en una Vita real antes de culpar al emulador.
- `python recomp/build_vita.py --trace-calls` compila con el registro de funciones guest para los informes de fallo.

## Vita real: memoria de texturas (24 oct 2026)

| Prueba | Resultado |
|---|---|
| 300 fotogramas, sin ritmo | Salida limpia en 32,6 s; seguía en la pantalla de carga (1 *draw* por fotograma) |
| 60 s a 60 Hz, píxeles en el heap de C | Volcado `psp2dmp`: `memcpy` desde NULL en `Texture_LockRect`, porque `calloc` agotó los 32 MiB del heap de newlib |
| 60 s, píxeles en un *pool* de 96 MiB de CDRAM | Salida limpia, pero el *pool* se llena (97 976 KiB) y el juego sigue pidiendo texturas de 512×512 |

**Medido en PC tras 3 600 fotogramas** (censo al salir):

- Texturas vivas: **155 MiB**, todas A8R8G8B8; el pico fue de 157 MiB. Las mayores son 54 de 512×512 (54 MiB), 15 de 640×640 (23 MiB), 74 de 256×256, 20 de 470×470 y 237 de 128×128.
- Dibujadas al menos una vez: solo **11,9 MiB**. El resto está precargado.
- Con zlib nivel 1, todas ocupan **15,7 MiB** (unas 10 veces menos, sin pérdida). Con una paleta de 8 bits solo bajarían a 118 MiB: apenas un tercio usa 256 colores o menos.

**Decisión:** en la Vita (`-DT123_PACKED_TEXTURES`), cada textura se guarda comprimida con zlib nivel 1 (la zlib 1.2.3 de T4) dentro del *pool* de CDRAM. Se descomprime en `LockRect` y se vuelve a comprimir en `UnlockRect`. Con vitaGL (H3), al dibujar se descomprimirán solo las texturas en uso, con una caché. Queda por medir en la Vita el coste de CPU de comprimir unos 155 MiB durante la carga.
