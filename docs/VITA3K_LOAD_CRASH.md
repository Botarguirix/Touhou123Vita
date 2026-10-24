# T11: excepción durante la carga en Vita3K

Fecha de las mediciones: **24 de octubre de 2026**, America/Mexico_City.

**Conclusión: fallo de nuestro camino de texturas, confianza alta.** El heap
nativo de newlib se queda sin espacio y `texture_new` conserva un puntero nulo
como datos de una textura. `Texture_LockRect` lo pasa a memcpy sin comprobarlo.
El acceso inválido ocurre dentro del HLE de Vita3K, pero su argumento nulo viene
del programa. No hay evidencia de que la causa sea E/S concurrente o timedwait.
No se corrige aquí: T11 permite crear solamente este informe.

## Versión, entradas y construcción

- Snapshot: rama codex/T11, base `5b01083`; respecto a `4c7abda` solo cambia
  docs/CODEX_TAREAS.md. El código H2 es el solicitado.
- PE: SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.
  El lanzador verifica la copia de ux0 antes de ejecutar.
- Vita3K: **v0.2.1 4190-fab6bfc7**, Windows 10 22H2, Vulkan, GTX 1660 Ti.
- SHA-256 de Vita3K.exe: `a576ac696b2fde9287b743a2aef0c4a2bb04053cd57a41216fdadda2ee599a56`.
- VitaSDK: arm-vita-eabi-gcc 15.2.0. Optimización -O1.
- Configuración aislada en local/vita3k-isolated; su log-level ya era 0 (trace),
  confirmado al inicio de los registros. No hacía falta elevarlo ni modificarla.

Se ejecutaron ambos builds, **pasaron, código 0**:

```powershell
python recomp/build_vita.py --jobs 4
python recomp/build_vita.py --trace-calls --jobs 4
```

El normal se compiló desde el worktree. Para el segundo se ejecutó el mismo
script desde la ruta absoluta del checkout principal, tras comparar todos los
.c/.h/.py/.txt de recomp/: eran idénticos al normalizar finales de línea.
Solo cambian las salidas ignoradas compartidas; no se editaron fuentes del
principal. Ambos construyeron 83 objetos, en 746 y 718 segundos respectivamente.

| VPK local preservado | Bytes | SHA-256 |
|---|---:|---|
| artifacts/t11-crash/normal.vpk | 8 942 548 | `70ee1851d9b9094d3e01426ef068241c5353e10e654bb1dd99c8c1ee076b73d2` |
| artifacts/t11-crash/trace.vpk | 9 057 717 | `f897e0f648a5fc85adf0815e3062de0503f8766a643a2576801a34ab25b8b8e9` |

Se verificó antes de reinstalar que el destino THSV12302 estaba dentro de
artifacts/vitafs/ux0/app, sin junctions internas. Se usó exclusivamente la
instancia aislada y se conservaron las seis salidas antes de cada repetición.

## Reproducibilidad: seis corridas, misma firma

Comando por corrida, con el VPK correspondiente:

```powershell
./tools/vita3k-recomp.ps1 -Vpk artifacts/t11-crash/normal.vpk -TimeoutSeconds 120
./tools/vita3k-recomp.ps1 -Vpk artifacts/t11-crash/trace.vpk -TimeoutSeconds 120
```

**Las seis reprodujeron la excepción** después de sceIoClose del descriptor
0x122. La salida global varía con los hilos: no siempre se termina el proceso
inmediatamente. No confundir el código del wrapper con una carga correcta.

| Variante / corrida | Tiempo externo (s) | Código del wrapper | Resultado nuevo del guest | Excepción |
|---|---:|---:|---|---|
| normal 1 | 18.328 | 0 | 300 Present, código 0, 172679 APIs | Sí |
| normal 2 | 17.453 | 0 | 300 Present, código 0, 172808 APIs | Sí |
| normal 3 | 17.687 | 0 | 300 Present, código 0, 172846 APIs | Sí |
| trace 1 | 19.188 | 0 | 300 Present, código 0, 173021 APIs | Sí |
| trace 2 | 20.859 | 0 | 300 Present, código 0, 174127 APIs | Sí |
| trace 3 | 13.828 | 1 | No se generó; proceso terminó | Sí |

Ejemplo literal de normal 1:

```text
[00:29:42.343] |T| [close_file]: sceIoClose: Closing file fd: 0x122
[00:29:42.343] |C| [logging::exception_handler]: Exception EXCEPTION_ACCESS_VIOLATION (0xC0000005).
[00:29:42.343] |C| [logging::exception_handler]: Read violation at address 0x0.
```

