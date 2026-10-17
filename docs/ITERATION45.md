# Iteración 1.41: contrato x86 de `onSkillUpgrade`

## Resultado medido

Ejecuté el helper original `Player::onSkillUpgrade` (`00489660`) bajo Unicorn contra el PE local fijado por SHA-256. Para cada carta de skill de Reimu, IDs 100–111, el helper hace lo siguiente:

- Incrementa `skilledSkillLevel[cardId - 100]` (base `Player+0x6c4`), convierte el estado inicial `-1` a nivel 1 y satura el nivel en 4.
- Escribe `-1` en las otras entradas del mismo grupo de cuatro: índices con igual residuo módulo 4. Esto coincide con las variantes de carta que comparten el mismo `costOrSlot` en el CSV de Reimu.
- Crea los objetos de acción `0x47` y `0x82 + nivel_resultante`; en la primera mejora se observa `[0x47, 0x83]`.
- Consume la carta con argumentos `(index=0, costOverride=0, cardNameTimer=60)`, llama el evento de spell use y termina mediante el tail-update `00468b50`.

Los nombres de los dos arrays se toman de SokuLib: `effectiveSkillLevel` empieza en `Player+0x6a4`, mientras que `skilledSkillLevel` empieza en `Player+0x6c4`. Este helper modifica el segundo. No infiero de estos writes por sí solos el comportamiento completo del ataque ni si todas las llamadas alcanzables representan la activación estándar de una skill.

## Oráculo reproducible

`tools/x86_skill_upgrade_oracle.py` ejecuta las instrucciones originales del helper y sustituye solo dependencias externas: acceso a la deque, creación de objetos, consumo de carta, evento spell y tail-update. Comprueba las 12 cartas, los slots declarados en `spellcard.csv`, la invalidación de variantes, el consumo/evento, las dos acciones de objeto, el balance de stack y cinco límites de nivel.

El reporte local es `artifacts/x86-skill-upgrade-oracle.json`. Comando:

```powershell
python tools/x86_skill_upgrade_oracle.py
```

## Alcance restante

La evidencia describe el helper compartido y sus efectos de estado con dependencias stubbed; todavía falta comprobar los guards/callers de `004ae670` mediante entradas x86, observar las rutas reales de activación de skills en combate y portar esos cambios al runtime Vita. Por personaje solo se cubrió Reimu. No se recompiló un VPK en esta iteración.
