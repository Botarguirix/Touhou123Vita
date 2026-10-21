# Iteración 2.28: inventario estático de dispatch de acciones

Fecha: 2026-10-17.

## Resultado

`tools/summarize_character_skill_dispatch.py` resume los CFGs de `handleInputs` del ejecutable fijado (`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`). En los 20 handlers aparecen 713 sitios donde el escaneo localiza un primer argumento inmediato entre 400 y 599 en `Player::useSkill`; hay 682 parejas handler/acción y pruebas sobre `Player+0x7c8` en los 20 CFGs. Los disassemblies están bajo `artifacts/kernel/<sha256>/character-input/`; el TSV regenerado localmente es `artifacts/character-skill-dispatch.tsv`.

Se verificó la interpretación con la firma `useSkill(int id, short action)` de `local/SokuLib/src/Player.hpp` y el probe ejecutable `tools/x86_skill_use_oracle.py`: el primer argumento se envía al `setAction` virtual. Es el action ID que debe compararse con PAT. El segundo argumento dinámico pasa por gates del handler, pero no selecciona la acción PAT en el cuerpo probado de `useSkill`. La extracción considera solo casos cuyo primer argumento es un `push` inmediato 400–599 dentro de las diez instrucciones previas, por lo que puede omitir llamadas preparadas de otra forma y no prueba alcanzabilidad normal.

En Suika `0x609dc0`, `InputCombination.hpp` confirma `0x400=623C`, `0x200=623B`, `0x40000000=22C` y `0x20000000=22B`. La rama 623C en `0x60a45c` consulta nivel y puede seleccionar acciones `0x213/0x20e/0x209` (531/526/521); 623B en `0x60a5b0` selecciona `0x212/0x20d/0x208` (530/525/520). Las rutas 22C/22B en `0x60abf3/0x60ad36` consultan `Player+0x6af` y agrupan `0x23b/0x236/0x231` (571/566/561) y `0x23a/0x235/0x230` (570/565/560). El catálogo PAT de Suika indica que 531/530 tienen poses sin cajas/daño directos; 526/525 tienen una pose dañina cada una, y 521/520 tienen varias variantes con daño. Esto hace importante seguir la selección de secuencia/objeto después de entrar en la acción.

## Verificación y límites

- `python -m unittest tests.test_character_skill_dispatch_summary tests.test_x86_suika_623c_dispatch_probe -v`: 2/2.
- Suites relacionadas de skills: 10/10.
- `tools/x86_suika_623c_dispatch_probe.py` ejecuta el bloque original 623C, comprueba selección 531/526/521 al variar niveles y consulta PAT para confirmar esos IDs.
- No cambia runtime, datos ni VPK. El TSV vive en `artifacts/`, ignorado localmente.
- El VPK diagnóstico disponible sigue siendo Iteración 2.27; esta iteración no genera una build nueva.

## Próximo paso

Extender el probe para seguir `setAction` y la selección de secuencia/pose de Suika 521/526/531, y luego producir el bit con el matcher y ring buffer originales en vez de inyectarlo. Contrastar con replay o PC y portar solo transiciones demostradas. El bloque 623C ya ejecuta sus gates de nivel/move-lock, pero aún no prueba input natural, actualización ni combate.
