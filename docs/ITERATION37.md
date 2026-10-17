# Iteración 1.33: contrato de geometría para Suwako 418

## Hallazgo del PE

El setter de espacio de escenario `00406d30` escribe `stage+0x98 = -param6` y `stage+0x9c = param5 - param7`. El adaptador `00438fc0` obtiene `param6` y `param7` de dos enteros con signo en el registro de metadatos apuntado por `object+0x150`: `-s16(metadata+0x0e)` y `-s16(metadata+0x0c)`. En las dos llamadas de la ruta Suwako 808 (`00789ed2` y `00789f0e`), `param5 = -object.y` (`object+0x37c`). Así, el contrato observable queda como:

- `stage+0x98 = s16(metadata+0x0e)`.
- `stage+0x9c = s16(metadata+0x0c) - object.y`.

El análisis comprobó el setter, adaptador y ambos callsites contra el PE 1.10a fijado por SHA-256 en `tools/analyze_object_motion.py`. Esto elimina la velocidad/offset inventados como hipótesis del análisis, pero aún no aporta los valores de los metadatos para la instancia de combate ni prueba que `object.y` sea el suelo global del escenario. No se sustituyeron todavía los valores provisionales del runtime.

## Revisión de Touhou75Vita

El chat **Configurar Touhou75Vita** y la revisión ya registrada en `PORT_REFERENCES.md` aportan una buena guía para hacer inventarios de funciones, CFG/reachability, cobertura de instrucciones, lifting por unidades y pruebas pequeñas fail-loud. Su prueba Linux solo cubrió un runtime semántico mínimo; su VPK de diagnóstico inspecciona cabeceras PE, y VitaSDK no quedó instalado en aquel entorno por el proxy. No hay licencia clara en el checkout revisado, así que no incorporé código de Touhou75 ni trasladé direcciones entre los juegos. Para TH123 seguiremos usando el PE local, hash fijo y comparaciones por ruta.

## Verificación

- `tools/analyze_object_motion.py` imprime los contratos y comprueba las llamadas directas relevantes del PE fijado.
- Suite Python: 8/8 pruebas; `git diff --check` limpio.
- El VPK de la iteración anterior sigue disponible: [Touhou123Vita-object-motion-auto.vpk](../artifacts/Touhou123Vita-object-motion-auto.vpk), SHA-256 `73dd3c237d56e372ad96d6bea26cc414dea66973d7e94b55915ebcf7eece0f28`. Esta iteración cambia el análisis/documentación; no recompila el VPK.

## Siguiente paso

Rastrear de dónde se llena `object+0x150` y cómo se elige la instancia/posición `object+0x37c` para la ruta 418, decodificar esos datos para el escenario activo y luego alimentar los dos valores al runtime. Después medir trayectoria, aterrizaje, daño y destrucción contra una traza x86.
