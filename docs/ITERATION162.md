# Iteración 2.62: hit espejo de Remilia y VPK validado

## Correcciones de combate

El análisis del contrato de `Remilia 412 / objeto 801` encontró dos detalles que una comprobación vieja ocultaba:

- El trail seq.1 hereda `x_q/y_q` del objeto padre al aparecer. Su posición visible entera ya no se usa como sustituto de la coordenada cuantizada.
- Antes de probar colisión, el desplazamiento horizontal del hitbox del objeto se lleva al espacio local del dueño con su facing. `overlap()` aplica el espejo una sola vez; así la ruta hacia la izquierda no vuelve a reflejar el desplazamiento del mundo.

El contrato `fight_contract` comprueba spawn y posición cuantizada, avance en ambos sentidos, 120 HP de daño y `hit_done`. El contacto espejo ahora está probado; no es solo cobertura de la trayectoria.

## Validación host

Compilados directamente con GCC de MSYS2 usando `-std=c11 -Wall -Wextra -Werror` y corridos en Windows:

- Siete contratos nativos: `core`, `fight`, `animation`, `resource`, `pattern`, `input` y `stage` — todos pasaron.
- `python -m unittest discover -s tests -p 'test_*.py'` — **83 pruebas pasaron**.

WSL sigue devolviendo `Wsl/Service/E_ACCESSDENIED`; esta validación host no se atribuye a CTest ni a WSL.

## VPK y Vita3K

El build de VitaSDK produjo [Touhou123Vita-latest.vpk](../artifacts/Touhou123Vita-latest.vpk), 92,330 bytes, SHA-256 `a84133ecc36ef2ba19505a4bd7e5fe8c577c283d44152538b75e9825768c6c7b`.

`tools/vita3k-test.ps1 -Frontend sdl` pasó con reporte fresco: schema 46, 600 frames, `status=passed`, regression gate 1, dash probe 1, Suwako 418 con diez spawns, ciclo de objeto y trails Remilia presentes, sin error de ruta de objeto. Los contratos BG33 pasaron: viewport, quads, layout, scroll, 30 quads, 24 tiles, seis updates y máscara de slots `0x3fffffff`. La corrida usó la copia aislada `local/vita3k-isolated`.

## Siguiente trabajo de alcance completo

El VPK sigue siendo una reconstrucción progresiva, no la decompilación completa. Falta reproducir el replay Sanae (solo se verificó su cabecera compatible con el PE 2009), completar mecánicas y efectos visuales reales, cubrir todas las rutas de habilidades de los 20 personajes, componer los escenarios reconstruidos dentro del combate y medir rendimiento en hardware Vita. `psp2-tooling` queda reservado para esta última etapa si el hardware y firmware son compatibles.
