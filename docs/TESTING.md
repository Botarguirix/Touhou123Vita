# Pruebas

## Host

`cmake`, build y `ctest` prueban movimiento, límites, salto/aterrizaje, golpes, ataque sostenido sin repetir, proyectiles, daño, reset y determinismo en 3600 frames; también validan rechazo de PE truncados y lectura de PE32. La IA se desactiva durante contratos aislados de movimiento.

## Vita3K automático

Generar variante de prueba:

```bash
export VITASDK=/ruta/vitasdk
export PATH="$VITASDK/bin:$PATH"
cmake -S . -B build-vita-auto -DT123_VITA=ON -DT123_AUTOTEST=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build-vita-auto -j2
```

En Windows, la instalación compartida está en `G:\Vita3k`. La variable de usuario `VITA3K_HOME` apunta a esa carpeta; los scripts de este proyecto la usan por defecto y aceptan `-Vita3K`, `-Config` y `-VitaFS` para reemplazar las rutas. El runner toma esa instalación como fuente y mantiene una copia local ignorada por Git en `local/vita3k-isolated`, en modo portátil. La carpeta `portable` contiene su propia configuración, logs y ruta de sistema; `portable/fs` es un junction al VitaFS de pruebas del proyecto en `artifacts/vitafs`. Así, cada proyecto conserva un entorno de prueba propio y puede compartir la instalación fuente leyendo `$env:VITA3K_HOME`.

Usar el VitaFS de pruebas de este proyecto, con copia del firmware ya instalado:

```powershell
./tools/vita3k-test.ps1 -Vpk './build-vita-auto/Touhou123Vita.vpk'
```

El guest pasa por menú y galería PAT, verifica los contratos BG02/BG12 y visita BG36 con sus transforms locales, recorre los cinco grupos auxiliares y en BG36 muestra la rejilla 6x5 más las dos nubes avanzando con el contrato de sus callbacks; después vuelve a BG34 para las capas, bitmaps, objetos y mapa provisional, y regresa al menú. El gate schema40 captura BG02/capa 1, BG12/capa 2 y BG36/capa 2; comprueba los 48 recursos y offsets locales de BG02, contador/fases de BG12, scroll BG36 con offsets esperados, máscara `stage_constructor_asset_mask=31`, 30+30 rejillas BG34, 4 bitmaps y 30 sprites `objectFa`. La vista de nubes representa transforms locales previos a cámara, no paridad final de composición. El catálogo enumera los 25 IDs del dispatcher x86; BG35 no tiene recursos en los DAT 10.5/12.3 inventariados. Luego verifica roster, práctica y combate durante 600 frames, incluyendo salto, matcher de dash `NRNR`/`NLNL`, impactos B/C y pérdida de vida. El gate no mide paridad temporal con PC ni todos los matchups. El runner archiva evidencia previa y registra hash, fecha UTC y resultado frescos. Ver [ITERATION140.md](ITERATION140.md), [ITERATION141.md](ITERATION141.md) e [ITERATION142.md](ITERATION142.md).

Desde la Iteración 1.83 el reporte schema31 exige una máscara completa `roster_a_attack_mask=0xFFFFF`: cada PAT debe tener una entrada terrestre entre 300/302/303/304/330 que, usando colocación controlada por hitboxes y hurtboxes PAT, aplique el daño de su pose. Desde Iteración 1.85 también exige `roster_a_natural_attack_mask=0xFFFFF`: cada personaje se acerca desde spawn normal con `IN_RIGHT` a Cirno inmóvil y debe conectar A sin reubicar cajas ni luchadores; el runner sigue exigiendo `a_hits>0` en el combate principal y guarda `fight-natural-a.bmp`. Desde Iteración 1.86 los campos `roster_b_natural_attack_mask` y `roster_c_natural_attack_mask` recogen impactos B/C por personaje; son diagnósticos y el runner solo valida su presencia/rango, no cobertura completa. Desde Iteración 2.133, la sonda prueba tres posiciones iniciales del rival (340/380/420), registra origen del hit, separación, rutas que alcanzan acción y variante PAT elegida; el TSV incluye aparte 623C de Suika por nivel. La Iteración 2.134 exige Udonge 409:1, cuadro12/400 de daño. El selector provisional basado en daño/caja no demuestra paridad de variante contra el PE; tampoco el sondeo con rival inmóvil prueba defensa, movimiento o todos los matchups. Ver [ITERATION234.md](ITERATION234.md), [ITERATION233.md](ITERATION233.md), [ITERATION86.md](ITERATION86.md), [ITERATION85.md](ITERATION85.md), [ITERATION84.md](ITERATION84.md) y [ITERATION83.md](ITERATION83.md).

