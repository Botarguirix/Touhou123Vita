# Iteración 2.137: geometría PE de Udonge 418:1 responde a la posición del defensor

Extendí `x86_player_pair_hit_probe.py` para aceptar posiciones y facing de ambos jugadores y barrer X del defensor. La fixture continúa ejecutando los constructores base, setters/pose selectors y sincronizador `0x465e10` del PE fijado (SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`), además de `0x4640b0` para las cajas transformadas y `0x47a5b0` para hit-vs-hurt. En Udonge 418:1/pose 0 contra Udonge 400:0/pose 0, X atacante 320, Y=180 para ambos, attacker facing +1 y defender facing -1, la barrida X defensora 280–480 en pasos de 10 produjo contacto exactamente para 320–450. El barrido fino halló transición entre 318 (sin contacto) y 320 (contacto), y entre 458 (contacto) y 460 (sin contacto). Con facing atacante -1 y defensor +1, la misma pareja es asimétrica: X=320 conecta, X=322 no conecta; no se refleja el intervalo simplemente alrededor del atacante.

El registro muestra siete transformaciones por pareja en el caso de contacto: cinco de la caja ofensiva del atacante y las cajas defensiva/hurtbox del defensor, todas vía `0x4640b0` con los facing actualmente instalados. La variante `0x464200` no aparece en esta postura; es una rama alternativa de conversión, no un helper requerido por rol. La aplicación de daño sigue llegando al resolver, pero la respuesta concluye en `0x0` después de mutar HP. Escenario/cámara, estadísticas, efectos, inputs y tiempo permanecen controlados; esto es una comparación geométrica estática, no combate nativo ni replay.

Añadí una regresión para los cuatro bordes observados y un modo CLI reproducible. Artefacto: [x86-udonge-418-position-sweep.json](../artifacts/kernel/x86-udonge-418-position-sweep.json), generado con:

```powershell
python tools/x86_player_pair_hit_probe.py --dat-dir original --character udonge --action 418 --sequence 1 --frame 0 --attacker-x 320 --attacker-y 180 --defender-y 180 --attacker-facing 1 --defender-facing -1 --sweep-defender-x 280 480 10 --output artifacts/kernel/x86-udonge-418-position-sweep.json
```

La prueba focalizada pasa 5/5. No se recompiló VPK porque el runtime Vita no cambió. Siguiente: recuperar el facing/cámara de un combate real y obtener una secuencia temporal equivalente del PE o del replay; luego cotejar el resolver y ajustar el runtime Vita con pares de cajas comparables. No extrapolar este alcance de pose única al C natural de roster.
