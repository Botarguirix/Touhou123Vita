# Touhou123Vita

> **Ruta vigente desde el 21 de octubre de 2026:** [recompilación estática del PE original para Vita](docs/ROADMAP_RECOMP.md). F0 completada: el motor hecho a mano quedó congelado en [`legacy/`](legacy/README.md) (etiqueta `legacy-reimpl-2.199`) y el [inventario del PE](docs/PE_INVENTORY.md) confirma la ruta. Lo que sigue debajo describe el prototipo legacy.

- [Iteración 2.199: cajas PAT en unidades de mundo](docs/ITERATION299.md)
- [Iteración 2.198: inicio de jugadores y cámara recuperado del PE](docs/ITERATION298.md)
- [Iteración 2.197: límites de mundo para combate PAT](docs/ITERATION297.md)
- [Iteración 2.196: recorte del lienzo 4:3 y referencia visual pendiente](docs/ITERATION296.md)
- [Iteración 2.195: cámara de la captura BG36 registrada](docs/ITERATION295.md)
- [Iteración 2.194: scroll de nubes BG36 comprobado durante combate](docs/ITERATION294.md)
- [Limpieza y conservación de artefactos](docs/ARTIFACTS.md)

Proyecto experimental para reconstruir y adaptar **Touhou 12.3: Hisoutensoku** a PS Vita.

El prototipo incluye un **lector nativo de DAT externos**, CV2/PAL/PAT, un kernel de animación contrastado con x86 y catálogos locales de 22 carpetas PAT. Vita3K verifica PAT, sprites y tarjetas de los 20 personajes cuando están disponibles los DAT de 12.3 y los DAT heredados de 10.5. El auto-test vigente schema46 valida roster, combate y escenarios en Vita3K durante 600 frames; Iteración 2.59 añade una regresión del ciclo de objetos Remilia 801/seq.1 comparada con la fixture x86. El visor enumera los 25 IDs del dispatcher x86; BG02 verifica 48 sprites, ciclo de 16 frames y offsets locales extraídos del PE; BG12 y BG36 tienen capturas de sus capas de análisis tomadas en escena, y BG34 conserva sus dos rejillas, assets estáticos y animación. BG35 está en el dispatcher pero no tiene carpeta en los manifiestos locales de DAT 10.5/12.3. La sonda parcial de impactos B/C llega a 15/20 y 15/20 (Alice conecta ambas rutas por objetos); no cuenta specials por comandos/flags y no es un gate integral del roster. Esto no demuestra todos los matchups ni paridad por frame. **El motor completo de Hisoutensoku aún no está portado**: faltan rutas B/C y skills del roster, objetos, cartas, clima, composición/mecánicas completas de escenarios, audio y replays contrastados con PC.

El repositorio contiene código, pruebas y documentación. Los ejecutables de PC, paquetes comerciales, recursos convertidos, pseudocódigo y VPK con recursos permanecen locales y están excluidos de Git.

## Documentación

- [Iteración 2.193: orientación de filas BG36 corregida según el constructor PE](docs/ITERATION293.md)
- [Iteración 2.192: selector de escenario BG33/BG36 conectado al combate](docs/ITERATION292.md)
- [Iteración 2.191: orden de capas BG36 según el renderer x86](docs/ITERATION291.md)
- [Iteración 2.190: cielo base BG36 reconstruido desde el PE](docs/ITERATION290.md)
- [Iteración 2.189: BG36 ya no hereda BG10 bajo sus capas](docs/ITERATION289.md)
- [Iteración 2.188: BG36 integrado y validado en Vita3K](docs/ITERATION288.md)

