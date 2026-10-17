# Iteración 1.27: rutas de dash auditadas para el roster

## Hallazgo del ejecutable

Partiendo de `vtable-handlers.tsv`, `tools/disassemble_character_handlers.py` recorre bloques alcanzables desde cada slot 20 del PE fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. Capstone encontró entre 1,930 y 2,951 instrucciones por handler; `tools/summarize_character_handlers.py` resume pushes de acciones que no corresponden a los argumentos de `getMoveLock` y los locks consultados. Los TSV y desensamblados detallados son artefactos locales en `artifacts/kernel/<sha>/character-input/`.

Resultado del cruce: 19/20 handlers tienen candidatos de dispatch 408 y 418; Remilia no los presenta. La rutina de Reimu muestra el patrón completo de estado 200 → consulta `getMoveLock(408/418)` → llamada virtual `setAction(408/418)`. Sakuya también muestra el uso de esos IDs en el handler propio. Remilia consulta y despacha 412 (2C), coherente con `Action.hpp`; conserva una ruta distinta. La identificación de IDs en los otros handlers es análisis estático de argumentos/CFG, no reconstrucción de todas las condiciones ni evidencia de que cada movimiento cause daño.

La comparación también reveló que el prototipo consultaba `moveLock` del índice 0 aunque su selector de demo pudiera animar otra variante. `src/fight.c` ahora consulta el lock de la misma variante elegida para el ataque. El contrato sintético usa locks 1/3/6 en las variantes 0/1/2 y confirma que el índice ofensivo 2 acepta frame 6 y rechaza frame 7.

## Prueba en el VPK

El probe automático carga cada PAT original y prueba ambos lados del borde inclusivo de `moveLock` para 408 y 418 en los 19 personajes que poseen esas acciones: el límite permite cancelar el dash y el frame siguiente la rechaza. Para Remilia confirma que el PAT carece de 408/418 y que abajo+C selecciona su acción 412; este caso valida selección, no daño ni objetos.

Build VitaSDK y Vita3K SDL aprobados: 600 frames, `dash_gate_probe=1`, 20/20 PAT y recursos de roster, 137 texturas decodificadas, escenario BG34 presente, cero fallos de textura. El VPK vigente es `artifacts/Touhou123Vita-roster-dash.vpk`, SHA-256 `8344d35f5d63a6d5c907b326c59f6116ccedf2ab076697ba5c1db3d142b7b2d0`. Reporte fresco: `artifacts/vita3k-result.json`.

## Verificación y siguiente trabajo

```powershell
$env:VITASDK='C:\vitasdk'
./tools/build-vita-native.ps1 -Output artifacts/Touhou123Vita-roster-dash.vpk -AutoTest
$env:VITA3K_HOME='G:\Vita3k'
./tools/vita3k-test.ps1 -Vpk artifacts/Touhou123Vita-roster-dash.vpk -Frontend sdl -VitaFS artifacts/vitafs
```

Las pruebas Python pasaron con `python -m unittest discover -s tests -p 'test_*.py'` (8 pruebas).

La siguiente brecha es reconstruir las condiciones y efectos de acción por personaje (especialmente variantes PAT, hitboxes/objetos de Remilia y estados de cancelación), y cotejarlos con trazas por frame de PC. Esta cobertura de dash no equivale a un combate completo ni a paridad funcional.
