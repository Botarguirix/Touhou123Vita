# Touhou123Vita alpha 0.1

## English

First source-only alpha of the PS Vita port of Touhou 12.3 Hisoutensoku 1.10a, using static recompilation (x86 → C → ARM). Build locally with your own lawful game copy. **No VPK, generated game code, game resources, patch files or third-party binaries are attached.** GitHub's automatic source archives contain the repository only.

Included in the source snapshot: vitaGL rendering on hardware, title/menu navigation and playable Vs Com fights; adaptive frame skip; DirectSound mixing with native Vorbis music decoding; optional phase-1 English resource overlay for the user's th123e.dat (426 resources). Historical hardware measurements include about 39 s to title and fight intervals at 50–59 FPS; they are not guarantees for this snapshot. Story/Arcade completion and complete English presentation remain unverified.

Known issues: reported black-screen freezing after 5–6 matches and latest audio degradation/slowdown (not independently reproduced here); documented asynchronous texture-compression failures; missing card actions 807/820 use a lower-action fallback. English fonts, about 80 EXE strings and layout changes are pending. Netplay, analog/touch controls, local two-player mode and Vita3K are unsupported.

Requires the user's 1.10a EXE (SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`), th123a/b/c.dat, HENkaku/Ensō, VitaShell and the user's libshacccg.suprx. Maximum supported clocks are recommended. See [README](../README.md) for Windows build/install commands and [ROADMAP](ROADMAP.md) for evidence and priorities. Hold START+SELECT for 2 seconds to exit and write diagnostics; `guest-vorbis.txt` selects the translated decoder for comparison.

Fan project, not affiliated with Team Shanghai Alice or Twilight Frontier. No game content is distributed.

## Español

Primera alpha de fuentes del port a PS Vita de Touhou 12.3 Hisoutensoku 1.10a por recompilación estática (x86 → C → ARM). Compila localmente con tu copia legal. **Sin VPK, C generado, recursos, archivos del parche ni bibliotecas binarias adjuntas.** Los archivos de fuentes automáticos de GitHub solo contienen el repositorio.

Incluye render vitaGL en consola, título/menús y peleas Vs Com; frame skip adaptativo; mezclador DirectSound y Vorbis nativo; superposición inglesa fase 1 para el th123e.dat del usuario (426 recursos). Se documentaron unos 39 s hasta el título y tramos de 50–59 FPS en hardware, no garantizados para este snapshot. Completar Story/Arcade y la presentación inglesa completa quedan sin verificar.

Problemas: congelación negra reportada tras 5–6 partidas y audio degradado/lentitud en la última prueba (sin reproducción independiente aquí); carrera de compresión asíncrona documentada; acciones 807/820 con respaldo inferior. Faltan fuentes inglesas, unas 80 cadenas del EXE y layout. Netplay, analógico/táctil, dos jugadores locales y Vita3K no están soportados.

Necesitas tu EXE 1.10a con el SHA indicado, th123a/b/c.dat, HENkaku/Ensō, VitaShell y tu libshacccg.suprx. Se recomienda el máximo overclock admitido. [Compilación/instalación](../README.md) y [roadmap](ROADMAP.md). Mantén START+SELECT 2 s para salir y guardar diagnóstico; `guest-vorbis.txt` activa el decodificador traducido para comparar.

Proyecto de fans no afiliado a Team Shanghai Alice ni Twilight Frontier; no distribuye contenido del juego.

## Publication gate / Publicación pendiente

These notes are a proposal. The owner must approve the target commit in chat before any tag or release is created. Do not tag a moving main branch or publish binaries.

Estas notas son una propuesta. El propietario debe aprobar el commit objetivo en el chat antes de crear tag o release. No etiquetar main sin fijar el commit ni adjuntar binarios.

After approval only / Solo tras aprobación (replace APPROVED_COMMIT with the approved full commit SHA):

```powershell
gh release create v0.1.0-alpha --repo Botarguirix/Touhou123Vita --target APPROVED_COMMIT --prerelease --title "Touhou123Vita alpha 0.1" --notes-file docs/RELEASE_NOTES_0.1.md
```

No asset arguments. This command has **not** been executed. Sin argumentos de adjuntos; **no ejecutado**.
