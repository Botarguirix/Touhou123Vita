# Propuesta y roadmap: Touhou 12.3 en PS Vita por recompilación estática

Fecha: 20 de octubre de 2026. **Aprobada el 21 de octubre de 2026**; sustituye la estrategia del [roadmap anterior](ROADMAP.md), que queda como historial.

**Estado: F0 completada; F1.1 (descubrimiento de funciones y switch) completada con 99,40 % de cobertura** ([F1_DISCOVERY.md](F1_DISCOVERY.md)). **F1.2 (lifter mínimo + modelo x87 explícito) completada**: el kernel de animación traducido pasa 2 048/2 048 casos, el x87 coincide con la FPU real en 2,7 M comprobaciones y 55/57 funciones x87 reales coinciden con el original ([F1_LIFTER.md](F1_LIFTER.md)). **F1.3 completada**: las 6 406 funciones se traducen, compilan y enlazan en PC, y el código del juego tiene **0 instrucciones sin soporte**; quedan 856 SSE2 del CRT, que no se ejecutan por la política de `cpuid` ([F1_COVERAGE.md](F1_COVERAGE.md)). **F1 cerrada.** **F2.0 completada**: el CRT y `WinMain` traducidos arrancan en PC, crean la ventana del juego, abren y parsean los tres DAT y llegan a `Direct3DCreate9` ([F2_BOOT.md](F2_BOOT.md)). **H1 / F3.0 conseguido**: el mismo código compilado para ARM arranca en Vita3K con una traza idéntica a la de PC ([H1_VITA_BOOT.md](H1_VITA_BOOT.md)). **H2 conseguido**: el código original dibuja la pantalla de título en PC con hilos reales y D3D9 sobre OpenGL ([H2_PC_TITLE.md](H2_PC_TITLE.md)). **H3 conseguido** en una Vita real con vitaGL. **En PC ya hay pelea:** Vs Com, Reimu contra Sanae, con HUD completo, controlada por pulsaciones por script ([H2_PC_TITLE.md](H2_PC_TITLE.md)). Siguiente: medir y acelerar la carga en la Vita (no llega al título en 60 s), y el audio.

F0 (21 oct 2026). Detalles en [PE_INVENTORY.md](PE_INVENTORY.md): la ruta sigue adelante, con dos ajustes en F1 (descubrimiento propio de funciones y switch, y verificación del modo x87 que deja D3D9).

## Hitos visibles y cuánto falta (actualizado el 21 oct 2026)

Hasta ahora todo el avance es invisible: el código original ya se traduce, compila y se valida contra el x86, pero todavía no dibuja nada. Estos son los primeros puntos en los que **se puede ver** algo, en el orden en que llegan.

Las estimaciones van en **bloques de trabajo**, con la escala de hoy: F0, F1.1, F1.2 y F1.3 fueron un bloque cada uno. Son estimaciones, no compromisos. Cada hito tiene criterio de salida, y si un bloque destapa un problema mayor se dice.

| # | Hito visible | Qué hace falta | Bloques desde hoy | Dónde se ve |
|---|---|---|---|---|
| H1 | **El código recompilado del juego corre en ARM.** El arranque del CRT y `WinMain` se ejecutan en Vita3K, con el progreso en una pantalla de texto | **Conseguido el 21 oct 2026** ([H1_VITA_BOOT.md](H1_VITA_BOOT.md)): traza idéntica a la de PC; **confirmado en una Vita real el 23 oct 2026** (2 723 ms hasta D3D) | — | Vita3K y Vita real |
| H2 | **Primera imagen del juego en PC**: la pantalla de título dibujada por el código original | Ventana y bucle de mensajes, subconjunto de D3D9 (dispositivo, texturas, *vertex buffers*, `DrawPrimitive`) sobre OpenGL/SDL2, los 3 efectos D3DX reescritos, hilos reales (el juego carga en un hilo aparte), DirectInput/DirectSound mínimos, excepciones C++ si aparecen | **Conseguido el 23 oct 2026** ([H2_PC_TITLE.md](H2_PC_TITLE.md)): 600 fotogramas del título sin errores | PC |
| H3 | **Primera imagen del juego en Vita3K / Vita** | La capa D3D9 de H2 sobre vitaGL, fuentes (sustituto de `GetGlyphOutlineA`) y presupuesto de memoria de texturas | **Conseguido el 24 oct 2026 en una Vita real** ([H2_PC_TITLE.md](H2_PC_TITLE.md), sección H3): la pantalla de carga «東方Project / Presented by» dibujada vía vitaGL, centrada en 4:3; en 60 s todavía no llega al título | Vita real |
| H4 | **Menús y un combate jugable** con mando | Entrada completa, audio (DirectSound → SceAudio), ritmo de frames y rendimiento mínimo aceptable | **4–8** después de H3 | Vita |

