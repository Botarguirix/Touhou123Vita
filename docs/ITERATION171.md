# Iteración 2.71: dispatch y avance del cursor de replay

La sonda nueva `tools/x86_replay_dispatch_probe.py` desensambla ventanas del PE original 2009 fijado por SHA-256 y comprueba los callbacks de input, sus referencias en tablas virtuales y la sincronización condicional por contador. El reporte reproducible es [`artifacts/x86-replay-dispatch-original-2009.json`](../artifacts/x86-replay-dispatch-original-2009.json).

Hallazgos del PE:

- Los métodos `0x47ee10` y `0x481040` tienen referencias en las tablas virtuales inspeccionadas y llaman `0x42a410` cuando el getter `0x43ced0` devuelve modo 2. Son callbacks distintos; las referencias no demuestran que ambos se ejecuten en una misma ronda.
- En `0x481040`, bajo su rama adicional (`0x43ccd0()==8` y guardas de estado/manager), se lee un `uint16` mediante `0x42ea50` con el índice del cursor, se escriben dos estados de input (`0x3c`, `0x3d`) y se incrementa una vez `[0x85d748]+0x14`.
- La ruta que incluye `0x4600fe` consulta el word corriente por `0x45bc50`, lo compara con `[0x85eb58]` y, cuando coincide, invoca `0x42a3a0` para consumir el elemento. El desensamblado completo posterior confirmó que, si no coincide, retorna sin consumir; no es una espera activa. Véase la corrección/evidencia ampliada en [ITERATION238.md](ITERATION238.md).

Esto concreta el avance por una invocación en la ruta observada. No prueba la frecuencia de invocación por tick/frame, el valor efectivo de configuración durante la reproducción Sanae ni qué callback se activa para cada modo de partida. La paridad de playback completa sigue pendiente; no se integró una cadence supuesta al runtime ni se reconstruyó VPK.

Validación: el probe verifica 8 invariantes del PE fijado; `tests/test_replay_dispatch_probe.py` corre contra el ejecutable original si está disponible. Las diez pruebas de `test_replay_layout.py` pasaron. Comando:

```powershell
$env:PYTHONPATH='local/python-deps'
python tools/x86_replay_dispatch_probe.py --exe 'F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe' --output artifacts/x86-replay-dispatch-original-2009.json
```

Siguiente gate: observar la llamada del callback y el cursor dentro de una sesión real con replay, relacionarlos con el tick/frame y recién entonces definir el adaptador de replay en Vita.
