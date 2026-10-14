# Touhou123Vita

Proyecto experimental para reconstruir y adaptar **Touhou 12.3: Hisoutensoku** a PS Vita.

La primera implementación es un **prototipo nativo de práctica con reglas propias**. Tiene menú, pantalla de práctica, jugador contra CPU, movimiento, salto, golpe, proyectil, guardia, vida, KO y reinicio. Usa sprites convertidos de la instalación local cuando están disponibles. **Todavía no ejecuta la lógica original de Hisoutensoku**: movimientos, colisiones, cartas, clima, animaciones y escenarios originales siguen pendientes. No debe presentarse como un port fiel ni como una decompilación completa.

El repositorio contiene código, pruebas y documentación. Los ejecutables de PC, paquetes comerciales, recursos convertidos, pseudocódigo y VPK con recursos permanecen locales y están excluidos de Git.

## Documentación

- [Roadmap y criterios de aceptación](docs/ROADMAP.md)
- [Requisitos y arquitectura](docs/REQUIREMENTS.md)
- [Fuentes investigadas](docs/RESEARCH.md)
- [Estado y evidencia](docs/STATUS.md)
- [Pruebas automáticas y Vita3K](docs/TESTING.md)

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

Para incluir recursos propios, extraer localmente `th123a.dat` con Shady Packer, usando una ruta sin paréntesis si la versión de la herramienta no acepta la ruta original:

```text
shady-cli pack -m dir -o artifacts/extracted original/th123a.dat
python tools/prepare_assets.py artifacts/extracted assets
```

Conservar las licencias de las herramientas por separado. No se integra código de SokuLib en el runtime ARM: sus direcciones x86 sirven como referencias para análisis.

## Controles de la demo

| Acción | PS Vita | Teclado Vita3K de referencia |
|---|---|---|
| Confirmar / entrar a práctica | Cruz | X |
| Moverse / saltar | Izquierda, derecha / arriba | Flechas |
| Golpe | Cuadrado | Z |
| Proyectil | Triángulo | V |
| Guardia | R | E |
| CPU activa / muñeco | L | Q |
| Reiniciar pelea | Select | Shift derecho |
| Volver | Círculo | C |

Title ID de desarrollo: `THSV12301`. La demo interactiva no contiene `auto-test.txt`; el VPK de prueba sí, ejecuta 600 fotogramas y produce un reporte antes de salir.

Tras preparar y ejecutar la prueba local, abrir la demo interactiva con `./tools/play.ps1`. Las pruebas de Vita3K y el estado exacto están documentados en `docs/STATUS.md`.
