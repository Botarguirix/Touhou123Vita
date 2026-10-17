# Iteración 1.82: rebuild fresco y regresión Vita3K

Fecha: 2026-10-17 (America/Mexico_City).

## Build

Se compiló desde las fuentes actuales con:

```powershell
.\tools\build-vita-native.ps1 -Output .\artifacts\Touhou123Vita-current-auto.vpk -AutoTest
```

El VPK resultante mide 95,972 bytes y su SHA-256 es `d361adfe700db32c6789d8eb2288d4c39d723c8d020bc3a4b92ed9b22b830318`.

## Corrida aislada

```powershell
.\tools\vita3k-test.ps1 -Vpk .\artifacts\Touhou123Vita-current-auto.vpk -Frontend sdl -TimeoutSeconds 120
```

La prueba produjo un reporte nuevo schema 28 con `status=passed`, 600 frames y el mismo hash de VPK. Pasaron menú, galería, práctica y combate; navegación de BG34; salto, dash, rutas de objetos y las secuencias de skill 560, 540, 565 y 505. El reporte registra 20/20 recursos PAT, sprites y tarjetas de personaje, cero fallos de textura y 148 texturas decodificadas. BG34 cargó 30 tiles por plano, cuatro assets estáticos y 30 objetos animados; la captura del combate muestra dos sprites y el HUD.

## Alcance y pendientes

Es una regresión automatizada del prototipo, no una prueba de combate completo ni de paridad con TH123. Los veinte personajes están cargados en la galería/roster, pero no son veinte personajes jugables. Solo se valida BG34; los otros 23 escenarios, la lógica completa de escenario, las mecánicas de combate, la respuesta original de hit/daño y la integración distribuible de los DAT siguen pendientes. El reporte indica `a_hits=0`. Los recursos comerciales no están dentro del VPK; la corrida los encuentra en el VitaFS local de prueba.

El VPK, el reporte y las capturas están en `artifacts/` y excluidos de Git por `.gitignore`. Esta iteración no cambia el runtime de combate; tampoco porta la mecánica Suwako 808 que sigue en análisis x86.
