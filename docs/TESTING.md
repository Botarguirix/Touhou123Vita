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

El guest pasa por menú, abre la galería PAT con Triangle, cambia personaje, pose y acción, vuelve con Circle; abre el visor con L, recorre los IDs hasta `bg34`, activa su vista compuesta `0000`+`0001`, inspecciona recursos auxiliares y revisa el mapa de colocación. Este último usa escala de inspección; no representa la cámara final. Deben decodificar 4 bitmaps y 30 sprites `objectFa`. La escena resalta el frame activo con `frame=floor(tick/2)` y tick módulo 60, según la referencia Ghidra. Regresa al menú, alcanza práctica y pelea durante 600 frames. El reporte exige navegación, 30+30 tiles, 4+30 recursos extra, cadencia correcta, galería PAT, roster 20/20, salto, matcher de dash `NRNR`/`NLNL` con historial de 15 muestras, impactos B/C y pérdida de vida. El probe del build acepta 12 muestras neutrales entre toques y rechaza 13. La duración del dash, locks y paridad temporal frente a PC siguen pendientes. El runner guarda `artifacts/screenshots/stage-assets.bmp` y `stage-layout.bmp`, archiva evidencia previa y registra hash, fecha UTC y resultado frescos. Ver [ITERATION26.md](ITERATION26.md).

Desde la Iteración 1.83 el reporte schema31 exige una máscara completa `roster_a_attack_mask=0xFFFFF`: cada PAT debe tener una entrada terrestre entre 300/302/303/304/330 que, usando colocación controlada por hitboxes y hurtboxes PAT, aplique el daño de su pose. Desde Iteración 1.85 también exige `roster_a_natural_attack_mask=0xFFFFF`: cada personaje se acerca desde spawn normal con `IN_RIGHT` a Cirno inmóvil y debe conectar A sin reubicar cajas ni luchadores; el runner sigue exigiendo `a_hits>0` en el combate principal y guarda `fight-natural-a.bmp`. Desde Iteración 1.86 los campos `roster_b_natural_attack_mask` y `roster_c_natural_attack_mask` recogen impactos B/C por personaje; son diagnósticos y el runner solo valida su presencia/rango, no cobertura completa. El runner guarda `artifacts/roster-bc-natural.tsv` con las acciones PAT candidatas y las que conectaron. Esto no demuestra matchups con defensa/IA ni paridad frente a PC. Ver [ITERATION86.md](ITERATION86.md), [ITERATION85.md](ITERATION85.md), [ITERATION84.md](ITERATION84.md) y [ITERATION83.md](ITERATION83.md).

Para inventariar poses con daño y flags de ataque usa `python tools/summarize_pat_attack_flags.py artifacts/pat-detail.tsv docs/PAT_ATTACK_FLAGS.md`. La prueba sintética del formato se ejecuta con `python -m unittest discover -s tests -p test_pat_attack_flags.py -v`. El reporte agrupa por personaje/acción/índice/flags y presencia de cajas; no interpreta bits ni valida contactos en runtime. Ver [ITERATION87.md](ITERATION87.md).

Para exportar una ventana de desensamblado del ejecutable fijado, usa `python tools/disassemble_pe_windows.py --window 00465e10:240 --output artifacts/ghidra/selected-window.tsv`. Repite `--window VA:LENGTH` para incluir más direcciones. El script rechaza cualquier PE cuyo SHA-256 no coincida con la referencia documentada. Ver [ITERATION88.md](ITERATION88.md).

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
