# Iteración 2.63: decoder estructural del replay 2009

## Loader localizado

En el PE original suministrado (SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`), el loader de archivo es `0x42e030`; no es el lector del listado de replays ni el `0x42eac0` del ejecutable más nuevo. Después de abrir la ruta, el loader:

1. Lee el DWORD de versión y lo compara con `0x43ca50` (`0x100c8` en la configuración del archivo).
2. Lee 10 bytes adicionales. El byte 7 es la cuenta de registros: el replay Sanae contiene 3.
3. Deserializa cada registro mediante `0x42cd60` a una estructura en memoria de stride `0x50`.

`0x42cd60` lee dos grupos, cada uno con dos bytes, una cuenta DWORD y una secuencia de `uint16`, seguidos de tres bytes; luego un trailer de tres bytes, un DWORD y otra cuenta/vector de `uint16`. `tools/replay_layout.py` implementa ese orden; `tools/inspect_replay_layout.py` también verifica el hash/build mediante el checker de compatibilidad. El parser aplica límites a las cuentas y falla ante truncación o bytes restantes.

## Resultado del archivo aportado

`090815_2219_sanae_story.rep`, SHA-256 `6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e`: el parser reproduce tres registros desde offset `0x0e` hasta EOF `0x10929`, consume 67,881/67,881 bytes y deja cero sobrantes. Las secuencias finales tienen 8,720, 6,932 y 18,168 valores `uint16`, respectivamente. El reporte [replay-layout-original-2009.json](../artifacts/kernel/replay-layout-original-2009.json) contiene límites, contadores y muestras iniciales/finales, no una copia del `.rep`.

El orden de bytes y la consumición exacta están demostrados contra el flujo de lecturas del PE. Los nombres son descriptivos del layout, no semántica confirmada: aún no sabemos si los valores representan ticks, offsets, estados de entrada u otra secuencia; tampoco se ha ejecutado el replay en el juego PC ni en Vita.

## Verificación

Seis pruebas sintéticas cubren decode, offsets, límite de registros, cuentas corruptas, truncación y bytes extra. El parser real pasó sin residuo. Para repetirlo con el PE y `.rep` del usuario:

```powershell
$env:PYTHONPATH = (Resolve-Path local/python-deps).Path
python tools/inspect_replay_layout.py `
  'F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\replay\story\090815_2219_sanae_story.rep' `
  --exe 'F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe' `
  --output artifacts/kernel/replay-layout-original-2009.json
```

Siguiente: rastrear consumidores de los campos deserializados en el PE para etiquetar canales y secuencias; después comparar una ventana frame-stepped del juego original antes de conectar replay al runtime Vita. El VPK no cambió en esta iteración.
