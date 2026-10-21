# Motor reimplementado a mano (congelado)

Este directorio contiene el motor C escrito a mano durante las iteraciones 1.0–2.199: lector de DAT/CV2/PAL/PAT, kernel de animación, combate parcial, escenarios BG02–BG38, replays y la app Vita con framebuffer por software.

**Está congelado desde el 21 de octubre de 2026** (etiqueta `legacy-reimpl-2.199`). La ruta principal es ahora la recompilación estática del PE original ([docs/ROADMAP_RECOMP.md](../docs/ROADMAP_RECOMP.md)). Aquí solo se aceptan correcciones para que siga compilando o para reutilizarlo como oráculo o herramienta de inspección.

Se sigue construyendo con los mismos comandos desde la raíz del repositorio (`CMakeLists.txt` y `tools/build-vita-native.ps1` apuntan a `legacy/`).

| Ruta | Contenido |
|---|---|
| `src/`, `include/t123/` | Motor y app Vita (`vita_main.c`, `soft2d.c`) |
| `tests/*.c` | Pruebas C nativas y `auto-test.txt` del autotest de Vita3K |

Las pruebas Python de `tests/` y las sondas x86 de `tools/` siguen en la raíz: sirven tanto al motor congelado como de oráculos para el código recompilado.
