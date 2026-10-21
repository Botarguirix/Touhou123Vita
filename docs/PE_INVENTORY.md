# Inventario del PE para la recompilación estática (F0)

Fecha: 21 de octubre de 2026. Fase F0 del [roadmap de recompilación](ROADMAP_RECOMP.md).

Este documento solo contiene metadatos agregados. Las salidas completas (`inventory.json`, `strings.txt`, `functions.tsv`) se generan localmente en `artifacts/pe-inventory/<sha>/` y no se publican.

Reproducción:

```powershell
python tools/pe_inventory.py
./tools/export-functions.ps1 -GhidraHome <ghidra_12.1.4> -JdkHome <jdk-21>
```

## Identidad

| Campo | Valor |
|---|---|
| SHA-256 | `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` |
| Versión | Cadenas `Ver1.10a` y `th123_110a`; timestamp PE 2011-09-16 |
| Tamaño | 4 816 896 bytes, PE32 i386, GUI |
| Base / entrada | `0x00400000` / `0x008218b2` |
| Relocaciones | **No hay**: la imagen debe ir en su base original (o con un desplazamiento fijo) |
| TLS callbacks / exports | No / 0 |
| Recursos | Un icono, un grupo de iconos y un manifest |

## Secciones y empaquetado

| Sección | VA | Tamaño virtual | Entropía |
|---|---|---|---|
| `.text` | `0x00401000` | 4 542 539 | 6,34 |
| `.rdata` | `0x00857000` | 175 610 | 5,40 |
| `.data` | `0x00882000` | 131 464 (86 016 en disco) | 6,25 |
| `.rsrc` | `0x008a3000` | 1 084 | 3,99 |

No está empaquetado ni protegido. Los nombres de sección y la entropía son los normales de MSVC, y la IAT es legible.

## Toolchain

Según el Rich header, el enlazador es la versión 8.0 y la mayoría de los objetos se compilaron con **Visual Studio 2005 RTM (14.0.50727)**. También hay objetos de VS2003 SP1 (13.10.4035), probablemente bibliotecas estáticas de terceros, e import libs de VS6.

**El CRT está enlazado estáticamente**: no se importa ninguna `MSVCR*.dll`. Las funciones del CRT forman parte del código que se traduce, y las más usadas (memcpy, rutinas matemáticas, `_ftol`, heap) son candidatas a reemplazarse por versiones nativas.

Bibliotecas embebidas que se pueden reemplazar por compilaciones nativas de la misma versión:

- **zlib 1.2.3** (cadenas de copyright de deflate/inflate)
- **libpng** (mensajes de libpng)
- **libogg/libvorbis** (la BGM está en `.ogg`; aparece la cadena `vorbis`)

## Importaciones: 171 funciones de 10 DLL

| DLL | Funciones | Uso y sustituto previsto en Vita |
|---|---|---|
| KERNEL32 | 105 | Archivos, heap, hilos, eventos, secciones críticas, TLS, tiempo, locale y consola del CRT → SceIo, SceKernel y un heap propio |
| USER32 | 31 | Ventana, bucle de mensajes, `MessageBoxA`, portapapeles, `wsprintfA` → ventana falsa y cola de mensajes mínima |
| WS2_32 | 14 | Sockets UDP (`sendto`/`recvfrom`) para netplay → stub en v1, SceNet en v2 |
| GDI32 | 6 | `CreateFontA` + `GetGlyphOutlineA`: **el juego rasteriza el texto con GDI** → rasterizador propio (ver riesgos) |
| IMM32 | 4 | Entrada IME de nombres de perfil → diálogo IME de Vita |
| d3dx9_33 | 4 | `D3DXCreateEffect`, `D3DXCreateTexture` y dos funciones de vectores |
| ole32 | 3 | `CoCreateInstance` para DirectSound8 y DirectInput8 |
| WINMM | 2 | `timeGetTime`, `timeBeginPeriod` |
| d3d9 | 1 | `Direct3DCreate9`; el resto pasa por las vtables COM |
| imagehlp | 1 | `MakeSureDirectoryPathExists` |

Los sitios de llamada más frecuentes son secciones críticas (87/68), `wsprintfA` (73), `CloseHandle` (46), `MessageBoxA` (27), eventos (`WaitForSingleObject` 24, `SetEvent` 21) y E/S de archivos. `LoadLibraryA`/`GetProcAddress` solo se usan para DLL del CRT (`mscoree.dll`, `kernel32`, `user32`); no se cargan otras DLL dinámicamente.

### COM y DirectX

GUID presentes en el binario:

- **Audio:** `CLSID_DirectSound8`, `IID_IDirectSound8` e `IID_IDirectSoundBuffer8`.
- **Entrada:** `CLSID_DirectInput8`, `IID_IDirectInput8A`, `GUID_SysKeyboard` y `GUID_SysMouse`. Los mandos se enumeran mediante DirectInput8; no se usa WINMM ni XInput.
- **Gráficos:** el binario incluye **3 efectos D3DX compilados** (blobs `fx` con firma `0xFEFF0901`) y 17 cadenas del compilador de shaders de D3DX9, con perfiles `vs_1_1`. Hay que reescribir esos tres efectos para vitaGL; el resto del render es D3D9 de función fija, que se cubre con la capa D3D9.

