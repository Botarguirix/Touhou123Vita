# Iteración 2.06: CRT inicializado y ciclo de vida del objeto Remilia 801

El PE entra en el inicializador CRT original `0x824bfa`. El probe resuelve `GetProcAddress` por nombre, reproduce `TlsAlloc/TlsSetValue`, `HeapAlloc` y el bloque FLS usado por el CRT. El inicializador termina sin acceso inválido: asigna el índice `0x40` y crea el bloque `0x214` bytes con `HeapAlloc`. Estos son servicios de host simulados; la factory y el dispatcher del juego siguen ejecutándose desde el PE.

El problema restante de tick 4 no era un fallo del CRT. El fixture de secuencias físicas no representaba el orden que selecciona la factory, y dejaba `+0x148=20` mientras seq.1 solo tenía dos frames. En tick 4, `0x464ae0` rechazaba el pose 2, fuera de `[0,2)`, y el handler CRT terminaba el proceso. Con los nodos PAT asignados al layout que selecciona la factory y el contador actualizado al cambiar de secuencia para inspeccionar las cajas, el objeto arranca como action 801/seq.1 con dos poses.

La corrida de 40 ticks ahora completa 18 updates originales, baja el alpha hasta 0 y pone `+0x34c=0`, sin excepción ni acceso inválido. Esto demuestra el fin del objeto en el dispatcher, pero no que el manager lo haya retirado. El sincronizador original publica una attack box para seq.0 y ninguna para seq.1; seq.1 no causa daño según PAT. Todavía no se ejecuta el setup natural emitido por Remilia 412 ni se demuestra un impacto.

Validación reproducible: `python tools/x86_suwako_808_factory_probe.py --character remilia --action 801 --ticks 40`; el reporte ignorado de esta corrida está en `artifacts/x86-remilia-801-sequence-map.json`. Suwako 808 aún completa ocho ticks y la suite Python pasa 39/39. No cambia el runtime Vita ni se genera un VPK.

Siguiente: conectar la secuencia y los parámetros exactos que crea Remilia 412, y seguir objetos/contactos hasta medir daño. La señal de seq.0 confirma una caja ofensiva del objeto, no un impacto real.
