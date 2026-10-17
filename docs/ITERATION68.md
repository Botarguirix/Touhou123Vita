# Iteración 1.68: regresión integral en Vita3K del checkout actual

## Resultado

Se compiló el checkout actual a `artifacts/Touhou123Vita-current-autotest.vpk` con VitaSDK y se ejecutó una instalación/corrida fresca en la instancia Vita3K aislada (`local/vita3k-isolated`). SHA-256: `11d0c4df4f35a27edd275ef0bb96ed4f8751df26ba9a68c3576700ad385873c3`.

El reporte schema 28 pasó 600 frames. Evidencia: menú/galería/poses; 20/20 PAT del roster, 20/20 recursos de combate y 20/20 cartas; 31 DAT externos abiertos, 148 texturas decodificadas, sin fallas de textura; BG34 capa 3, layout/navegación, 30 tiles principales, 30 alternativos, 4 recursos estáticos y 30 objetos; práctica/combate/salto; 35 impactos directos PAT de dash; Suwako 418 con diez spawns y sprite/render; Reimu 560 con vuelo, inversión, aterrizaje e impacto; carta 102→540 con 1100; 107→565 con 450; 104→505, fases 3/4/5, cuatro objetos 811, sprite y 1100 de daño en el probe.

Reporte fresco: `artifacts/vita3k-result.json`. Capturas de la corrida en `artifacts/screenshots/`. El runner valida hash del VPK, cierre y criterios de aceptación definidos en `tools/vita3k-test.ps1`.

## Alcance

Esta corrida confirma que el estado actual integrado del VPK conserva las regresiones cubiertas. Los cambios de Iteración 1.67 fueron del oracle x86 y documentación, no del motor jugable; por tanto el VPK no contiene la física radial nueva de Suwako 808. La paridad de partida completa, el resto de acciones/personajes y escenarios/mecánicas siguen abiertos.
