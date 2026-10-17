# Touhou123Vita

Proyecto experimental para reconstruir y adaptar **Touhou 12.3: Hisoutensoku** a PS Vita.

El prototipo incluye un **lector nativo de DAT externos**, CV2/PAL/PAT, un kernel de animación contrastado con x86 y catálogos locales de 22 carpetas PAT. Vita3K verifica PAT, sprites y tarjetas de los 20 personajes cuando están disponibles los DAT de 12.3 y los DAT heredados de 10.5. El auto-test schema31 conecta A naturalmente con los 20 personajes (`0xFFFFF`) contra Cirno inmóvil; B/C son sondas diagnósticas de momento (14/20 y 15/20) y aún no son gates completos. Esto no demuestra todos los matchups ni paridad por frame. **El motor completo de Hisoutensoku aún no está portado**: rutas B/C y skills del roster, objetos, cartas, clima, escenarios completos, audio y replays requieren recuperación y comparación con PC.

El repositorio contiene código, pruebas y documentación. Los ejecutables de PC, paquetes comerciales, recursos convertidos, pseudocódigo y VPK con recursos permanecen locales y están excluidos de Git.

## Documentación

- [Roadmap y criterios de aceptación](docs/ROADMAP.md)
- [Iteración 1.89: handler x86 de Remilia 2C](docs/ITERATION89.md)
- [Iteración 1.88: sincronización de cajas PAT desde el PE](docs/ITERATION88.md)
- [Iteración 1.87: inventario de attack_flags PAT](docs/ITERATION87.md) y [reporte de combinaciones](docs/PAT_ATTACK_FLAGS.md)
- [Iteración 1.86: rutas B/C naturales y selección de variantes](docs/ITERATION86.md)
- [Iteración 1.85: rutas A naturales para todo el roster](docs/ITERATION85.md)
- [Iteración 1.84: impacto A tras aproximación normal](docs/ITERATION84.md)
- [Iteración 1.83: gate de ataque A para los 20 PAT](docs/ITERATION83.md)
- [Iteración 1.82: rebuild fresco y regresión Vita3K](docs/ITERATION82.md)
- [Iteración 1.80: sincronización de cajas del objeto 808](docs/ITERATION80.md)
- [Iteración 1.81: consumidores de cajas y fases de pares](docs/ITERATION81.md)
- [Requisitos y arquitectura](docs/REQUIREMENTS.md)
- [Fuentes investigadas](docs/RESEARCH.md)
- [Estado y evidencia](docs/STATUS.md)
- [Iteración 1.39: revisión actualizada de Touhou75Vita y vdpm](docs/ITERATION43.md)
- [Iteración 1.40: cartas de skill de Reimu a acciones PAT](docs/ITERATION44.md)
- [Iteración 1.41: contrato x86 de onSkillUpgrade](docs/ITERATION45.md)
- [Iteración 1.42: gate x86 de activación de skills](docs/ITERATION46.md)
- [Iteración 1.43: despacho x86 de skills ejecutado](docs/ITERATION47.md)
- [Iteración 1.44: primera skill Reimu jugable en Vita3K](docs/ITERATION48.md)
- [Iteración 1.46: contrato x86 del loop PAT y corrida fresca](docs/ITERATION50.md)
- [Iteración 1.47: selección de secuencias PAT ejecutada contra x86](docs/ITERATION51.md)
- [Iteración 1.38: activación de skills contrastada con x86](docs/ITERATION42.md)
- [Iteración 1.37: cobertura de instrucciones de handlers](docs/ITERATION41.md)
- [Iteración 1.36: ráfaga de Suwako 418](docs/ITERATION40.md)
- [Pruebas automáticas y Vita3K](docs/TESTING.md)
- [Roadmap integral](docs/ROADMAP.md)
- [Iteración 1.0: arte original del roster y evidencia Vita3K](docs/ITERATION10.md)
- [Iteración 1.1: auditoría de versiones PAT e idle](docs/ITERATION11.md)
- [Iteración 1.2: DAT 10.5 y prueba Vita3K 20/20](docs/STATUS.md)
- [Inventario de DAT](docs/RESOURCE_INVENTORY.md) y [cobertura PAT](docs/PAT_COVERAGE.md)
- [Cruce de poses dañinas e imágenes en cinco DAT](docs/PAT_RESOURCE_COVERAGE.md)
- [DAT externos y formatos](docs/DATA.md)
- [Kernel original y oráculo x86](docs/KERNEL.md)
- [Referencias de puertos Vita y recompilación](docs/PORT_REFERENCES.md)
- [Iteración 1.20: matcher x86 bajo Unicorn](docs/ITERATION24.md)
- [Iteración 1.21: revisión Touhou75Vita y helper C experimental](docs/ITERATION25.md)
- [Iteración 1.22: matcher C/ARM integrado y prueba Vita3K](docs/ITERATION26.md)

