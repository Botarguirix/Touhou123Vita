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

La variante automática sale después del reporte; la interactiva queda disponible para jugar. Solo el runner puede cerrar su propio proceso hijo en caso de timeout. No interrumpe procesos de otros proyectos.

## Verificación manual y futura

- Menú -> práctica -> arena mediante controles reales.
- Caminar, saltar, golpe, proyectil, guardia, reset, toggle CPU, volver al menú.
- Registrar capturas y comprobar gráficos/legibilidad.
- No aceptar animación automática como prueba de entradas de teclado.
- Después de recuperar el motor original: comparar hitboxes, tiempos, daño, cartas/clima y replays contra PC.
- Repetir en Vita física antes de cerrar compatibilidad y rendimiento.

GitHub Actions ejecuta pruebas host en pushes y PRs. Vita3K se ejecuta localmente con firmware y datos locales; no se descargan juegos ni firmware en CI público.
