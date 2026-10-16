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

En Windows, usar un VitaFS de pruebas con copia del firmware ya instalado:

```powershell
./tools/vita3k-test.ps1 -Vita3K 'C:/ruta/Vita3K.exe' -Config 'C:/ruta/config.yml' -VitaFS './artifacts/vitafs' -Vpk './build-vita-auto/Touhou123Vita.vpk'
```

El guest pasa por menú y práctica, mueve al jugador, salta y ataca durante 600 frames. El runner archiva el reporte anterior y solo acepta evidencia nueva, con escena de pelea alcanzada, salto, impactos y pérdida de vida del oponente. Guarda hash del VPK, fecha UTC y resultado. Un timeout o una ventana de instalación no equivale a un pase.

Para automatización reproducible se recomienda una versión de Vita3K con `--frontend sdl` y añadir `-Frontend sdl` al runner. No usar `--console` para ejecutar por Title ID: es un modo de instalación. El runner mantiene una copia local del emulador y su configuración predeterminada, porque Vita3K valida `-r` antes de aplicar `--config-location`. No modifica la instalación del usuario.

`tools/run-all.ps1` encadena pruebas host, compilación Vita, VPK automático y validación Vita3K en una sola ejecución. Requiere font/assets y VitaFS preparados. `tools/play.ps1` instala la variante interactiva en el VitaFS local, retira conservando el indicador de autoprueba y abre una ventana para jugar.

También exige las tres capturas del framebuffer guest, revisa errores críticos del runtime y el código de salida, y guarda evidencia bajo `artifacts/`. Los contratos host incluyen guardia y KO. Un reporte de pelea seguido de un crash no se considera aprobado.

La variante automática sale después del reporte; la interactiva queda disponible para jugar. Solo el runner puede cerrar su propio proceso hijo en caso de timeout. No interrumpe procesos de otros proyectos.

## Verificación manual y futura

- Menú -> práctica -> arena mediante controles reales.
- Caminar, saltar, golpe, proyectil, guardia, reset, toggle CPU, volver al menú.
- Registrar capturas y comprobar gráficos/legibilidad.
- No aceptar animación automática como prueba de entradas de teclado.
- Después de recuperar el motor original: comparar hitboxes, tiempos, daño, cartas/clima y replays contra PC.
- Repetir en Vita física antes de cerrar compatibilidad y rendimiento.

GitHub Actions ejecuta pruebas host en pushes y PRs. Vita3K se ejecuta localmente con firmware y datos locales; no se descargan juegos ni firmware en CI público.

## Iteración 0.2

Preparar `ux0/data/touhou123vita/th123a.dat`, `th123b.dat` y `th123c.dat` en el VitaFS aislado. El VPK ya no lleva imágenes del juego. El reporte usa schema 3 y exige los tres DAT, más de dos texturas decodificadas y pérdida de vida respecto de `max_hp`.

Los oráculos opcionales se generan con `tools/x86_animation_oracle.py` y las dependencias de `tools/requirements-oracle.txt`; los CSV locales activan contratos adicionales en CMake. En CI sin los ejecutables locales se ejecutan los contratos sintéticos, no el oráculo comercial.

`tools/verify-dat.py` compara CSV generados por `resource_probe` con XML de Shady Packer y los píxeles RGBA independientes. Herramientas/resultados y DAT permanecen ignorados por Git.
