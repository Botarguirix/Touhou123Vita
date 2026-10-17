# Iteración 1.43: despacho x86 de skills de Reimu ejecutado

## Resultado medido

Ejecuté con Unicorn los dos bloques de tabla de saltos originales dentro de `handleInputs` de Reimu (`004ae8b1` terrestre, `004af821` aéreo), usando el PE local fijado por SHA-256. El test recorre las 12 cartas de skill en tierra y las ocho cartas con caso explícito en aire. Cada ruta alcanza `useSkill` (`00487ba0`) con la acción esperada y `actionLock=23`; también se observan una llamada a `eventSkillUse` (`00483ce0`) y una a `onSkillUpgrade` (`00489660`) antes de `useSkill`. El epílogo original regresa con la pila balanceada en las 20 rutas.

El harness stubea `eventSkillUse` y `onSkillUpgrade` para aislar la selección de acción. Por eso esta corrida ejecuta el switch y su epílogo original, no los efectos laterales ni los guards compartidos de entrada del handler. Las cuatro cartas sin caso aéreo continúan verificadas por el análisis de la tabla/handler; probar su destino dinámico implicaría ejecutar el resto del handler, fuera del alcance de este oráculo.

## Oráculo reproducible

`tools/x86_skill_handler_dispatch_oracle.py` regenera `artifacts/x86-skill-handler-dispatch.json`. Ejecuta las 20 rutas conocidas y falla si cambia el hash de `original/th123.exe`, una acción enviada a `useSkill`, su `actionLock`, las llamadas esperadas o el retorno de pila.

```powershell
python tools/x86_skill_handler_dispatch_oracle.py
python -m unittest tests.test_skill_handler_dispatch_oracle -v
```

## Alcance y siguiente paso

El dispatch x86 queda demostrado, pero aún no tenemos una traza integral que satisfaga dinámicamente los guards de `handleInputs`, y las skills no están implementadas en el runtime Vita. El siguiente paso es recuperar un fixture válido de frame, secuencia, input, carta y estado del jugador desde una ejecución/replay PC; luego emular la función desde su entrada con stubs acotados y barrer gates, antes de portar una primera ruta de skill y comparar sus frames/efectos. No se generó VPK en esta iteración.
