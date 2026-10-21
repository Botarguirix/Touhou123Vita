# Iteración 2.26: objetos Alice 849 con cadena PAT

Fecha: 2026-10-17.

## Hallazgo del PE

La sonda `tools/x86_suwako_808_factory_probe.py --character alice --action 849 --ticks 80 --copy-box-transform` ejecuta el factory y dispatcher `0x7876D0` originales. Al crear el objeto con `customData[2]=19`, inicia action 849/seq.19. El update original avanza a seq.20 después de tres ticks y a seq.21 tras recorrer seq.20; seq.21 permanece como bucle. PAT seq.20 contiene poses de 150 con cajas ofensivas; seq.21 contiene poses de 450 con dos cajas ofensivas.

## Cambio en el runtime

`T123Object` ahora avanza por los descriptores PAT del action y guarda la secuencia activa en su estado. Alice 66B crea el objeto 849 en seq.19 y puede continuar por seq.20/21; su vida local permite completar esa cadena. Cuando una caja del objeto conecta, el objeto se desactiva y el barrido se detiene en ese mismo update para que las dos cajas PAT superpuestas no resten dos veces el daño de un único impacto.

## Verificación

- Vita3K SDL aislado, corrida fresca schema31/600 frames: `passed`.
- Cobertura natural A 20/20, B 15/20 (`0x0EBBBE`) y C 16/20 (`0x0BF9BF`). Alice B y C registran acción 408/418 con daño PAT; los fallos restantes están en `artifacts/roster-bc-natural.tsv`.
- PAT, sprites de combate y tarjetas 20/20; BG34 con 30 tiles y 30 tiles alternos, 4 assets estáticos y 30 objetos cargados.
- Pruebas Python: 45/45. VitaSDK compila `src/fight.c` y `tests/fight_tests.c` con `-Wall -Wextra -Werror`; no fue posible ejecutar el binario de pruebas C en host por la falta de CMake/WSL disponible.
- SHA-256 `artifacts/Touhou123Vita-current.vpk`: `8368849683ba22301bd69e25d6cc273d4fc056ee9b23d44d04ce744122881340`, coincide con el reporte fresco `artifacts/vita3k-result.json`.

## Pendiente

Completar y contrastar los objetos 849 fuera de este callsite, los otros dash objects y las nueve rutas B/C restantes; después extender la comparación a input/replay real y no solo a sondas controladas. Este avance no demuestra paridad completa del motor ni cobertura total de escenarios.
