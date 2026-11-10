# Roadmap: Touhou 12.3 Hisoutensoku en PS Vita por recompilación estática

Reescrito el 4 de noviembre de 2026. Sustituye la versión del 21 de octubre. La estrategia no cambia (recompilación estática x86 → C → ARM, con el código original del juego); lo que cambia es el plan: qué está hecho, qué falta y cómo se prueba.

## 1. Dónde estamos hoy

Hechos medidos (fuentes: historial de `origin/main` hasta `1ae065d`, y el trace de la última sesión en Vita del 4 nov 2026):

| Área | Estado | Evidencia |
|---|---|---|
| Lifter x86 → C | **Hecho.** 6 406 funciones, 0 instrucciones sin soporte en el código del juego | F1_COVERAGE.md |
| Capas Win32 / D3D9 / DirectSound / DirectInput | **Hecho** (162 de 171 imports implementados) | trace: `imports: 171, implemented: 162` |
| Render en Vita (vitaGL) | **Hecho.** Presupuesto de GPU con LRU, texturas deflate en memoria, 1024×1024, fondos a media resolución | commits 24–28 oct |
| Audio | **Hecho.** DirectSound → mezclador PCM → `sceAudioOut`, vorbis nativo | commit 26 oct |
| Combate en Vita real | **Funciona**, con FPS por debajo de 60 | ver abajo |
| Traducción inglesa (`th123e.dat`) | **Hecho** como caché (426 recursos) | commit e9ad62d |
| Roster 10.5 (`th105a/b.dat`) | Soportado por la ruta de `configex123.ini`; **sin verificar en Vita** | README |
| Sockets (WS2_32) | **Stub**: todo falla con `WSAENETDOWN` | commit 862efaa |

**Rendimiento (trace del 4 nov 2026, 315 s, 17 520 frames):**

- Menús y arranque: ~17,2 ms por frame (≈58 FPS), con casi todos los frames por encima de 16,7 ms.
- Pelea: 17,8–19,6 ms por frame (≈51–56 FPS). La GPU no es el cuello de botella (draws ≈1–3 ms, swap ≈0,15 ms).
- El coste extra en pelea son las subidas de textura: hasta 225 por ventana de ~10 s, 1 376 evicciones acumuladas, y hasta 591 ms de "small unpack/convert" por ventana. Cada textura expulsada se guarda deflate y se descomprime al volver a subirla.
- Picos de frame de hasta 535 ms al cargar recursos.

**Trabajo perdido.** Las mejoras de FPS posteriores a `1ae065d` (temporizadores por fase, precarga de texturas, optimizaciones de unpack y de hacer espacio) estaban solo en el disco que se perdió y **no se subieron a GitHub**. Se reconstruyen en la fase P1. Comparando las cadenas del último `eboot.bin` anterior a la pérdida (VPK del 4 nov 2026) con el reconstruido, la versión perdida tenía, además: **teclado en pantalla y portapapeles** (nombre del perfil: `# keyboard: …`, `GetClipboardData`, `GlobalLock/GlobalUnlock`, `GetStringTypeExA`, 4 imports más: 162 contra 158), **precarga de texturas** (`T123_NO_PRELOAD`), **volcado de subidas** (`T123_UPLOADLOG`), la línea `# timing:` con desglose (`making room [free query, scan, delete]`, `batch flush`, `small unpack/convert`) y el aviso `texture pool full … dropping kept copies`. Esto sale de las cadenas del binario, no del código fuente. Ya hay una primera reconstrucción local (conversión de formatos sin `switch` por píxel y temporizadores de subida, en `recomp/host/render_gl.c`), sin compilar en Vita ni probar.

## 2. Qué trae Hisoutensoku y qué falta en Vita