Para inventariar poses con daño y flags de ataque usa `python tools/summarize_pat_attack_flags.py artifacts/pat-detail.tsv docs/PAT_ATTACK_FLAGS.md`. La prueba sintética del formato se ejecuta con `python -m unittest discover -s tests -p test_pat_attack_flags.py -v`. El reporte agrupa por personaje/acción/índice/flags y presencia de cajas; no interpreta bits ni valida contactos en runtime. Ver [ITERATION87.md](ITERATION87.md).

Para exportar una ventana de desensamblado del ejecutable fijado, usa `python tools/disassemble_pe_windows.py --window 00465e10:240 --output artifacts/ghidra/selected-window.tsv`. Repite `--window VA:LENGTH` para incluir más direcciones. El script rechaza cualquier PE cuyo SHA-256 no coincida con la referencia documentada. Ver [ITERATION88.md](ITERATION88.md).

Para ejecutar el sincronizador x86 sobre Remilia 412/seq.0/pose5 usa `python tools/x86_remilia_412_box_sync_probe.py`. Toma el PAT efectivo del DAT local y genera `artifacts/kernel/remilia-412-box-sync.json`; las transformaciones geométricas se sustituyen por copias, así que verifica conteos/layout y no un impacto en combate. Ver [ITERATION94.md](ITERATION94.md).

Para ejecutar la función x86 original `0x42a410` sobre cada pareja del replay aportado, usa `python tools/x86_replay_input_probe.py <replay.rep> --exe <th123-2009.exe> --output artifacts/x86-replay-input-oracle.json`. El probe verifica ambos masks por pareja, los flags de slot 0 y el avance bajo `this+0xf0=3`; el slot 1 ignora los seis flags altos. No modela cadence por frame. Solo acepta el hash del PE original documentado. Ver [ITERATION168.md](ITERATION168.md) e [ITERATION170.md](ITERATION170.md).

Para automatización reproducible se recomienda una versión de Vita3K con `--frontend sdl` y añadir `-Frontend sdl` al runner. No usar `--console` para ejecutar por Title ID: es un modo de instalación. El modo portátil se activa con una carpeta `portable` al lado del ejecutable; el FAQ oficial describe esta disposición. La copia local conserva el nombre `Vita3K.exe` y no modifica la instalación compartida.

`tools/run-all.ps1` encadena pruebas host, compilación Vita, VPK automático y validación Vita3K en una sola ejecución. Requiere font/assets y VitaFS preparados. `tools/play.ps1` instala la variante interactiva en el VitaFS local, retira conservando el indicador de autoprueba y abre una ventana para jugar.

Para crear un VPK interactivo desde una ruta montada con espacios en WSL, `tools/build-vita-temp.sh [ruta-vpk]` copia temporalmente solo fuentes/headers/assets a `/tmp`, compila con `$VITASDK` y copia el paquete resultante al destino.

También exige las tres capturas del framebuffer guest, revisa errores críticos del runtime y el código de salida, y guarda evidencia bajo `artifacts/`. Los contratos host incluyen guardia y KO. Un reporte de pelea seguido de un crash no se considera aprobado.

La variante automática sale después del reporte; la interactiva queda disponible para jugar. Solo el runner puede cerrar su propio proceso hijo en caso de timeout. No interrumpe procesos de otros proyectos.

## Verificación manual y futura

