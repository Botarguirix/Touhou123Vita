# Touhou123Vita

Proyecto experimental para reconstruir y adaptar **Touhou 12.3: Hisoutensoku** a PS Vita.

La iteración 0.2 incorpora un **lector nativo de DAT externos**, CV2/PAL/PAT y un kernel de animación recuperado y contrastado con el x86 original. La arena de práctica reproduce poses y usa cajas/daño de 5A de Reimu y Cirno. **El motor completo de Hisoutensoku aún no está portado**: física, selección de acciones, reacción al golpe, proyectiles, cartas, clima, escenario y replays todavía requieren recuperación y comparación con PC.

El repositorio contiene código, pruebas y documentación. Los ejecutables de PC, paquetes comerciales, recursos convertidos, pseudocódigo y VPK con recursos permanecen locales y están excluidos de Git.

## Documentación

- [Roadmap y criterios de aceptación](docs/ROADMAP.md)
- [Requisitos y arquitectura](docs/REQUIREMENTS.md)
- [Fuentes investigadas](docs/RESEARCH.md)
- [Estado y evidencia](docs/STATUS.md)
- [Pruebas automáticas y Vita3K](docs/TESTING.md)
- [DAT externos y formatos](docs/DATA.md)
- [Kernel original y oráculo x86](docs/KERNEL.md)

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

## Controles de la demo

| Acción | PS Vita | Teclado Vita3K de referencia |
|---|---|---|
| Confirmar / entrar a práctica | Cruz | X |
| Moverse / saltar | Izquierda, derecha / arriba | Flechas |
| Golpe | Cuadrado | Z |
| Guardia | R | E |
| CPU activa / muñeco | L | Q |
| Reiniciar pelea | Select | Shift derecho |
| Volver | Círculo | C |

Title ID de desarrollo: `THSV12301`. La demo interactiva no contiene `auto-test.txt`; el VPK de prueba sí, ejecuta 600 fotogramas y produce un reporte antes de salir. Proyectiles originales y especiales todavía pendientes; esta arena integra 5A como primera acción real basada en datos.

Tras preparar y ejecutar la prueba local, abrir la demo interactiva con `./tools/play.ps1`. Las pruebas de Vita3K y el estado exacto están documentados en `docs/STATUS.md`.
