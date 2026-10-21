# Iteración 2.68: oráculo x86 sobre el stream real de replay

## Implementación del oráculo

Se añadió `tools/x86_replay_input_probe.py`, que valida el SHA-256 del ejecutable original 2009, carga su PE32 en Unicorn y ejecuta la función original `0x42a410` con words reales del `.rep`. Se aíslan los locks y el setter global de input; el setter conserva solamente el byte bajo de sus argumentos booleanos porque el original usa `SETA` y deja sin definir los bytes altos del registro antes de hacer `push`.

Con ambos flags de fuente (`this+0xf0 == 3`) activos, la rutina consume dos words por llamada: el primero escribe `word & 0x03ff` en `this+0x68` y actualiza seis IDs (`0x3b`, `0x3c`, `0x3d`, `0x3f`, `0x40`, `0x41`) desde los bits altos; el segundo escribe solo `word & 0x03ff` en `this+0xd0`. Esta semántica es la observada en el PE, no nombres de botones.

## Corrida con datos del usuario

El oráculo ejecutó todas las parejas del replay `090815_2219_sanae_story.rep`: 8.720, 6.932 y 18.168 words en sus tres registros, para 4.360, 3.466 y 9.084 llamadas, respectivamente. La comprobación es pareja por pareja: el primer y segundo `button_mask` coinciden en cada llamada, los seis callbacks del primer word coinciden en toda la secuencia y el cursor termina agotado. Las 16.910 llamadas pasan. Reporte reproducible local: `artifacts/x86-replay-input-oracle.json`.

Comando (requiere el PE y replay propios, más las dependencias Python locales):

```powershell
python tools/x86_replay_input_probe.py "F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\replay\story\090815_2219_sanae_story.rep" --exe "F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe" --output artifacts/x86-replay-input-oracle.json
```

## Límites y siguiente paso

El probe confirma decoder y avance bajo ambos slots activos; no ejecuta el loop completo del combate ni determina si cada llamada coincide con un frame de simulación. El origen/configuración de `this+0xf0` se sigue en [ITERATION169.md](ITERATION169.md); las diferencias de decodificación entre slots se implementan en C/Python en [ITERATION170.md](ITERATION170.md). La ruta `0x4600fe` agrega otra consulta/sincronización que espera coincidencia con `[0x85eb58]`. El runtime y el VPK no cambiaron.