Normal 2/3 registran la misma firma a 00:32:19.946 y 00:32:37.816.
Trace 1/2/3 la registran a 07:27:45.381, 07:28:06.591 y 07:28:24.915.
En cada log está en la línea 1462; el descriptor previo es siempre 0x122.
Eso identifica un punto de carga estable, **no demuestra que falle sceIoClose**.
Su NID es C70B8886 según la [base de VitaSDK](https://github.com/vitasdk/vita-headers/blob/master/db/360/SceIofilemgr.yml).

## Captura del fallo real con GDB

La primera prueba con GDB agotó 90 s durante el arranque sin obtener una pila.
Se repitió desactivando la carga automática de símbolos de DLL y debuginfod;
la captura se obtuvo en 67.33 s. Se hizo una segunda captura que leyó además
las estructuras de memoria del programa. Ninguna cambió su código.

- Hilo host: GDB **Thread 37, nombre pthread**, Thread 17540.0x5e3c en la
  primera captura. No se atribuye sin evidencia a uno de los índices guest 1..7.
- PC host: vcruntime140.dll, instrucción `rep movsb`.
- RSI y RDX: **0**, fuente nula.
- R8 y RCX: **0x100000**, 1 MiB.
- Destino host: **0x48AAB3000**, dirección Vita **0x8AAB3000**.
- R12: **0x14E9DBD7**, NID de **sceClibMemcpy**, corroborado por
  [SceLibKernel de VitaSDK](https://github.com/vitasdk/vita-headers/blob/master/db/360/SceLibKernel.yml).

La captura de memoria de la variante normal, con símbolos de su ELF, dio:

| Medición | Valor |
|---|---:|
| Límite newlib, _newlib_heap_size_user | 33 554 432 bytes (32 MiB) |
| Texturas con dimensiones | 90 |
| Píxeles de texturas con data no nulo | **33 237 500 bytes** |
| Máximo sbrk observado | 33 456 128 bytes |
| Textura que coincide con el destino | **índice 90** |
| Dimensiones / pitch / formato | 512x512 / 2048 / 21 (A8R8G8B8) |
| Puntero nativo data | **0x00000000** |
| Staging guest pixels | **0x02AB3000** |
| guest_base nativo | **0x88000000** |

La suma guest_base + pixels es exactamente 0x8AAB3000, el destino de la copia.
El staging guest existe; la fuente nativa de la textura no. Solo los píxeles
ya reservados dejan menos de 317 KiB del límite de 32 MiB, antes de contar
metadatos y demás reservas: no cabe la nueva textura de 1 MiB.
Los campos de mallinfo salvo arena estaban a cero y no se interpretan como un
recuento actualizado de bytes libres; se sumaron directamente las texturas vivas.

Direcciones **del ELF normal**, no direcciones del PE x86:

- Texture_LockRect: 0x822E962E.
- memcpy: 0x822F6AE8; stub sceClibMemcpy: 0x82303110.
- textures: 0x82332B98, 4096 entradas de 36 bytes.
- guest_base: 0x823813A0; _newlib_heap_size_user: 0x82332058.
- __malloc_current_mallinfo: 0x82387028.

Se preservó normal.elf reenlazando sus 83 objetos, sin recompilar ni cambiar
fuentes. Estas direcciones no deben usarse con trace.elf, cuyo layout difiere.
Los scripts de GDB, pilas y metadatos quedan bajo artifacts/t11-crash/.

## Interpretación y correcciones propuestas

**Confianza alta:** el problema de esta copia está en nuestro programa, por
agotamiento del heap nativo y uso de una textura sin píxeles reservados.
En recomp/host/d3d9.c, texture_new llama calloc sin comprobar su retorno y
entrega el objeto igualmente. Texture_LockRect copia desde t->data sin validar
ni ese puntero ni el resultado de heap_alloc para el staging. La captura coincide
concretamente con el primer fallo; no es el overflow de solicitudes de 4 GiB
hallado por T10 ni agotamiento del heap guest de 96 MiB.

Cambios propuestos para Claude, **no aplicados en T11**:

1. Validar dimensiones, multiplicaciones y retorno de calloc en texture_new.
   Si falla, revertir el slot y devolver un HRESULT de memoria insuficiente,
   sin crear/devolver un objeto parcialmente válido ni S_OK.
2. Validar la reserva de staging y todos los límites de LockRect antes de copiar.
   Propagar el error al guest y dejar el recurso en un estado coherente.
3. Revisar el presupuesto de memoria nativa de H2/H3. El límite de 32 MiB viene
   de H1, cuando el host solo cargaba el exe; ahora también conserva texturas.
   Medir bytes y pico por categoría. Una ampliación, por ejemplo a 64 MiB, es
   una hipótesis de prueba, no una configuración validada en consola: contar
   también los 128 MiB guest, código, stacks, framebuffer y futuro vitaGL.
4. Repetir las mismas corridas tras el cambio y exigir una carga/título real,
   además de Present. No basta con que otro hilo llegue al límite de frames.

No se encontró un uso incorrecto de hora relativa en event_wait: threads.c usa
CLOCK_REALTIME y una fecha absoluta normalizada para pthread_cond_timedwait.
El reuso de handles que muestran las trazas no prueba compartir un FILE desde
varios hilos; no se atribuye una carrera de E/S a esta excepción. Hay otros
aspectos de lifetime y concurrencia que pueden auditarse, pero no son su causa
medida en esta captura.

## Dos limitaciones del método de prueba

Vita3K registra esta excepción mediante AddVectoredExceptionHandler y devuelve
EXCEPTION_CONTINUE_SEARCH: [logging.cpp del commit exacto](https://github.com/Vita3K/Vita3K/blob/fab6bfc7/vita3k/util/src/logging.cpp).
El mensaje por sí solo no prueba terminación instantánea de todo el proceso.
En cinco corridas otros hilos llegaron a frame_limit y produjeron resultado 0
pese al acceso nulo durante la carga. En normal 1 el contador terminó en 421
draws para 300 Present; no se considera prueba de la pantalla de título.

Además, vita3k-recomp.ps1 borra el resultado de ux0 antes de arrancar, pero no
borra la copia anterior en artifacts/.../vita/run. Si la siguiente corrida no
genera resultado, queda allí el anterior. Se detectó en trace 3: su wrapper
informa literalmente `No recomp-result.txt after 13 s (process exited: True)`;
ux0 no tenía resultado y la copia del directorio run conservaba el mismo hash y
mtime de trace 2. En la instantánea se renombró a recomp-result.stale.txt y se
marcó como obsoleto en runs-summary.json; no se atribuye a trace 3.

Propuesta para el lanzador, también fuera del alcance editable: limpiar o aislar
las salidas por corrida, comprobar frescura/procedencia, inspeccionar errores del
log aunque exista resultado 0 y verificar que la carga llegó al estado esperado.
No se modificó tools/vita3k-recomp.ps1.

## Búsqueda en issues públicos

Se consultó GitHub por repo:Vita3K/Vita3K con pthread, Read violation, sceIoRead y
thread crash, guardando respuestas en github-issues.json. Referencias revisadas:

- [#3898: mutex destruido en Limbo](https://github.com/Vita3K/Vita3K/issues/3898):
  aborto de sincronización en Android; no coincide con nuestra copia desde cero.
- [#1024: sceKernel y LwMutex en homebrew](https://github.com/Vita3K/Vita3K/issues/1024):
  reporte antiguo de APIs/mutex; no aparecen esos errores en nuestro punto de fallo.
- [#3891: Read violation 0 en otro juego](https://github.com/Vita3K/Vita3K/issues/3891):
  misma firma genérica, contexto de shaders distinto; no demuestra una causa común.
- [#4028: hard crash vitaGL](https://github.com/Vita3K/Vita3K/issues/4028):
  relacionado con framebuffer; nuestro H2 aún usa render_vita vacío.

Ninguno prueba un fallo equivalente de E/S concurrente o una solución aplicable.
La evidencia específica procede de nuestros registros y de la captura de memoria,
no de equiparar dos mensajes genéricos de excepción.

## Entrega y límites

Archivo creado: docs/VITA3K_LOAD_CRASH.md. No se modificó ningún archivo de
recomp/, el lanzador, AGENTS, el roadmap ni la configuración de otra instancia.
No hay recursos del juego, ejecutables o código comercial en este commit.

Builds normal y trace: **pasaron**. Diagnóstico: **excepción reproducida 6/6**;
validación de carga: **falló**, aunque cinco wrappers devolvieran 0. GDB identificó
fuente nula y su textura. git diff --check: **pasó**.

Quedan sin verificar: el arreglo propuesto, el presupuesto de memoria definitivo,
la carga completa, H3, Vita real y comportamiento posterior al título. Estos VPK
son artefactos locales de diagnóstico; no son una entrega del juego completo.