### Archivos y configuración

El ejecutable hace referencia a `data/...dat` (escenas y menús dentro de los DAT), `config123.dat`, `Profile1P.dat`, `Profile2P.dat`, `score123.dat`, replays `.rep` y archivos `.ini` (`GetPrivateProfile*`). Todo se mapea a `ux0:data/touhou123vita/`.

## Código

### Barrido lineal (Capstone, `.text` completa)

| Medida | Valor |
|---|---|
| Instrucciones | 1 252 622 |
| Mnemónicos distintos | 309 |
| x87 | **297 425 (24 %)**: `fstp` 101 k, `fld` 79 k, `fadd` 28 k, `fild` 15 k, `fnstsw` 11 k… |
| Cambios de control word (`fldcw`) | 290 |
| SSE / MMX | 962 / 9 (CRT) |
| Accesos a `fs:` (SEH y EH de C++) | 2 485 |
| `jmp [reg*4+tabla]` (switch) | 1 199 sitios |
| Llamadas indirectas por registro (vtables) | 11 574 |
| `lock` / `rep` | 49 / 202 |

El barrido también decodifica datos incrustados en `.text` (tablas de switch): 1 303 bytes no decodificables más `in`/`out`/`hlt`/`int` espurios. El lifter debe separar código y datos y no traducir en lineal.

### Proyecto Ghidra existente (`ExportFunctions.java`)

| Medida | Valor |
|---|---|
| Funciones | 5 558 (52 thunks) |
| Bytes / instrucciones dentro de funciones | 2 373 716 / 661 336 |
| **Instrucciones fuera de cualquier función** | **494 845** |
| Funciones con x87 / SSE / `fs:` | 710 / 16 / 758 |
| Funciones con saltos calculados | 309 |

**Hallazgo clave:** cerca del 47 % de `.text` (2,15 MB en 1 726 huecos que no son padding) queda fuera de las funciones de Ghidra. Los huecos se concentran entre `0x490000` y `0x800000`, que es el código de los personajes.

Ejemplo: el update de Reimu `0x490490` aparece con 2 089 bytes, y justo al terminar (`0x490cb9`) empieza un hueco de 94 567 bytes. Ghidra no resolvió sus switch y truncó el cuerpo de la función. Además, 509 punteros de `.rdata`/`.data` apuntan dentro de esos huecos.

Consecuencia: **la base de Ghidra no sirve como lista de funciones para el lifter.** F1 necesita un descubrimiento propio de funciones y switch (patrón MSVC `jmp [reg*4+tabla]`, tablas `movzx` de dos niveles, vtables y punteros en datos). Ghidra se usará como referencia cruzada.

## Riesgos detectados en F0

1. **x87 y determinismo.** El 24 % de las instrucciones son x87 y hay 290 `fldcw`. D3D9 reduce la FPU a precisión simple salvo que el dispositivo se cree con `D3DCREATE_FPU_PRESERVE`. **F1 debe verificar las flags de `CreateDevice`:** si el juego corre a 24 bits, emularlo con `float` en ARM es más fiel y más rápido que con `double`. Esto es decisivo para que los replays de PC se reproduzcan idénticos.
2. **Excepciones de C++ y SEH.** Hay 758 funciones con frames `fs:[0]` y se importan `RaiseException`/`RtlUnwind`. El runtime necesita un TIB falso y desenrollado para `throw` (el proyecto ya tiene trazas de rutas de throw en `artifacts/ghidra/pe-throw-path.tsv`).
3. **Texto con GDI.** `GetGlyphOutlineA` rasteriza glifos (Shift-JIS) en tiempo de ejecución. En Vita hace falta un sustituto: FreeType con una fuente japonesa, o una caché de glifos generada en PC con la fuente del usuario.
4. **Hilos.** `CreateThread` aparece en 6 sitios (carga y audio), además de eventos y secciones críticas. El runtime necesita hilos reales con contexto y pila de guest propios.
5. **Tamaño.** 1,25 millones de instrucciones generan bastante más C que el ejemplo de Isaac por función. Hay que vigilar el tiempo de compilación y el tamaño del `eboot`, por ejemplo agrupando unidades de traducción como repentogxm.

## Decisión

**Se sigue con la ruta D (recompilación estática).** Nada en el inventario la bloquea:

- El binario no está protegido y su superficie de plataforma es pequeña y conocida (171 importaciones, DirectX 9 y DirectSound/DirectInput 8 por COM, solo 3 efectos de shader).
- La falta de relocaciones simplifica el mapeo de memoria.

Ajustes al plan de F1:

- El primer entregable de F1 es el **descubrimiento propio de funciones y switch**, con un criterio medible: cubrir al menos el 99 % de los bytes no-padding de `.text` y explicar el resto.
- Antes de elegir el modelo x87 hay que **verificar las flags de `CreateDevice` y el control word** que deja D3D9.
- El primer lifter se sigue validando con el oráculo de 4 096 casos del kernel de animación, como estaba previsto.
