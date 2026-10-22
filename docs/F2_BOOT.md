# F2.0: arranque del CRT y de WinMain traducidos en PC

Fecha: 21 de octubre de 2026. Primer paso de F2 en el [roadmap de recompilación](ROADMAP_RECOMP.md).

**Resultado:** el código original traducido arranca desde el punto de entrada del PE (`0x8218b2`):

- completa la inicialización del CRT de MSVC 2005;
- entra en `WinMain` (`0x7fb590`), registra la clase de ventana y crea la ventana con el título del juego;
- **abre y parsea los índices de `th123a/b/c.dat`**;
- llega a `Direct3DCreate9`.

Allí se detiene a propósito, porque la capa gráfica todavía no existe (F2.2). El juego reacciona como el original cuando falla DirectX: muestra sus propios mensajes de error.

```powershell
python recomp/lift_all.py                  # C generado (una vez)
python recomp/build_host.py --run          # compila el host, ejecuta y escribe run/host-trace.log
```

## Qué se ejecutó (traza de esta ejecución)

| Etapa | Evidencia en `host-trace.log` |
|---|---|
| `__security_init_cookie` | `GetSystemTimeAsFileTime`, `GetCurrentProcessId`, `GetCurrentThreadId`, `GetTickCount`, `QueryPerformanceCounter` |
| `_heap_init`, `_mtinit` | `HeapCreate` y `GetProcAddress` de `FlsAlloc`/`EncodePointer`/…, que devuelven 0 como en Windows XP. El CRT pasa a TLS (`TlsAlloc` + 866 `TlsGetValue`) |
| `_ioinit`, entorno, argumentos | `GetStartupInfoA`, `GetStdHandle`, `GetCommandLineA`, `GetModuleFileNameA`, `GetCPInfo`/`GetACP` (código de página 932) |
| `_cinit`: constructores globales de C++ | 16 `InitializeCriticalSectionAndSpinCount`, un `CreateThread` (entrada `0x4192a0`, todavía no se arranca) |
| `WinMain` | `timeBeginPeriod`, `CoInitialize` y `CreateMutexA("東方非想天則")` (instancia única); `SetCurrentDirectoryA`; `RegisterClassExA("th123_110a", wndproc 0x7fb560)`; `CreateWindowExA("東方非想天則 ～ 超弩級ギニョルの謎を追え Ver1.10a", 640×480)`; `GetFileAttributesA(configex123.ini)` |
| Archivos del juego | `CreateFileA` de `th123a.dat`, `th123b.dat` y `th123c.dat` (los del usuario), 9 `ReadFile` y **54 163 `HeapAlloc`**: el código original construyó en memoria el índice de los archivos |
| Gráficos | `Direct3DCreate9(32)` (desde `0x414ed0`), que devuelve NULL a propósito; `MessageBoxA("DirectX-Error", "D3Dオブジェクトの作成に失敗")` y `MessageBoxA("Error", "初期化失敗")` |
| Después | El juego sigue con `ShowWindow`, `SetEvent` y `SetThreadPriority` y termina leyendo la dirección guest `0x40`, un puntero de dispositivo nulo. Es el límite esperado sin gráficos |

En total hubo unas 55 000 llamadas Win32 a 66 funciones distintas, sin ningún `guest_fault` del código traducido antes del punto de D3D.

## Capa de host (`recomp/host/`, C portable sin llamadas a Win32)

| Pieza | Descripción |
|---|---|
| `main.c` | Carga el PE del usuario, construye TIB/PEB en `fs:` (cadena SEH, límites de pila, ranura TLS, PEB con ImageBase), pila guest de 2 MB y CW x87 inicial `0x027F`. Ejecuta el punto de entrada. En Windows, un manejador de excepciones convierte un acceso inválido del host en **dirección guest + últimas 64 funciones guest ejecutadas** |
| `support.c` | IAT con **direcciones falsas** por importación (`0x7F000000 + 16·i`): `call [IAT]`, punteros cargados de la IAT y `GetProcAddress` llegan al mismo despachador. Heap guest con clases de tamaño, `VirtualAlloc` en región propia, tabla de handles, rutas guest `C:\th123\…` → directorio de datos del usuario, conteo por API y anillo de las últimas 64 llamadas |
| `kernel32.c` | ~90 funciones: heap, TLS dentro del TIB, módulos (`kernel32`/`user32` existen y `mscoree.dll` no, como sin .NET), Interlocked atómicos, archivos con `fopen`, `GetPrivateProfile*` que lee el `.ini` del usuario, código de página 932, conversiones (solo ASCII por ahora), Windows XP SP3 como versión |
| `other.c` | WINMM, USER32 (ventana como handle, `MessageBoxA` a la traza, `wsprintfA` con varargs del guest), GDI32 (`CreateFontA` registrado y `GetGlyphOutlineA` pendiente de T5), IMM32, OLE32 (`CoCreateInstance` aún falla), WS2_32 y `Direct3DCreate9` → NULL |
| `recomp/build_host.py` | Compila el host y reutiliza los objetos generados (los recompila si cambia `guest.h`), con `-DT123_TRACE_CALLS` |

Cambios en el runtime y el lifter:

- `guest_call_import` va por el contenido de la IAT.
- `guest_invoke` para callbacks del host al guest (ventanas, hilos).
- Intercepciones ordenadas con búsqueda binaria; también pueden sustituir funciones traducidas.
- `T123_ENTER` al inicio de cada función, vacío salvo en los builds de depuración.
- Instrucciones de cadena con **DF=1** (el CRT busca `\` hacia atrás con `std; repne scasb`), validadas en `tests/test_recomp_instructions.py`.

## Errores encontrados durante el arranque

- `InitializeCriticalSectionAndSpinCount` (pedida por `GetProcAddress`) compartía el stub de un argumento de `InitializeCriticalSection` y desalineaba la pila. Un número de argumentos stdcall equivocado es la causa más probable de los fallos de esta capa, así que cada API nueva debe revisarse contra su firma.
- `rep scas`/`movs`/`stos` con DF=1 no estaban implementados.

## Pendiente (siguiente paso F2.1 / F2.2)

- **Hilos reales:** el `CreateThread` del arranque (`0x4192a0`) y los que vengan, con secciones críticas y eventos de verdad.
- **Ventana y mensajes:** `CreateWindowExA` debe enviar `WM_CREATE` y demás a la wndproc guest (`0x7fb560`) con `guest_invoke`.
- **D3D9:** objeto COM `IDirect3D9`/`IDirect3DDevice9` con los métodos que mida T3, sobre OpenGL/SDL2. Es el siguiente bloqueo real.
- **Texto Shift-JIS:** tablas de conversión 932 ↔ UTF-16; hoy los caracteres no ASCII se convierten como `?` y se registra.
- **Excepciones de C++:** `RaiseException` detiene el programa. Todavía no ha aparecido.