En resumen: lo primero que se verá **en Vita3K es H1**, a unos 2–3 bloques. Es un avance real (el código de Hisoutensoku ejecutándose en ARM), pero es texto, no gráficos. La **primera imagen del juego** llega con H2 en PC y con H3 en Vita.

Riesgos que pueden mover estas cifras:

- **Rendimiento del código traducido en el Cortex-A9.** Se mide en H1 con el arranque; si es muy lento, las optimizaciones de F5 se adelantan.
- **Memoria de la Vita.** Se mide en H1 y H3.
- **Excepciones de C++ (SEH)**, si el juego las usa en su flujo normal.
- **Fallos de Vita3K** con un ejecutable de ese tamaño. Por eso conviene probar también en una Vita real desde H1.

## 1. Diagnóstico del proyecto actual

| Medida | Valor |
|---|---|
| Iteraciones documentadas | ~300 (`docs/ITERATION*.md`, 317 documentos) |
| Runtime nativo (`src/` + `include/`) | ~3 900 líneas de C; `vita_main.c` sola tiene 2 000 |
| Herramientas de análisis | 70 scripts Python, muchas sondas x86 de una sola función |
| Avance que declara el propio proyecto | 27 % |
| Suite C general | En rojo (fixture Suika 530) |

El enfoque actual **reimplementa a mano** el motor: cada acción de cada personaje se redescubre en el PE, se reescribe en C y se contrasta con Unicorn. Es riguroso, pero no escala. Hisoutensoku tiene 20 personajes con cientos de handlers, objetos, cartas, clima, 20+ escenarios, Story, menús, audio y red. Después de 300 iteraciones siguen sin portar las rutas B/C, las skills, los objetos, las cartas, el clima, el audio y casi todos los escenarios. A este ritmo el juego completo no llega.

Vagante2Vita llegó a la misma conclusión en [COMPARACION_RAMAS.md](../../Vagante2Vita/docs/COMPARACION_RAMAS.md): el motor que *imita* el juego (rama B) da una demo pronto pero «no escala al juego completo». Lo que sí escala es **traducir el código original**, sin redescubrir su comportamiento.

**Conclusión: hay que cambiar de estrategia, no tirar el trabajo.** El objetivo deja de ser «reescribir Hisoutensoku» y pasa a ser «ejecutar el código original de Hisoutensoku en ARM».

## 2. Lo que se toma de Vagante2Vita

