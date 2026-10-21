# Iteración 2.125: ciclo de movimiento x86 del proyectil Suika PAT 821

Se completó la comparación del ciclo principal de PAT 821, acción 531/seq.0, con la traza del PE x86. La sonda guest captura 27 actualizaciones y verifica posición fraccionaria, gravedad, alpha, avance de pose y retiro antes de mover en la actualización 27. Sus puntos de control coinciden con la traza: primer cuadro `(420,0), alpha 255`; segundo `(387.1108,11.4707), alpha 245`; cuadro 26 `(-402.2309,136.7676), alpha 5`; cuadro 27 conserva la posición y queda inactivo. El renderer proyecta las coordenadas fraccionarias y mezcla el alpha capturado. Se amplió la ventana controlada de la sonda a 50 ticks, pues el startup de Suika dejaba menos de 27 ticks disponibles en la ventana anterior.

La prueba estricta terminó en Vita3K SDL: schema 46, 600 frames, `status=passed`, route mask 31, dos objetos y 800 HP de daño de PAT 821. La evidencia detallada está en `artifacts/vitafs/ux0/data/touhou123vita-suika821-debug.json` y `touhou123vita-suika821-motion.tsv`; reporte integral: `artifacts/vita3k-result.json`. La primera corrida con el gate de movimiento detectó que la ventana de 36 ticks solo producía 18 muestras; tras ampliarla, se registraron las 27 esperadas y pasó.

VPK construidos desde el árbol actual con VitaSDK:

- Interactivo: [Touhou123Vita-suika623c.vpk](../artifacts/Touhou123Vita-suika623c.vpk), SHA-256 `45a000dfa2de9af0273e31033bc590440d42242b8994c15e261108a4a466b7d0`.
- Autotest: [Touhou123Vita-suika623c-auto.vpk](../artifacts/Touhou123Vita-suika623c-auto.vpk), SHA-256 `d2352c1efb5b7bff84b426af8498cd6055ef0101977436359fe8d26cfeee0e87`.

La secuencia visual secundaria 821/seq.1 todavía carece de una traza de ciclo x86, y no se ha verificado en hardware Vita. Tampoco están cubiertos el hitstop/reacción completos, guardia, Spell 531, la progresión natural de cartas, el resto de skills/personajes ni la paridad integral de escenarios. Esta iteración cierra solo la trayectoria y el alpha del proyectil principal en una fixture de combate controlada.