- [Iteración 2.187: auxiliares BG36 visibles durante el combate](docs/ITERATION287.md)
- [Iteración 2.186: BG33 integrado a la escena de combate](docs/ITERATION286.md)
- [Iteración 2.185: `Player+0x884` no explica aún la recuperación natural de Suika](docs/ITERATION285.md)
- [Iteración 2.184: VPK con LiveArea y Vita3K validado](docs/ITERATION284.md)
- [Iteración 2.183: ausencia BG35 en los seis DAT locales](docs/ITERATION283.md)
- [Iteración 2.182: huecos BG36 tolerados por el loader original](docs/ITERATION282.md)
- [Iteración 2.181: auditor de recursos corrige la cuadrícula BG33](docs/ITERATION281.md)
- [Iteración 2.180: registros y contadores de progreso Story](docs/ITERATION280.md)
- [Iteración 2.179: inventario de las campañas Story](docs/ITERATION279.md)
- [Iteración 2.178: el PE carga las tablas Story del roster](docs/ITERATION278.md)
- [Iteración 2.177: Namazu es el rival de la etapa 4 de Meiling](docs/ITERATION277.md)
- [Iteración 2.176: ruta Story carga el personaje desde CSV](docs/ITERATION276.md)
- [Iteración 2.175: el roster persistente limita los personajes a IDs 0–19](docs/ITERATION275.md)
- [Iteración 2.174: GameDataManager alimenta el factory de Player](docs/ITERATION274.md)
- [Iteración 2.173: writer del timer localizado en Namazu](docs/ITERATION273.md)
- [Iteración 2.172: selector de input 2 asociado al lado derecho](docs/ITERATION272.md)
- [Iteración 2.171: expiry del timer enlazado con Spell Break](docs/ITERATION271.md)
- [Iteración 2.170: nueve updates asignan contadores `+0x884` de 300](docs/ITERATION270.md)
- [Iteración 2.169: action96 sigue 1.200 ticks con InfoManager HUD aislado](docs/ITERATION269.md)
- [Iteración 2.145: matcher PE confirma NRNR con updates consecutivos](docs/ITERATION245.md)
- [Iteración 2.144: KeyInput x86 encadenado con acción 418](docs/ITERATION244.md)
- [Iteración 2.143: productor PE condicional de la acción 418](docs/ITERATION243.md)
- [Iteración 2.142: gate de aterrizaje x86 para Suika 418](docs/ITERATION242.md)
- [Iteración 2.141: timeline x86 de Suika 418](docs/ITERATION241.md)
- [Iteración 2.140: definiciones PAT crudas y efectivas](docs/ITERATION240.md)
- [Iteración 2.139: VPK interactivo y autotest reconstruidos y validados](docs/ITERATION239.md)
- [Iteración 2.138: sincronización Story condicional y replay revalidado](docs/ITERATION238.md)
- [Iteración 2.137: geometría PE de Udonge 418:1 sensible a posición](docs/ITERATION237.md)
- [Iteración 2.131: Suika 623B nivel 9 crea y conecta PAT 821](docs/ITERATION231.md)
- [Iteración 2.129: factory original y PAT 821 de Suika 623B nivel 9](docs/ITERATION229.md)
- [Iteración 2.128: Suika 623B por niveles, PAT 520/525/530](docs/ITERATION228.md)
- [Iteración 2.126: ciclo x86 del efecto visual PAT 821/seq.1](docs/ITERATION226.md)
- [Iteración 2.127: reacción de Remilia tras PAT 821](docs/ITERATION227.md)
- [Iteración 2.125: ciclo x86 de movimiento y fade de PAT 821](docs/ITERATION225.md)
- [Iteración 2.124: Suika 623C/531 impacta con PAT 821](docs/ITERATION224.md)
- [Iteración 2.123: dispatcher Suika 623C según niveles 5/9](docs/ITERATION223.md)
- [Iteración 2.122: Suika 623C conecta ambas ventanas PAT](docs/ITERATION222.md)
- [Iteración 2.121: primer comando especial de Suika conectado al combate](docs/ITERATION221.md)
- [Iteración 2.120: VPK del árbol actual reconstruido y validado](docs/ITERATION220.md)
- [Iteración 2.119: decoder y contador enlazados a una invocación Story](docs/ITERATION219.md)
- [Iteración 2.118: slot 5 Story llama slot 16; cadence aún pendiente](docs/ITERATION218.md)
- [Iteración 2.117: VPK actual revalidado y evaluación de psp2-tooling](docs/ITERATION217.md)
- [Iteración 2.116: dispatcher de Story y frecuencia del replay](docs/ITERATION216.md)
- [Iteración 2.115: rama de fila seleccionada llega al loader replay](docs/ITERATION215.md)
- [Iteración 2.114: CReplayList y replay Sanae conectados estáticamente](docs/ITERATION214.md)
- [Iteración 2.113: selección Story y loader replay en CTitle](docs/ITERATION213.md)
- [Iteración 2.107: replay Sanae completo en callback Story x86](docs/ITERATION207.md)
- [Iteración 2.106: callback Story ejecutado en Unicorn](docs/ITERATION206.md)
- [Iteración 2.105: objeto de input compartido con el decoder Story](docs/ITERATION205.md)
- [Iteración 2.104: ciclo global de selección y update del manager](docs/ITERATION204.md)
- [Iteración 2.103: selector de modo y dos rutas Story](docs/ITERATION203.md)
- [Iteración 2.102: manager Story y canales de replay son estados distintos](docs/ITERATION202.md)
- [Iteración 2.101: RTTI del manager resuelve el dispatch de replay](docs/ITERATION201.md)
- [Iteración 2.100: cursor C por parejas validado con el replay real en Vita3K](docs/ITERATION200.md)
- [Iteración 2.99: método x86 de input probado con todo el replay](docs/ITERATION199.md)
- [Iteración 2.98: revalidación Vita3K del VPK con recorte PAT](docs/ITERATION198.md)
- [Iteración 2.97: alcance del estado de sampler en SpriteEx](docs/ITERATION197.md)
- [Iteración 2.96: WRAP inicial del sampler x86](docs/ITERATION196.md)
- [Iteración 2.95: ruta x86 de dibujo PAT y recortes extremos](docs/ITERATION195.md)
- [Iteración 2.94: variantes PAT con recortes extremos](docs/ITERATION194.md)
- [Iteración 2.93: test de recorte desplazado dentro del guest](docs/ITERATION193.md)
- [Iteración 2.92: corregidos los límites del recorte PAT](docs/ITERATION192.md)
- [Iteración 2.91: campos del quad PAT aplicados al renderer](docs/ITERATION191.md)
- [Roadmap y criterios de aceptación](docs/ROADMAP.md)
- [Herramientas de análisis y plan de profiling en Vita física](docs/ANALYSIS_AND_TESTING_TOOLING.md)
- [Iteración 2.59: ciclo completo de objetos secundarios Remilia 801](docs/ITERATION159.md)
- [Iteración 2.58: estado x86 de objetos secundarios Remilia 801](docs/ITERATION158.md)
- [Iteración 2.57: replay Sanae compatible con el PE original proporcionado](docs/ITERATION157.md)
- [Iteración 2.40: catálogo x86 completo y captura real de BG36](docs/ITERATION140.md)
- [Iteración 2.20: update original 5AAA y lookup de spell background](docs/ITERATION120.md)
- [Iteración 2.19: dispatcher original del defensor y estado inválido](docs/ITERATION119.md)
- [Iteración 1.90: caja collision de Remilia 2C](docs/ITERATION90.md)
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

