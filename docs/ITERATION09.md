# Iteración 0.9: selector de roster y autoprueba diagnóstica

## Resultado

El prototipo ahora permite cambiar el personaje en menú/práctica y trata de resolver un sprite ligado al PAT de cada personaje antes de contar su cobertura. Un test nuevo en Vita3K, con VPK extraído desde cero en la instancia portátil local, duró 600 frames y escribió un reporte fresco.

| Medida | Resultado |
|---|---:|
| Menú / práctica / pelea | alcanzados |
| Salto | detectado |
| PAT cargados | 20/20 |
| Sprites de preview decodificados | 11/20 |
| Texturas decodificadas | 93 |
| Impactos A / B / C | 3 / 0 / 0 |
| CPU | 9600/10000 HP |
| DAT internos | 7 |
| Salida Vita3K guest | código 0 |

La build no pasa la aceptación integral: faltan nueve sprites de roster y no hay impactos B/C. Este VPK es diagnóstico, no sustituye la iter06 como última base de combate conocida.

Se hicieron dos instalaciones y corridas frescas consecutivas con el mismo VPK; ambas dieron el mismo digest (`2562787365`) y métricas, por lo que la secuencia automatizada es reproducible.

- VPK: `artifacts/Touhou123Vita-iter09-diagnostic.vpk`
- SHA-256: `79070659b1fa8c144f68af7abe141fefccfcc465aa66e369f2617a1a45a0f5bc`
- Reporte: `artifacts/vitafs/ux0/data/touhou123vita-smoke.json`
- Matriz del roster: `artifacts/vitafs/ux0/data/touhou123vita-roster.tsv`
- Capturas de guest: `artifacts/screenshots/{menu,practice,fight}.bmp`

## DAT y lookup de sprites

Se compararon los SHA-256 de `th123a.dat`, `th123b.dat` y `th123c.dat` de `F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law` con la copia instalada en el VitaFS; los tres coinciden exactamente. El problema de los nueve sprites no se debe a paquetes distintos.

Los PAT de Sakuya, Youmu, Remilia, Yuyuko, Udonge, Aya, Komachi, Iku y Tenshi piden imágenes `standNNN.bmp`, pero el inventario no contiene la entrada CV2 homónima. Sí hay otros CV2 para esas carpetas (ataques, guardia, salto, proyectiles y efectos) y la extracción local produce XML/PAT con las referencias esperadas. Por eso no se introdujo una sustitución visual: falta recuperar el esquema real de lookup/alias/carpeta compartida del juego o confirmar cómo están divididos esos recursos.

El barrido diagnóstico recorre las poses del primer bloque idle de cada PAT y cuenta sólo un sprite CV2 decodificado. El renderer de combate permanece ligado a la imagen activa del PAT. La cobertura del selector no equivale a cobertura de todas las poses, hitboxes o acciones del personaje.

## Ghidra y siguiente trabajo

El script `tools/ghidra/ExportKernel.java` lista `handleGroundBE` (`00487990`) y `handleAirBE` (`00487ab0`), pero esta sesión no tuvo acceso ejecutable a la distribución de Ghidra ni pudo iniciar WSL para ejecutar el análisis. Se conservaron como evidencia estática los pseudocódigos exportados de métodos Reimu/Cirno (`004ac670`, `004ae670`, `006fa260`, `006fb8b0`); éstos llaman a los helpers de input y muestran rutas `useSkill`, pero no se debe inferir el mapeo completo de botones sólo de esa llamada.

Próximos pasos: (1) restablecer Ghidra y exportar los helpers añadidos; (2) localizar la regla de nombres/lookup de sprites y contratos de imagen contra recursos extraídos, empezando con Sakuya; (3) exigir cobertura visual PAT/CV2 verificable de los 20 personajes; (4) mapear B/C y volver a exigir impactos; (5) extender a escenarios, cartas, clima, rondas y trazas de referencia.
