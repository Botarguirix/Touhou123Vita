# T3: censo de llamadas COM y estados gráficos

Referencia: `th123.exe` 1.10a, SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. La herramienta rechaza cualquier otro hash antes de analizarlo. Los contextos de instrucciones quedan exclusivamente en `artifacts/pe-inventory/<sha>/com-usage.json`, fuera de git.

Resultado: **195 sitios atribuidos**, 129 con confianza alta y 66 con confianza media. Otros 12,134 sitios indirectos del barrido quedan sin atribuir.

Estos conteos son un **mínimo estático documentado**, no un porcentaje de cobertura COM. Los sitios restantes incluyen IAT, vtables del juego, CRT, datos decodificados linealmente y posibles interfaces aún sin procedencia recuperada. No representan ese número de llamadas COM pendientes. Cero atribuciones a una interfaz tampoco demuestra que no se use.

## Procedencia y confianza

| Interfaz / origen | Evidencia de creación o copia |
|---|---|
| IDirect3D9, `0x8A0E2C` | `Direct3DCreate9` en `0x414EF0`, thunk `0x81F6B8`, IAT `0x8572A0`. En su rama de éxito, EAX alcanza `GetAdapterDisplayMode` en `0x414F27`. |
| IDirect3DDevice9, `0x8A0E30` | Salida de los tres intentos `CreateDevice`, `0x415028/0x415049/0x41506B`. |
| Alias Device9, `0x896B50` | Copia explícita: carga de `0x8A0E30` en `0x401430` y escritura en `0x401435`. Es el campo +4 del renderer `0x896B4C`. |
| IDirect3DSwapChain9, `0x8A0E34` | `GetSwapChain` en `0x4150C7`, slot 14 de Device9. **No es IDirect3DSurface9**. |
| IDirectInput8A, `0x8A019C` | `CoCreateInstance` en `0x40D655`; IID en `0x86777C`, `bf798030-483a-4da2-aa99-5d64ed369700`. |
| InputDevice8A, `0x8A01A0` y `0x8A01A4` | Salidas de `CreateDevice` en `0x40D854` y `0x40DB07`. El segundo slot se descubre automáticamente por su argumento de salida absoluto. |
| IDirectSound8, `0x8A0FCC` | `CoCreateInstance` en `0x41883A`; IID en `0x8676AC`, `c50a7e93-f395-4834-9ef6-7fa99de50966`. |
| IDirectSoundBuffer, `0x8A0FC8` | Salida absoluta de `CreateSoundBuffer` en `0x41899D`, recuperada automáticamente. El tipo devuelto es la interfaz base; no se convierte sin prueba en Buffer8. |
| ID3DXEffect, `0x89AB00/0x89AB08` | Campo +4 de objetos `0x89AAFC/0x89AB04`, creados mediante wrapper `0x418190`, llamada D3DX en `0x4181C7`, desde `0x7FB030/0x7FB049`. |
| Texture9 y Surface9 locales | `D3DXCreateTexture` en `0x40907B/0x409453`; loads revisados `0x4090A5/0x409481`. `GetSurfaceLevel` en `0x405250`, seguido de Surface9 `GetDesc` en `0x405261` y `Release` en `0x40527F`. |

**Alta:** cadena local desde un global de interfaz conocido y argumento `this` coincidente. Es confianza en la atribución estática; no implica que ese sitio se haya ejecutado en una partida.

**Media:** procedencia interprocedural, campo revisado o camino que cruza ramas. El CFG acotado une registros por igualdad, mantiene alternativas de constantes y descarta un receptor si una ruta lo invalida. Las anotaciones de campos y retornos se identifican explícitamente en la herramienta; no se deduce una interfaz por el offset aislado de una llamada.

**Sin atribuir:** no se inventa una interfaz. Cada sitio correspondiente en el JSON tiene `confidence=unassigned` y un motivo.

Los helpers `0x4010F0/0x401130` reciben el renderer desde callers `0x4704BD/0x433EEF`; `0x404AD0/0x404AF0` desde `0x41E1BB/0x41E177`. Los cuatro callers cargan ECX=`0x896B4C`. Esto justifica el Device9 de su campo +4 y las atribuciones medias de dibujo/filtrado. Los wrappers de efecto y buffer de sonido también tienen anotaciones revisadas y limitadas a sus entradas/loads concretos.

## Métodos por interfaz

Una fila cuenta direcciones de callsite, no llamadas por frame. Las columnas separan las dos confianzas; el JSON conserva cada dirección y su procedencia. El orden de las vtables está incluido en la herramienta y corresponde a los encabezados públicos `d3d9.h`, `d3dx9effect.h`, `dinput.h` de `local/SokuLib/directx/` y `dsound.h` de MinGW. Se añade SwapChain9 para evitar etiquetarlo como Surface9 y SoundBuffer base para distinguirlo de Buffer8.

