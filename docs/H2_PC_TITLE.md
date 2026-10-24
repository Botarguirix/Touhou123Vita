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

## Pendiente (no forma parte de H2)

- Efectos D3DX reales (la función fija basta para el título), Shift-JIS en `MultiByteToWideChar`, `GetGlyphOutlineA` (devuelve `GDI_ERROR`), entrada desde SDL y salida de audio.
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
