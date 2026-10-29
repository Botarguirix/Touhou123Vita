# Touhou123Vita alpha 0.1 — roadmap / hoja de ruta

## English

**Source snapshot:** `e9ad62d`, 28 October 2026. Experimental, source-only alpha. This document separates historical measurements from unverified behaviour; it does not certify the latest binary. No game content, generated C, VPK or third-party binaries accompany the release.

### What it does

| Area | Evidence and practical limit |
|---|---|
| Boot on a real Vita, title and menus | [H2_PC_TITLE.md](H2_PC_TITLE.md), hardware load measurements: 38.8–39.1 s to title; later reports include a 29 s run. Different builds, not a timing guarantee. |
| Playable fights / Vs Com | H2 hardware fight reports and PC fight walkthrough; title → menu → Vs Com → fight was played using Vita buttons. |
| Story and Arcade | Listed main-menu modes in H2. Complete campaigns, all encounters and their stability on current Vita build: **unverified**. |
| Adaptive frame skip | Commit `3fbe061`: logic continues while rendering may skip frames. H2 records 50–59 FPS fight intervals and 55,000 frames without exits in an earlier run; this does not establish long-session stability. |
| Music / audio | Commit `13f537b` integrates the DirectSound mixer and Vita audio output; `ce1a032` adds native vorbisfile, `5e9f9c9` adds translated-decoder fallback for diagnosis. Audio quality on the latest hardware build: **unverified**. |
| English translation, phase 1 | Commit `e9ad62d`: optional th123e.dat → local cache, resource priority through 0x41C080. Its code limits replacement to 426 resources: images, tables and scripts/data. Visual correctness of every resource on hardware: **unverified**. |

### What it does not do / known issues

- Black-screen freeze after 5–6 matches: investigation priority from the release brief; **unverified**, no reproducer for that exact interval in the checked docs/history. H2 does record asynchronous compression failures (2/6 PC runs) and prior GPU/memory failures. Do not assume a shared cause.
- Degraded audio and slowdown in the latest reported hardware test: **unverified** here; no matching current trace in the checked documentation. Native Vorbis and `guest-vorbis.txt` allow A/B diagnosis.
- Native English patch fonts, about 80 strings stored in the original EXE, and patch-specific layout corrections are not covered by phase 1. T15 analysis on `codex/T15` identifies these remaining layers; Noto glyphs are not metric-identical substitutes.
- Netplay/network play, mapped analog stick, touch, and supported local two-player play are outside this alpha's supported scope. Existing socket/API stubs are not proof of working netplay.
- Missing action IDs **807/820**: H2 documents fallback; `game_checks.c` chooses the nearest lower available action when lookup fails. Full card-action fidelity is not verified.
- **Vita3K is unsupported.** Historical H1/emulator boot evidence is not a support promise for the current vitaGL game.
- No 60 FPS guarantee, no exhaustive character/stage/campaign/replay certification, and no redistributed VPK.

### Next steps, in priority order

1. Reproduce and diagnose long-session black screens; correlate texture pool/GPU use, thread failures and compression lifetime.
2. Compare native and translated audio using `guest-vorbis.txt`; investigate slowdown and sound degradation before claiming stable audio.
3. Add contextual English fonts/metrics, then the EXE string overlay and scene layout fixes identified by T15.
4. Profile load, fight logic and frame skip on hardware; restore missing card actions and broaden character/stage/campaign coverage.

The old reimplementation roadmap is preserved as [ROADMAP_REIMPLEMENTATION.md](ROADMAP_REIMPLEMENTATION.md). [ROADMAP_RECOMP.md](ROADMAP_RECOMP.md) remains the technical architecture/history and includes older milestone text that should be read chronologically.

## Español

**Base:** `e9ad62d`, 28 de octubre de 2026. Alpha experimental publicada solo como fuentes. Las mediciones históricas no certifican el binario más reciente.

### Qué hace

| Área | Evidencia y límite |
|---|---|
| Arranque, título y menús en Vita real | H2 documenta 38,8–39,1 s hasta el título y una ejecución posterior de 29 s. Son builds distintos. |
| Peleas jugables / Vs Com | H2 documenta el recorrido título → menú → Vs Com → pelea con botones de Vita y una pelea en PC. |
| Story y Arcade | Están en los menús documentados; completar campañas y todos sus encuentros en la Vita actual queda **sin verificar**. |
| Frame skip adaptativo | `3fbe061` mantiene la lógica mientras puede omitir dibujo. H2 registra tramos de 50–59 FPS y una prueba anterior de 55.000 fotogramas sin cierres; no garantiza estabilidad indefinida. |
| Música/audio | `13f537b`: mezclador y salida Vita. `ce1a032`: vorbisfile nativo. `5e9f9c9`: diagnóstico con decodificador traducido. Calidad actual en hardware **sin verificar**. |
| Inglés, fase 1 | `e9ad62d`: caché local y superposición de 426 recursos del th123e.dat opcional. Paridad visual completa **sin verificar**. |

### Qué no hace / problemas conocidos

- Congelación negra tras 5–6 partidas: prioridad de la solicitud de publicación, **sin verificar**; no se encontró una reproducción de ese intervalo concreto en docs/historial. La carrera de compresión asíncrona documentada en H2 es un hallazgo distinto, sin causa compartida demostrada.
- Audio degradado y lentitud de la última prueba reportada: **sin verificar** con una traza actual. Comparar ambas rutas de Vorbis.
- Faltan las fuentes contextuales del parche inglés, unas 80 cadenas del EXE y sus ajustes de layout. El análisis T15 no equivale a integración ni validación visual.
- No se soportan netplay, stick analógico, táctil ni dos jugadores locales.
- Acciones de carta **807/820** ausentes: se usa la acción disponible inmediatamente inferior; no hay paridad completa garantizada.
- **Vita3K no está soportado**. No hay garantía de 60 FPS ni validación exhaustiva de personajes, escenarios, campañas y replays.
- No se publica VPK, C generado, recursos del juego ni bibliotecas binarias ajenas.

### Próximos pasos

1. Estabilidad: reproducir congelaciones largas y correlacionar memoria, GPU, hilos y vida de compresión.
2. Diagnosticar sonido y lentitud comparando Vorbis nativo y traducido.
3. Fuentes inglesas y métricas por contexto; después cadenas del EXE y ajustes de diseño.
4. Rendimiento medido en consola, acciones faltantes y mayor cobertura de modos/personajes/escenarios.

Evidencia: [H2_PC_TITLE.md](H2_PC_TITLE.md), commits indicados y análisis T15 en su rama. El [roadmap anterior](ROADMAP_REIMPLEMENTATION.md) se conserva como historial; [ROADMAP_RECOMP.md](ROADMAP_RECOMP.md) describe la arquitectura técnica.