### ID3DXEffect

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| Release | 0 | 2 | 2 |
| SetFloat | 12 | 0 | 12 |
| SetVector | 5 | 0 | 5 |
| Begin | 6 | 0 | 6 |
| BeginPass | 6 | 0 | 6 |
| CommitChanges | 6 | 0 | 6 |
| EndPass | 6 | 0 | 6 |
| End | 6 | 0 | 6 |
| OnLostDevice | 0 | 1 | 1 |
| OnResetDevice | 0 | 1 | 1 |

### IDirect3D9

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| Release | 0 | 1 | 1 |
| GetAdapterDisplayMode | 0 | 1 | 1 |
| CreateDevice | 3 | 0 | 3 |

### IDirect3DDevice9

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| Release | 0 | 1 | 1 |
| TestCooperativeLevel | 0 | 1 | 1 |
| GetDeviceCaps | 1 | 0 | 1 |
| GetSwapChain | 2 | 0 | 2 |
| Reset | 1 | 0 | 1 |
| BeginScene | 1 | 0 | 1 |
| EndScene | 0 | 1 | 1 |
| Clear | 5 | 0 | 5 |
| SetRenderState | 19 | 15 | 34 |
| SetTexture | 10 | 0 | 10 |
| SetTextureStageState | 0 | 1 | 1 |
| SetSamplerState | 0 | 6 | 6 |
| DrawPrimitiveUP | 7 | 4 | 11 |
| SetFVF | 7 | 4 | 11 |

### IDirect3DSurface9

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| Release | 0 | 1 | 1 |
| GetDesc | 0 | 1 | 1 |

### IDirect3DSwapChain9

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| Release | 0 | 2 | 2 |
| Present | 2 | 0 | 2 |

### IDirect3DTexture9

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| GetSurfaceLevel | 0 | 1 | 1 |
| LockRect | 0 | 2 | 2 |
| UnlockRect | 0 | 2 | 2 |

### IDirect3DVertexBuffer9

Sin sitios atribuidos; no demuestra ausencia de uso.

### IDirectInput8A

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| Release | 0 | 1 | 1 |
| CreateDevice | 3 | 0 | 3 |
| EnumDevices | 0 | 1 | 1 |
| Initialize | 1 | 0 | 1 |

### IDirectInputDevice8A

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| Release | 2 | 0 | 2 |
| SetProperty | 1 | 0 | 1 |
| Acquire | 4 | 0 | 4 |
| Unacquire | 0 | 2 | 2 |
| GetDeviceState | 0 | 2 | 2 |
| SetDataFormat | 2 | 0 | 2 |
| SetCooperativeLevel | 2 | 0 | 2 |

### IDirectSound8

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| Release | 0 | 1 | 1 |
| CreateSoundBuffer | 2 | 0 | 2 |
| GetCaps | 1 | 0 | 1 |
| SetCooperativeLevel | 2 | 0 | 2 |
| Initialize | 1 | 0 | 1 |

### IDirectSoundBuffer

| Metodo | Alta | Media | Total |
|---|---:|---:|---:|
| QueryInterface | 1 | 1 | 2 |
| Release | 1 | 5 | 6 |
| Lock | 0 | 3 | 3 |
| Play | 1 | 0 | 1 |
| Unlock | 0 | 2 | 2 |

### IDirectSoundBuffer8

Sin sitios atribuidos; no demuestra ausencia de uso.


## Estados constantes recuperados

| RenderState (ID) | Valores ligados a ese ID sin ambiguedad |
|---|---|
| ZENABLE (7) | 0, 1 |
| ZWRITEENABLE (14) | 0, 1 |
| ALPHATESTENABLE (15) | Valor dinamico/no resuelto |
| SRCBLEND (19) | 1, 5 |
| DESTBLEND (20) | Valor dinamico/no resuelto |
| CULLMODE (22) | 1 |
| ZFUNC (23) | 1 |
| ALPHAREF (24) | 1 |
| ALPHAFUNC (25) | 7 |
| ALPHABLENDENABLE (27) | Valor dinamico/no resuelto |
| STENCILENABLE (52) | 0, 1 |
| STENCILFAIL (54) | 3 |
| STENCILPASS (56) | 5, 8 |
| STENCILFUNC (57) | Valor dinamico/no resuelto |
| STENCILMASK (58) | 255 |
| BLENDOP (171) | 1, 3 |

TextureStageState: stage 0, ALPHAOP (4) = MODULATE (4), sitio `0x404D48`.

