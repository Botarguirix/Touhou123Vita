# Iteración 1.38: helper común de activación de skill

## Evidencia x86

Los handlers `handleInputs` del PE 1.10a fijado llaman al helper común `Player::useSkill` (`00487ba0`). Un resumen del desensamblado de sus bloques acotados encontró 713 llamadas en los 20 handlers. El helper:

- activa el bit `0x08` de `Player+0x4ad` cuando su segundo argumento es `>= 10`, sin borrar los bits preexistentes;
- despacha su primer argumento a través de la función virtual `this->vtable[2]` (`setAction` en SokuLib);
- invoca `0046d950` para reinicializar el historial de comandos desde la muestra de input actual;
- escribe cero en el campo de 32 bits `Player+0x12c` (su significado semántico sigue sin confirmarse).

El helper paralelo de spell `00487b60` muestra la misma estructura y usa el flag `0x10`; su ejecución diferencial aún no está incluida aquí. Las llamadas desde handlers prueban que las skills usan IDs de acción `500+` y una transición distinta a los ataques normales. Todavía falta recuperar qué entrada de control/card selecciona cada ID, sus requisitos de cancelación y efectos específicos por personaje.

## Oráculo

`tools/x86_skill_use_oracle.py` ejecuta el código original de `00487ba0` bajo Unicorn con un `setAction` virtual controlado y el `0046d950` interceptado para aislar los efectos del wrapper. Cinco casos prueban despacho de acción, límite inclusivo del argumento secundario en 10, preservación de otros bits y puesta a cero de `+0x12c`.

El mismo oráculo ejecuta `0046d950` directamente y sustituye solo su helper de reconstrucción del ring `0046d890`. Una matriz de 144 combinaciones de ejes `{-1,0,1}` y los 16 estados de A/B/C/D confirma la muestra empacada y capacidad 90. No ejecuta el ciclo interno que llena las 90 posiciones; tampoco prueba el productor real de controles del sistema ni la semántica del campo `+0x12c`.

Resultado local: `artifacts/x86-skill-use-oracle.json`, ligado al SHA-256 del PE. Se regenera con:

```powershell
python tools/x86_skill_use_oracle.py original/th123.exe artifacts/x86-skill-use-oracle.json
```

## Consecuencia

El runtime actual no activa acciones de skill 500+ ni modela los requisitos de su uso. La relación estática de las 12 cartas de skill de Reimu con acciones PAT ya se recuperó en [ITERATION44.md](ITERATION44.md); los guards/cancelaciones, la ruta secundaria de acciones alternas, los efectos y el input configurado aún requieren trazas x86. El siguiente paso es portar una skill con hitbox directa junto con la transición `useSkill` y compararla por frame antes de generalizarla.