- **Precedente directo, [repentogxm](https://github.com/0xl0cal/repentogxm).** Traduce por adelantado *todas* las funciones del `.exe` x86 de *The Binding of Isaac: Repentance* a C (`guest_####.c`) y las compila con VitaSDK. Carga la imagen en una dirección fija mediante kubridge y redirige OpenGL a vitaGL. Según el proyecto, la v0.1.1-alpha corre a 60 FPS en menús, a 55–59 FPS en salas normales y a 33–34 FPS en salas densas. Sus decisiones clave:
  - Cada función entra en una tabla de *dispatch*, así que las llamadas indirectas no requieren reescritura.
  - El código que no se puede traducir falla de forma visible (`guest_fault(dirección, mnemónico)`) en vez de quedar silencioso.
  - Las funciones calientes se reemplazan por versiones nativas, con *fallback* al código traducido.
  - El código generado no se publica y el build comprueba el SHA-256 del `.exe` del usuario.
- **Separar dos métricas:** el avance de la reconstrucción (funciones traducidas o reemplazadas) por un lado; el avance del port (qué se ve y se juega en Vita3K y en hardware) por otro.
- **Validar en PC antes que en Vita3K.** Vagante perdió mucho tiempo con fallos de arranque de Vita3K que no tenían que ver con el juego. El mismo C generado debe compilar también para PC y compararse allí con el original.
- **Procedencia y hashes** de cada entrada (`.exe`, DAT, versión de las herramientas), que este proyecto ya practica.

## 3. Rutas evaluadas

| Ruta | Juego completo | Fidelidad | Esfuerzo | Veredicto |
|---|---|---|---|---|
| A. Seguir reimplementando a mano (actual) | No realista | Aproximada salvo lo verificado | Enorme, lineal por cada función | Abandonar como ruta principal |
| B. Decompilación *matching* (como [th06](https://github.com/GensokyoClub/th06)) | Sí, a muy largo plazo | Exacta | Años; exige el MSVC original | No, por ahora |
| C. Decompilación manual no-matching guiada por SokuLib | Sí | Alta | Muy grande: miles de funciones a mano | Como pista secundaria y progresiva |
| **D. Recompilación estática x86 → C + capas de plataforma** | **Sí, todo el código a la vez** | **Del original** | Grande, pero concentrado en el traductor y las capas Win32/D3D9 | **Recomendada** |
| E. Emular x86/Windows en Vita (box86/Wine) | — | — | No existe en Vita y el coste por instrucción sería alto | Descartada |

**Propuesta: D como columna vertebral, con C de forma progresiva encima.** Primero todo el juego corre traducido. Después se reemplazan funciones por C legible y nativo, con nombres de SokuLib, donde aporte rendimiento o claridad. Así la «decompilación» que pides se obtiene completa desde el principio (C generado para todo el ejecutable) y mejora de forma incremental.

### Por qué Hisoutensoku es un buen candidato

- `th123.exe` 1.10a (SHA-256 `f0db9366…a16731e`) pesa **4,8 MB**, unas 2,5 veces menos que el `.exe` de Vagante.
- La superficie de importaciones es pequeña: unas **170 funciones** según `local/SokuLib/src/dlls`, de KERNEL32, USER32, GDI32, WINMM, WS2_32, OLE32, IMM32 e IMAGEHLP. De D3D9 solo importa `Direct3DCreate9`; el resto pasa por las vtables COM. De D3DX9_33 importa 4 funciones: `D3DXCreateEffect`, `D3DXCreateTexture` y dos de vectores.
- Es un juego 2D de 640×480 que corría en PCs de 2008, así que hay margen frente al Cortex-A9 a 444 MHz, aunque hay que medirlo.
- **SokuLib** (MIT, ya está en `local/SokuLib`, unas 25 000 líneas) nombra clases, campos, vtables y direcciones: BattleManager, Player, GameObject, Scenes, Renderer, TextureManager, SoundManager, InputManager, Weather y más. Eso da nombres y tipos al código generado y orienta las capas de plataforma.
- **shady-packer** ya resuelve el formato de los DAT, y el oráculo **Unicorn** del proyecto permite comparar función por función el C generado con el x86 original.

## 4. Objetivo correcto

> **Touhou 12.3 Hisoutensoku 1.10a jugable en PS Vita a partir del `th123.exe` y los DAT del propio usuario, ejecutando el código original recompilado para ARM, con todos los modos offline, audio y guardado, a 60 FPS como objetivo.**

**Fuera del alcance inicial:** netplay (Winsock/UDP, posible en v2), mods de SWRSToys, editor de mazos con ratón (se adapta a botones) y cualquier distribución de código generado o de recursos.

**Reglas legales que se mantienen:** el repositorio contiene solo el traductor, el runtime, las capas y la documentación. El C generado, el `.exe`, los DAT y el VPK con recursos se quedan locales.

## 5. Alcance por versiones

| Versión | Contenido | Criterio de aceptación |
|---|---|---|
| **MVP** | Arranque → título → menús → VS CPU con cualquier personaje y escenario, con audio | Corre en Vita3K y en Vita física y completa un combate sin `guest_fault` |
| **v1** | Arcade, Story (con Namazu), VS 2P local en PSTV, Practice, perfiles y mazos, replays, guardado en `ux0:data/touhou123vita/` | Replays grabados en PC se reproducen idénticos en Vita (determinismo) |
| **v1.x** | Rendimiento: 60 FPS estables con clima y spells, cargas menores de 2 s | Medido en hardware con perfilador |
| **v2** | Netplay compatible con PC (opcional), opciones de escala y filtros | Partida contra un PC 1.10a sin desync |

## 6. Arquitectura propuesta

```
th123.exe (del usuario, hash verificado)
   │
   ├─ análisis: límites de función (Ghidra + heurísticas), jump tables,
   │            vtables, IAT, datos vs. código    → functions.json / bounds.json
   │
   ├─ lifter x86 → C (Capstone; x87 sobre double; SSE si aparece)
   │      → guest_NNNN.c + tabla de dispatch + guest_fault para lo no soportado
   │
   └─ build ─┬─ PC host (x86/x64, SDL2 + OpenGL)    ← depuración y comparación
             └─ Vita (VitaSDK, kubridge, vitaGL)    ← objetivo
                   │
     runtime "guest": memoria del PE en dirección fija, pila, registros,
                      CRT de MSVC (traducido o sustituido)
                   │
     capas de plataforma (tamaño estimado, por medir):
       KERNEL32  → archivos ux0:, hilos SceKernel, tiempo, heap
       USER32/GDI32/IMM32 → ventana falsa, mensajes mínimos, fuentes
       D3D9 COM (subconjunto que usa Soku) → vitaGL / GXM
       D3DX9: texturas + efectos → shaders reescritos a mano
       DirectSound (vía OLE32/COM) + WINMM → SceAudio / OpenAL
       DirectInput / joystick WINMM → SceCtrl
       WS2_32 → stub (v1), SceNet (v2)
```

## 7. Riesgos principales y cómo se acotan

| Riesgo | Mitigación / punto de decisión |
|---|---|
| Precisión x87 (80 bits) contra double en ARM, con posibles desincronizaciones de replays | Se mide pronto con los replays reales y el oráculo Unicorn. Si hay divergencias, se emula la precisión solo en las funciones afectadas. |
| Memoria: Vita tiene 512 MB de RAM + 128 MB de VRAM y `th123a.dat` pesa 1 GB | Soku carga los recursos bajo demanda. En F2 se mide el uso real en PC (heap y texturas). Si no cabe, se implementa streaming o compresión de texturas en la capa D3D9. |
| Rendimiento del código traducido sin optimizar | `-O2`, tabla de dispatch directa, eliminar registros redundantes y luego reemplazos nativos de las funciones calientes (renderer, blits, matemáticas), como hace repentogxm. |
| Funciones o patrones no traducibles (SEH, `thunks`, código en datos) | Fallo visible con `guest_fault`, contador de cobertura y corrección caso por caso. |
| Shaders de `D3DXCreateEffect` | Inventariarlos en F0. Son pocos y se reescriben a mano para vitaGL. |
| Vita3K inestable | Validar primero en PC host y en hardware. Vita3K es una ayuda, no un requisito para avanzar. |
| Esfuerzo concentrado en el lifter | Reutilizar ideas (y código, si se acepta su licencia GPL-2.0+) de repentogxm, o escribir uno propio. Se decide en F1. |

## 8. Roadmap por fases

Cada fase tiene un criterio de salida. Si una fase se atasca, se reevalúa la ruta antes de seguir.

### F0 — Congelar, rescatar e inventariar
- Etiquetar el estado actual (`legacy-reimpl-2.199`) y mover el motor hecho a mano a `legacy/`. Sigue compilando como demo y como fuente de oráculos.
- Inventario exacto del PE: secciones, compilador y versión del CRT de MSVC, si está empaquetado, IAT completa, objetos COM creados (`CoCreateInstance`: DirectSound, DirectInput), efectos D3DX embebidos e hilos.
- Lista de funciones desde el proyecto Ghidra existente más heurísticas, con conteo y tamaño.
- **Salida:** documento `docs/PE_INVENTORY.md` con la decisión de seguir o no seguir con D.
- **Resultado:** completada. Se etiquetó `legacy-reimpl-2.199`, el motor está en `legacy/` y sigue compilando (host y VPK). Herramientas nuevas: `tools/pe_inventory.py` y `tools/export-functions.ps1`. Decisión: seguir. El proyecto Ghidra deja el 47 % de `.text` fuera de funciones (switch sin resolver), así que F1 empieza por el descubrimiento propio de funciones.

### F1 — Lifter y cobertura
- Traductor x86 → C para el conjunto de instrucciones que usa el PE: enteros, x87, SSE si existe y cadenas (`rep movs`).
- Tabla de dispatch, jump tables, vtables y `guest_fault` para lo pendiente.
- Las sondas Unicorn existentes (animación, matcher `NRNR`, transformación de cajas, Remilia 801, Suika 418) se convierten en **pruebas de equivalencia** del C generado.
- **Salida:** al menos el 99 % de las funciones traducidas y compilando en PC, y todas las pruebas de equivalencia en verde.

### F2 — Arranque en PC host
- **F2.0** (completada): CRT y `WinMain` traducidos sobre una capa Win32 mínima y portable (`recomp/host/`: heap y memoria virtual guest, TLS en el TIB, archivos, perfiles `.ini`, código de página 932). Llega a `Direct3DCreate9` después de abrir y parsear los tres DAT ([F2_BOOT.md](F2_BOOT.md)).
- **F2.1:** ventana, mensajes e hilos reales.
- **F2.2:** D3D9 sobre OpenGL/SDL2 y los 3 efectos D3DX (hito **H2**: primera imagen en PC).
- **F2.3:** entrada, audio y combate.
- Se mide en PC el uso de memoria (heap y texturas) y el número de draw calls por frame.
- **Salida:** combate completo en PC con el código traducido, y un replay de PC reproducido idéntico.

### F3 — Primer arranque en Vita
- **F3.0** (hito **H1**, se adelanta y va justo después de F2.0): el mismo C compilado para ARM con VitaSDK, con un mapa de memoria guest de 32 bits dentro de un único bloque de la Vita y la capa de host portable. Lo prueba el autotest de Vita3K y el progreso se ve en una pantalla de texto.
- **F3.1** (hito **H3**): la capa D3D9 pasa a vitaGL y el audio a SceAudio.
- Se valida en Vita3K y en hardware, con FPS, RAM y VRAM medidos.
- **Salida:** MVP en Vita, es decir, título, menús y un combate VS CPU con audio.

### F4 — Juego offline completo
- Todos los modos (Arcade, Story, VS, Practice, replays), perfiles y mazos, guardado, mapeo de controles y 2P local en PSTV.
- Pruebas: barrido de los 20 personajes × escenarios con el autotest de Vita3K reutilizado, y replays de PC como prueba de determinismo.
- **Salida:** v1.

### F5 — Rendimiento
- Perfilado en hardware y reemplazos nativos de funciones calientes con *fallback*; caché de texturas y tiempos de carga.
- **Salida:** 60 FPS estables en los casos pesados (clima y spells de pantalla completa).

### F6 — Pulido y extras
- LiveArea, opciones, distribución reproducible (el usuario aporta el `.exe` y los DAT; un script genera su VPK).
- Pista paralela de decompilación progresiva: reemplazar funciones por C legible con nombres de SokuLib, sin romper la equivalencia.
- Netplay opcional (v2).

## 9. Qué se reutiliza del proyecto actual

| Pieza actual | Uso en la nueva ruta |
|---|---|
| Oráculo Unicorn y sondas x86 | Pruebas de equivalencia del lifter (valor muy alto) |
| Proyecto Ghidra, desensamblados y xrefs en `artifacts/` | Límites de función, jump tables y vtables |
| SokuLib y shady-packer locales | Nombres, tipos y estructuras; validación de los DAT |
| Lector de DAT / CV2 / PAL / PAT en C | Herramienta de inspección y verificación (el juego traducido lee los DAT por su cuenta) |
| Infraestructura Vita3K (`vita3k-test.ps1`, autotest, VitaFS aislado) | Pruebas automáticas del VPK nuevo |
| Empaquetado VPK, LiveArea, Title ID `THSV12301` | Directo |
| Replays analizados (`replay.c`, layout) | Prueba de determinismo PC contra Vita |
| Motor hecho a mano (`fight.c`, `stage.c`, …) | Se congela como demo `legacy/`; no se sigue extendiendo |
| Documentación de iteraciones | Historial; el conocimiento del PE ayuda a depurar el código traducido |

## 10. Próximos pasos concretos

Hechos: F0 (inventario y congelación), F1.1 (descubrimiento), F1.2 (lifter y x87) y F1.3 (programa completo).

1. ~~**F2.0:** llevar el arranque del CRT y `WinMain` traducidos tan lejos como permita una capa Win32 sin gráficos~~ (hecho: llega a `Direct3DCreate9`).
2. ~~**F3.0 / H1:** build ARM del mismo programa con la ventana de memoria de 32 bits, y prueba en Vita3K~~ (hecho). Queda pendiente la prueba en una Vita real, con las instrucciones de [H1_VITA_BOOT.md](H1_VITA_BOOT.md).
3. ~~**F2.1–F2.2 / H2:** ventana, hilos y D3D9 en PC hasta la pantalla de título~~ (hecho).
4. En paralelo, Codex: T3 (censo de métodos COM, que fija el alcance de la capa D3D9), T4 (zlib/libpng/vorbis para Vita) y T5 (fuentes).

## 11. Decisiones tomadas

- Cambio de ruta aprobado el 21 oct 2026; el motor hecho a mano queda congelado en `legacy/`.
- **Lifter propio:** no se copia código de repentogxm, solo ideas. La licencia del proyecto queda libre de elegir.
- El C generado, el `.exe`, los DAT y los recursos no se publican.

## Fuentes

- [repentogxm](https://github.com/0xl0cal/repentogxm): recompilación estática de un `.exe` x86 a C para Vita.
- [M-HT/SR](https://github.com/M-HT/SR): recompilador estático de ejecutables DOS/Windows a llasm/LLVM, con builds ARM en Linux.
- [SokuLib](https://github.com/SokuDev/SokuLib): estructuras y direcciones de Hisoutensoku reconstruidas por la comunidad de mods.
- [Mods de Hisoutensoku (wiki)](https://hisouten.koumakan.jp/wiki/Mods): ecosistema SWRSToys/SokuMods.
- [th06 decomp](https://github.com/GensokyoClub/th06) y [TH08-Platform](https://github.com/dwgx/TH08-Platform): decompilaciones de otros Touhou, como referencia de la ruta B.
- Vagante2Vita: `docs/COMPARACION_RAMAS.md`, `docs/GITHUB_REFERENCE_REVIEW.md` y `docs/FEASIBILITY.md`.