SamplerState: stage 0, MAGFILTER (5) y MINFILTER (6) = POINT (1) o LINEAR (2); MIPFILTER (7) = POINT (1). El helper `0x404AEB` recibe argumentos dinamicos.

Las rutas de mezcla usan un switch de dos niveles en `0x404BA7`: 35 selectores en `0x404CB8`, que eligen entre 14 entradas de `0x404C80`. El helper de profundidad/stencil usa cuatro entradas de `0x405014`, salto en `0x404E49`. La herramienta valida su codificación y que los destinos estén en `.text`, y recorre ambos CFG. No quedan saltos indirectos sin resolver dentro de esos helpers analizados; esto no demuestra haber resuelto los switches del resto del juego.

`constant_arguments` contiene solo constantes únicas recuperadas; `None` significa no resuelto. `constant_argument_choices` conserva alternativas por argumento después de unir ramas. Son **conjuntos marginales**, no un producto cartesiano de combinaciones demostradas ni una recuperación de las guardas de configuración. En particular, los sitios comunes `0x404C1A/0x404C76` pueden recibir diferentes IDs de estado; no se asignan todos sus posibles valores a cada ID como si fueran pares probados.

## Contrato mínimo para la capa Vita

- Device9/SwapChain9: creación y capabilities coherentes; `TestCooperativeLevel`, `Reset`, `GetSwapChain`, `BeginScene`, `EndScene`, `Clear`, `Present` y liberación. Mantener la identidad y el orden correctos de ambas vtables.
- Dibujo: `SetFVF`, `DrawPrimitiveUP`, `SetTexture`, y conversión de los layouts de vértices usados. El backend debe consumir la memoria suministrada al draw; no asumir un VertexBuffer9 porque haya posiciones, UV y color.
- Estado gráfico: blending y operación de mezcla, alpha test/ref/func, depth test/write/func, stencil enable/fail/pass/func/mask, culling, combiner de textura y filtros de sampler. Preservar alpha y orden de composición; aceptar un ID y descartarlo silenciosamente no reproduce el renderer.
- Recursos: creación D3DX de texturas, `GetSurfaceLevel`, `GetDesc`, `LockRect`, `UnlockRect`, pitch y lifetime/Release compatibles. La creación D3DX usa además la capa de efectos documentada por T2.
- Efectos: `SetFloat`, `SetVector`, ciclo `Begin/BeginPass/CommitChanges/EndPass/End`, `OnLostDevice`, `OnResetDevice` y Release, además de los programas/parámetros recuperados en T2.
- Entrada y audio: crear/enumerar dispositivos, formato/propiedades/cooperación/adquisición/estado y buffers de sonido con QueryInterface/Play/Lock/Unlock/lifetime. El mínimo atribuido no cierra los otros métodos de audio ni las interfaces 3D consultadas por QueryInterface.

Para VertexBuffer9 y Buffer8 no hay atribuciones suficientes en este modelo. La herramienta incluye sus tablas de nombres, pero no afirma ausencia de uso ni marca sus métodos como implementados. Nuevas rutas deben fallar visiblemente hasta tener soporte y pruebas; este censo no sustituye la cobertura del lifter ni un replay de referencia.

## Verificación y límites

```powershell
python -m unittest tests.test_com_usage_census -v
python tools/com_usage_census.py
python -m py_compile tools/com_usage_census.py tests/test_com_usage_census.py
git diff --check
```

La suite específica verifica offsets distintos según interfaz, procedencia de device/input/audio/texture/surface, constantes de estado, propagación por CFG, pérdida de tipo ante una ruta o registro parcial que lo modifica, alineación de argumentos desde ESP y rechazo de PE incorrecto. Los casos que necesitan `original/th123.exe` usan skipUnless si falta. La herramienta usa argparse y no añade dependencias.

El barrido lineal puede decodificar datos; el análisis no es un points-to global, no sigue todos los arrays ni reconstruye los receptores de todo el código del juego. Los helpers CFG tienen límites explícitos y sus cortes figuran en el JSON. No se ejecutaron Windows/D3D9, Vita3K ni hardware para T3, ni se cambió `recomp/`, CMake o el renderer. Los conteos son evidencia de interfaces y estados a cubrir, no una prueba de que la capa Vita ya funcione.

Resultados medidos: 11 pruebas, `OK` (13,968 s); CLI exit 0, `py_compile` exit 0. Dos generaciones consecutivas del JSON produjeron SHA-256 `2e589e78b96b5172b4f1a60f3bef829da559cb152dc72e389c5a5220f8ae717d`. `git diff --check` y revisión de los archivos preparados sin errores de espacios. No se declara validación dinámica de esas 195 llamadas.
