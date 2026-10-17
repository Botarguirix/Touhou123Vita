# Iteración 1.42: gate x86 de activación de skills de Reimu

## Condiciones recuperadas

La rama de skill del handler `004ae670` no se evalúa en cualquier tick:

- El `CharacterFrameData` actual debe traer `FrameFlags.cancellable` (`frameData+0x4c & 0x20`). El bit `highJumpCancellable` (`0x200000`) comparte el primer despacho de cancelaciones, pero por sí solo no permite continuar al bloque de skills.
- El `CharacterSequenceData.actionLock` (`sequenceData+0x12`) debe ser menor que `0x33` (51); el handler pasa ese valor como segundo argumento a `useSkill`.
- La tecla `spellcard` actual (`Player+0x770`) debe valer 1 o 2, o su valor bufferizado (`Player+0x790`) debe ser distinto de cero.
- `confusionDebuffTimer` (`Player+0x524`) y `stopwatchTimeLeft` (`Player+0x84c`) deben valer cero. También debe ser cero el byte de Player `+0x836`; su significado sigue sin identificarse.
- La primera carta de la mano debe tener ID 100–199 y la ruta seleccionada depende de `Player::isGrounded()`: en el aire hay ocho casos explícitos; en el suelo, doce.
- Para una acción actual ≥300, `collisionType` (`GameObjectBase+0x190`) no puede ser 0 ni 3. Acciones menores de 300 pasan esta condición.
- `canActivateCard(0)` debe permitir pagar la carta.

## Oráculo de costo de carta

Ejecuté `Player::canActivateCard` (`00468e80`) de la imagen x86 fijada, reemplazando solo el acceso a la deque por un stub de puntero controlado. Ocho casos cubren mano vacía, slot fuera del rango, costo por encima o igual a la cantidad de cartas, `weatherId == 2` (descuento observado de un punto con costo mínimo 1), `weatherId == 11` (permite activar con al menos una carta aunque el costo exceda la mano) y lectura del slot 1. Todos mantienen la pila balanceada.

El oráculo y su reporte son `tools/x86_card_activation_oracle.py` y `artifacts/x86-card-activation-oracle.json`. Se regenera así:

```powershell
python tools/x86_card_activation_oracle.py
```

El inventario de rutas ahora añade `activation_gate` con las condiciones, offsets y hashes de las estructuras SokuLib contrastadas. El JSON `artifacts/reimu-skill-card-routes.json` se regenera con `python tools/analyze_skill_card_routes.py`.

## Verificación y límites

- `tests/test_card_activation_oracle.py` ejecuta los ocho contratos del helper x86.
- `tests/test_skill_card_routes.py` contrasta los offsets y el contexto tierra/aire contra el handler decompilado y las estructuras SokuLib.
- Suite Python completa: 15 pruebas. Esta iteración sigue siendo análisis/oráculo; el runtime Vita todavía no activa skills, no se modeló el significado de `Player+0x836`, y no se generó VPK.

## Próximo paso

Emular el handler Reimu alrededor de `004ae670` con memoria de Player/deque y stubs registrados para los helpers no pertinentes. Barrer `cancellable`, `actionLock`, tecla `spellcard`, estado tierra/aire, carta y costo de mano; capturar la acción enviada a `useSkill`, la actualización de niveles, consumo y primer estado/frame. Eso convertirá el gate estático en una traza x86 ejecutable que luego podrá guiar la primera skill en el runtime ARM.