Fuentes del contenido: [Wikipedia](https://en.wikipedia.org/wiki/Touhou_Hisoutensoku), [wiki Hisouten](https://hisouten.koumakan.jp/wiki/Touhou_Hisoutensoku) y el propio `th123.exe` (inventario en [PE_INVENTORY.md](PE_INVENTORY.md)). Como se ejecuta el código original, todo el contenido existe por construcción; lo que falta es **verificarlo y adaptarlo** (entrada, red, memoria, guardado). "Verificado" significa probado en una Vita real.

| Contenido del juego | Qué necesita la Vita | Estado |
|---|---|---|
| **20 personajes** (9 propios, incluido Namazu, + roster de 10.5) | `th105a/b.dat` en la tarjeta; memoria de texturas por personaje | Combate Reimu vs. otros probado; **barrido de los 20 pendiente** |
| **Escenarios** (muchos con fondos 640×640+) | Fondos a media resolución ya hecho | Pendiente barrido |
| **Clima** (el de 10.5 más tipos nuevos) y **efectos D3DX** | Los 3 efectos reescritos; vértices XYZW de efectos corregidos el 28 oct | Pendiente verificar Utsuho y clima |
| **Mazo de 20 cartas / Spell Cards** | Editor de mazos (ratón en PC) | **Pendiente: mapear a botones/táctil** |
| **Story** (con diálogos y finales) | Texto japonés/inglés (FreeType + Noto); guardado | **Final alcanzado con el primer personaje**; faltan los demás |
| **Arcade** | Igual que Story | **Crash total a media partida** (antes de las mejoras de rendimiento); hay que reproducirlo con el build actual |
| **VS CPU** | — | **Funciona** |
| **VS Player (2P local)** | Dos mandos. Una Vita tiene uno solo | **Inviable en una Vita sola → ADHOC (sección 4)** |
| **Practice** | — | **Verificado completo** |
| **Replay** (grabar y ver) | `FindFirstFile` (hecho), x87 determinista | **Verificado**; falta confirmar que sigue grabando replays nuevos y cómo acceder a más de los visibles; falta prueba de determinismo con replays de PC |
| **Network** (cliente/servidor/espectador por UDP) | WS2_32 sobre SceNet | **Pendiente (sección 4)** |
| **Perfiles, mazos, score, config** | Guardado en `ux0:data/touhou123vita/` | Rutas mapeadas; **escritura entre sesiones sin verificar** |
| **Music Room, Result** | — | **Verificados completos** |
| **Config** | — | **Verificado**; no se puede cambiar de ventana a pantalla completa (aceptado: la Vita siempre usa pantalla completa) |
| **Audio** (BGM ogg, SFX) | Mezclador y vorbis nativo | Hecho; falta medir sincronía |
| **Mods SWRSToys / SokuMods** | — | **Fuera de alcance** |
| **Control**: 6 acciones por jugador | Mapa de botones de la Vita (incluye táctil trasero si hace falta) | Perfil predeterminado en README; falta revisar combos y Dash |

## 3. Fases

### Hecho

- **F0** inventario y congelación del motor hecho a mano (`legacy/`).
- **F1** lifter x86 → C, x87, 99,4 % de cobertura de funciones, equivalencia con el oráculo Unicorn.
- **F2** arranque en PC, D3D9 sobre OpenGL, primera pelea en PC.
- **F3 / H1 / H2 / H3** arranque en ARM, título en PC, imagen en Vita real con vitaGL.
- **Audio** (T12), **fuentes** (FreeType), **traducción inglesa**, **hilos y prioridades**, **VPK alpha v0.1.0 y v0.1.1**.

### P1 — Llegar a 60 FPS estables (hito actual)

Objetivo: **60 FPS sostenidos en pelea**, medidos en Vita real con el trace. **El push a GitHub se hace al llegar a este hito**, no antes.

1. **Medir primero.** Compilar con los temporizadores de subida (ya añadidos), correr una pelea de 5 min y pasar el trace. Decide dónde está el costo real: inflate, conversión, `glTexSubImage2D` o hacer espacio.
2. **Reducir evicciones** (la causa más probable): subir el presupuesto de 44 MiB si la memoria libre lo permite, evitar expulsar texturas de la pelea en curso, precargar las del personaje y escenario al iniciar la pelea (no durante), y agrupar hojas pequeñas.
3. **Eliminar el trabajo en el hilo principal:** inflate y conversión en los núcleos 1–2, con la textura lista antes de que haga falta.
4. **Frame pacing:** revisar que ~270 de 580 frames pasan de 16,7 ms incluso en menús (parece un tope del pacing o del vsync, no de carga).
5. **Spin del guest:** el trace muestra `WaitForSingleObject`, `PeekMessageA` y `EnterCriticalSection` en bucle; ceder CPU o esperar con tiempo.
6. **Carga:** título a ~39 s; objetivo menor de 15 s (precarga en segundo plano, lectura de DAT por bloques).

**Salida:** trace de 10 min en pelea con ≥ 95 % de frames dentro de 16,7 ms, sin crashes de GPU ni de memoria.

### P2 — Cobertura de modos (v1 offline)

Matriz de pruebas por modo, personaje y escenario, ejecutada en Vita3K y repartida entre las 5 Vitas.

- Barrido de los 20 personajes y todos los escenarios en VS CPU (sin `guest_fault`, sin sprites perdidos, sin crash).
- Story, Arcade, Practice, Music Room, Result, Config: arrancan, avanzan, guardan.
- **Mazos:** decidir mapeo táctil/botones.
- **Guardado:** perfiles, score, config y replays se escriben y se releen tras reiniciar.
- **Replays:** reproducir replays grabados en PC y comparar el resultado (prueba de determinismo x87).
- **Entrada:** revisar los 6 botones, repeticiones de los menús y salida con START+SELECT.

**Salida:** versión v1 (todo el juego offline, un jugador por Vita).

### P3 — Multijugador: ADHOC (ver sección 4)

### P4 — Robustez y pulido

- Sesiones largas (1 h) sin fuga de memoria, de hilos ni de pilas (ya se corrigió una fuga de pilas de 1 MiB por pelea).
- Opciones de pantalla (4:3 centrado, 16:9 estirado), filtro, LiveArea.
- Script de preparación que el usuario ejecuta con su `th123.exe` y sus DAT (el repositorio nunca incluye recursos comerciales).
- Documentación de instalación (ya hay README bilingüe) y verificación del hash del `.exe`.

### P5 — Decompilación progresiva (paralela)

Reemplazar funciones calientes por C legible con nombres de SokuLib, con *fallback* al código traducido y pruebas de equivalencia. Solo donde aporte rendimiento.

## 4. Multijugador con ADHOC (dos Vitas)

**Idea.** Hisoutensoku hace netplay por UDP con `sendto`/`recvfrom` de WS2_32. En vez de reescribir el modo de red, se **implementa WS2_32 sobre `sceNetAdhoc`**: el juego sigue creyendo que habla UDP, y cada datagrama viaja por PDP de ad-hoc entre las dos Vitas. Así el modo **Network** del menú (y por extensión VS Player) funcionaría sin tocar la lógica del juego.

Piezas (APIs de [vitasdk](https://docs.vitasdk.org/adhoc__matching_8h.html): `sceNetAdhocctl*`, `sceNetAdhocMatching*`, `sceNetAdhoc*`):

1. **Descubrimiento y emparejamiento:** pantalla propia previa al juego (host o buscar) con `sceNetAdhocMatching` (modo parent/child), que entrega la dirección MAC del compañero.
2. **Mapeo IP ↔ MAC:** una tabla en el shim traduce la "IP" que el juego cree usar (p. ej. 10.0.0.1 y 10.0.0.2) a la MAC real.
3. **Datagramas:** `socket`, `bind`, `sendto`, `recvfrom`, `select`, `closesocket` sobre PDP (`sceNetAdhocPdpCreate/Send/Recv`), con el mismo puerto que usa el juego.
4. **Integración con el menú:** autocompletar la dirección del servidor para que "Network → Client/Server" conecte sin escribir IP.
5. **Latencia:** el juego usa retardo de entrada, no rollback. Hay que medir el RTT del ad-hoc en pelea y el retardo que impone al juego.

**Riesgos:**

- La semántica de PDP no es idéntica a UDP (tamaño de paquete, buffers); se prueba con capturas del tráfico del juego en PC.
- El determinismo de x87 entre dos Vitas es el mismo código, así que no debería haber desincronización entre ellas; contra PC sí podría (v2).
- Vita3K probablemente no soporta ad-hoc de forma útil; **esta fase se prueba solo en hardware**.

**Pruebas con tus 5 Vitas.** Con 5 consolas se pueden probar varios pares (A–B, C–D) y una tercera Vita como espectador, además de probar la coexistencia de varias sesiones ad-hoc en la misma habitación.

**Alternativas, por si ADHOC falla:**

- **Infraestructura (Wi-Fi):** SceNet con sockets BSD y la misma capa WS2_32. Mantiene el shim, permite Vita↔PC y juego remoto, pero requiere router y manejo de IP.
- **Segundo mando en una sola Vita (PSTV, DS4):** para 2P local en la misma pantalla, sin red.
- **Vita↔PC:** solo vía infraestructura y con riesgo de desync por x87.

**Salida:** dos Vitas juegan una pelea completa por ad-hoc y la repiten dos veces sin desincronizarse.

## 5. Cómo se prueba

| Herramienta | Para qué | Notas |
|---|---|---|
| **PC host** (gcc, SDL2) | Depurar con el mismo C que la Vita; capturas por script | Requiere el C generado (`discover.py` + `lift_all.py`, ya ejecutados) |
| **Vita3K** | Arranque, regresiones, barridos de modos | Instalado en varias carpetas; versión por elegir (la 4170 funcionó para el prototipo viejo, la 4103 no) |
| **5 PS Vita liberadas** | Rendimiento real, memoria, ad-hoc, sesiones largas | Reparto sugerido: 1 para rendimiento, 2 para ad-hoc, 1 de reserva, 1 para barridos de modos |
| **Trace** (`recomp-trace.log`) | Medición continua | Incluye frames, temporizadores, memoria, evicciones |
| **Pruebas Python** (`tests/`) | Lifter, formatos, mezclador, etc. | Se ejecutan con `local/python-deps` |

Entorno actual de build (4 nov 2026): MSYS2 con gcc 15, VitaSDK 2026.08, Python 3.12, `libshacccg.suprx` en la Vita. El `.exe` verificado tiene SHA-256 `f0db9366…a16731e`.

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Memoria: 44 MiB de presupuesto GPU y ~22 MiB de CDRAM libres tras vitaGL | Medir por fase; compresión y streaming |
| Crashes de GPU por evicciones masivas (pasó a las 5 300) | Reducir evicciones; mantener el reintento tras `glTexImage2D` fallido |
| Trabajo no subido a GitHub | Commit local frecuente; el push solo en el hito P1 |
| Netplay: PDP distinto de UDP | Capturas de tráfico y pruebas con 2 Vitas antes de integrar |
| x87 entre PC y Vita (replays/netplay) | Medir con replays; emular solo donde difiera |
| Vita3K inestable | Validar primero en PC y en hardware |
| Legal | El repositorio solo contiene código, nunca el `.exe`, los DAT, el C generado ni recursos; el README insiste en la copia legal |

## 7. Próximos pasos concretos

1. Terminar el build de Vita con las modificaciones de `render_gl.c` (en curso) y probar en una Vita real; devolver el trace nuevo.
2. Con ese trace, escoger entre evicciones, precarga o conversión para la siguiente mejora (P1.2–P1.3).
3. Preparar el barrido de los 20 personajes (P2) y repartirlo entre las Vitas.
4. Diseñar el shim WS2_32 → `sceNetAdhoc` (P3), empezando por una prueba mínima de emparejamiento entre dos Vitas.
5. Al cumplir 60 FPS: pulir, commit y **push a GitHub**.

## Fuentes

- [Touhou Hisoutensoku (Wikipedia)](https://en.wikipedia.org/wiki/Touhou_Hisoutensoku) y [wiki Hisouten](https://hisouten.koumakan.jp/wiki/Touhou_Hisoutensoku): contenido y modos del juego.
- [vitasdk: sceNetAdhocMatching](https://docs.vitasdk.org/adhoc__matching_8h.html) y [sceNetAdhocctl](https://docs.vitasdk.org/pspnet__adhocctl_8h.html): API de ad-hoc.
- [SokuLib](https://github.com/SokuDev/SokuLib): estructuras y direcciones del juego.
- [repentogxm](https://github.com/0xl0cal/repentogxm) y [M-HT/SR](https://github.com/M-HT/SR): recompilación estática x86 de otros proyectos.