## Compilar

Requisitos: CMake 3.16+, compilador C11, Python 3, Pillow para convertir recursos/fuente; VitaSDK para generar VPK. No requiere vita2d: el prototipo dibuja directamente al framebuffer.

```bash
cmake -S . -B build-host -DCMAKE_BUILD_TYPE=Debug
cmake --build build-host -j2
ctest --test-dir build-host --output-on-failure
python3 tools/font.py assets
export VITASDK=/ruta/vitasdk
bash tools/build.sh
```

Para ejecutar, copiar `th123a.dat`, `th123b.dat` y `th123c.dat` desde la instalación propia a `ux0:data/touhou123vita/`. Vita los interpreta directamente; no se empaquetan recursos comerciales en el VPK. Ver `docs/DATA.md`. Shady Packer se usa solo como referencia independiente de validación en PC. No se integra código de SokuLib en el runtime ARM: sus estructuras/direcciones sirven como referencias para análisis.

En Windows con VitaSDK se puede crear directamente el VPK interactivo con `tools/build-vita-native.ps1 -Output artifacts/Touhou123Vita.vpk`. Para cubrir los sprites idle referenciados desde Touhou 10.5, coloca también `th105a.dat` y `th105b.dat` en la misma carpeta de datos. El VPK automático [Touhou123Vita-matcher.vpk](artifacts/Touhou123Vita-matcher.vpk) se compiló y pasó Vita3K SDL el 16 oct 2026 (SHA-256 `e9be67a7dff4b3400a0bb52752589ad66bdbe356bde02a87df701e64f0ea0361`). La corrida automática aislada se ejecuta con `./tools/vita3k-test.ps1 -Vpk ./artifacts/Touhou123Vita-auto.vpk -Frontend sdl`, una vez creado ese VPK con `-AutoTest` y preparado el VitaFS local. El matcher de dash `NRNR`/`NLNL` ya está portado y contrastado contra x86; la captura del productor de entrada, los replays y la paridad de combate completa siguen pendientes.

La build interactiva experimental está en [Touhou123Vita-skill-demo.vpk](artifacts/Touhou123Vita-skill-demo.vpk), SHA-256 `35162bf1dbc601887d7245e36c37ea27f87cb368a9d08c33fcc5891831ccf54d`. Con Reimu, `L + Circle` activa la carta fija de prueba 103 → acción PAT 560; mano/costo y el resto de las skills aún no están portados. La autoprueba [Touhou123Vita-skill-sequence-probe.vpk](artifacts/Touhou123Vita-skill-sequence-probe.vpk) pasó Vita3K SDL schema21 en una corrida fresca: los primeros 11 updates no causan daño en PAT 0 y el update 12 entra a PAT 1 para golpear. El loop de seq. 2 requiere una transición externa aún no recuperada. Ver [ITERATION49.md](docs/ITERATION49.md), [ITERATION50.md](docs/ITERATION50.md) y la [revisión de Touhou75Vita](docs/TOUHOU75_REUSE_REVIEW.md).

## Controles de la demo

| Acción | PS Vita | Teclado Vita3K de referencia |
|---|---|---|
| Confirmar / entrar a práctica | Cruz | X |
| Moverse / saltar | Izquierda, derecha / arriba | Flechas |
| Golpe | Cuadrado | Z |
| B experimental (no validado) | Triángulo | X |
| C experimental (no validado) | Círculo durante el combate | C durante el combate |
| Guardia | R | E |
| CPU activa / muñeco | L | Q |
| Reiniciar pelea | Select | Shift derecho |
| Volver a práctica | Start | Escape |

Title ID de desarrollo: `THSV12301`. La demo interactiva no contiene `auto-test.txt`; el VPK de prueba ejecuta 600 fotogramas y produce un reporte antes de salir. A está verificado para el alcance de la demo Reimu/Cirno. B/C continúan experimentales: la hipótesis inicial de control 400/500 fue refutada por la autoprueba. Las entidades de proyectil y especiales todavía están pendientes.

Tras preparar y ejecutar la prueba local, abrir la demo interactiva con `./tools/play.ps1`. Las pruebas de Vita3K y el estado exacto están documentados en `docs/STATUS.md`.