- Menú -> práctica -> arena mediante controles reales.
- Caminar, saltar, golpe, proyectil, guardia, reset, toggle CPU, volver al menú.
- Iteración de combate: abajo agacha; Square/Z hace A según dirección (5A, 6A, 2A, 3A, j5A/j6A/j2A); repetir A tras confirmar un golpe intenta 5AA→5AAA→5AAAA cuando el PAT contiene esos bloques.
- Registrar capturas y comprobar gráficos/legibilidad.
- No aceptar animación automática como prueba de entradas de teclado.
- Después de recuperar el motor original: comparar hitboxes, tiempos, daño, cartas/clima y replays contra PC.
- Repetir en Vita física antes de cerrar compatibilidad y rendimiento.

GitHub Actions ejecuta pruebas host en pushes y PRs. Vita3K se ejecuta localmente con firmware y datos locales; no se descargan juegos ni firmware en CI público.

## Iteración 0.2

Preparar `ux0/data/touhou123vita/th123a.dat`, `th123b.dat` y `th123c.dat` en el VitaFS aislado. El VPK ya no lleva imágenes del juego. El reporte usa schema 3 y exige los tres DAT, más de dos texturas decodificadas y pérdida de vida respecto de `max_hp`.

Los oráculos opcionales se generan con `tools/x86_animation_oracle.py` y las dependencias de `tools/requirements-oracle.txt`; los CSV locales activan contratos adicionales en CMake. En CI sin los ejecutables locales se ejecutan los contratos sintéticos, no el oráculo comercial.

`tools/verify-dat.py` compara CSV generados por `resource_probe` con XML de Shady Packer y los píxeles RGBA independientes. Herramientas/resultados y DAT permanecen ignorados por Git.

Para auditar decodificación real de imágenes en todas las versiones PAT, ejecutar `tools/run-pat-image-audit-vita.ps1`; este empaqueta y ejecuta el sondeador ARM en Vita3K aislada y espera a que el guest termine para copiar el TSV. La corrida actual decodificó las 12,189 imágenes referenciadas por poses de los 20 PAT candidatos; queda una referencia no ofensiva sin recurso en PAT `common`. El TSV distingue entradas sin uso, recurso ausente, paleta ausente y CV2 inválida/no soportada. `tests/test_pat_image_decode.py` comprueba el resumen del TSV. La auditoría y galería no demuestran que cada movimiento sea alcanzable ni que los gráficos sean visualmente idénticos a PC.

La auditoría de cobertura de escenarios acepta múltiples manifiestos para modelar la prioridad/fallback de DAT TH123 y TH105 y guarda `source_archives` por ID. Regenerar el inventario conjunto con:

```powershell
python tools/audit_stage_resources.py artifacts/th105-resource-manifest.tsv artifacts/th123-resource-manifest.tsv --output docs/STAGE_RESOURCE_AUDIT.tsv --json artifacts/stage-resource-audit.json
```

La tabla de recursos registra presencia y procedencia, no composición jugable; los auxiliares se marcan como reconocidos desde constructor y pueden seguir pendientes de renderizado. Ver [ITERATION141.md](ITERATION141.md).

El gate Vita3K schema46 exige `stage-bg33-layout.bmp` y `stage-bg33-scroll.bmp`, 24 tiles, la máscara completa de 30 ranuras, 30 quads aceptados por Soft2D, la relación `counter == updates & 0x3ff` y los vectores viewport/quad del PE. La captura scroll usa una cámara cero encajada para diagnóstico; aún no verifica estado vivo del manager ni paridad de escena en combate. Ver [ITERATION148.md](ITERATION148.md), [ITERATION149.md](ITERATION149.md) e [ITERATION150.md](ITERATION150.md).


Además, desde la Iteración 2.192 el menú de preparación permite alternar BG33/BG36 con arriba/abajo antes de confirmar el combate. El gate schema46 recorre esa selección, exige `battle_stage_selected_interactively=1`, captura BG36 con cámara activa y mide sus 25 tiles/cuatro auxiliares; luego vuelve a BG33 para conservar sus regresiones. Esto valida selección y dibujo, no la paridad final de cámara ni composición. Ver [ITERATION292.md](ITERATION292.md).


BG36 base tiles: el gate automático exige 25 tiles presentes, 25 draws y máscara  x3ffff79c; esta integración requiere repetir Vita3K SDL y confirmar un reporte fresco antes de citarla como runtime verificado.