El VPK interactivo más reciente es [Touhou123Vita-udonge-409-interactive.vpk](artifacts/Touhou123Vita-udonge-409-interactive.vpk), SHA-256 `64AB8EA453C1A2183C3089C1F176BF73AE69E5CF8DAA99EE68CFB75350F44954`. El autotest [Touhou123Vita-udonge-409-auto.vpk](artifacts/Touhou123Vita-udonge-409-auto.vpk), SHA-256 `DA7B2DA4B19DF9F21A98B1C19E28B90FFE8A44D3D951AB44227D7F40DD5A9363`, pasó Vita3K SDL schema46/600. El barrido registra 18/20 impactos B y 17/20 C normal; Udonge/Tenshi/Cirno conectan B aéreo 409:1 y el runner exige Udonge 400 de daño. El selector de variantes sigue provisional. Ambos VPK comparten `eboot.bin` SHA-256 `5BBF5848B37925E074CF948AB32062B1437923ACE324620C30B97331BF055354`. Evidencia y faltantes: [reporte](artifacts/vita3k-result.json), [roster-bc-natural.tsv](artifacts/roster-bc-natural.tsv) e [ITERATION234.md](docs/ITERATION234.md). Sigue siendo un prototipo; falta gran parte del motor, roster y paridad.

En Windows con VitaSDK se puede crear directamente el VPK interactivo con `tools/build-vita-native.ps1 -Output artifacts/Touhou123Vita.vpk`; usa `-Os` por defecto y admite `-Optimization 2` o `-Optimization 3` para comparar otros niveles. Para cubrir los sprites idle referenciados desde Touhou 10.5, coloca también `th105a.dat` y `th105b.dat` en la misma carpeta de datos. El VPK automático [Touhou123Vita-matcher.vpk](artifacts/Touhou123Vita-matcher.vpk) se compiló y pasó Vita3K SDL el 16 oct 2026 (SHA-256 `e9be67a7dff4b3400a0bb52752589ad66bdbe356bde02a87df701e64f0ea0361`). La corrida automática aislada se ejecuta con `./tools/vita3k-test.ps1 -Vpk ./artifacts/Touhou123Vita-auto.vpk -Frontend sdl`, una vez creado ese VPK con `-AutoTest` y preparado el VitaFS local. El matcher de dash `NRNR`/`NLNL` ya está portado y contrastado contra x86; la captura del productor de entrada, los replays y la paridad de combate completa siguen pendientes.

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
