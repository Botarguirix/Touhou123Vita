# Iteración 0.4: estados base, cadenas A y ataques B/C

## Alcance

Esta entrega avanza la demo jugable de Reimu contra Cirno; no representa aún el juego comercial completo ni el roster de 20 personajes. Los datos se cargan desde DAT del usuario y quedan fuera del VPK.

## Cambios

- Control con IDs de acción PAT para caminar hacia/desde el rival, agacharse/levantarse, salto neutral/hacia delante/hacia atrás, caída y aterrizaje.
- A selecciona 5A, 6A, 2A, 3A, j5A, j6A o j2A; si el archivo de personaje no contiene una acción, el selector vuelve a 5A.
- Tras conectar, volver a pulsar A avanza por 5AA, 5AAA y 5AAAA cuando esos bloques existen en ese PAT. El rival puede recibir impactos mientras está en hitstun, requisito para probar combos.
- B y C seleccionan las acciones base 400 y 500 al pulsar Triangle/Circle (X/C en Vita3K), si el PAT de ese personaje tiene esos bloques. Tras confirmar impacto, la entrada permite cancelar a B/C; daño y cajas siguen saliendo de las poses PAT.
- Las reacciones iniciales de impacto y bloqueo usan sus acciones PAT (50/70 y 150/158) y el tiempo de stun leído del frame.
- El runner de juego instala el VPK indicado dentro de `artifacts/vitafs` y abre la copia portátil local de Vita3K. No cambia la instalación compartida.

Los IDs comunes de estado se contrastaron con el enum público de [SokuLib, `CharacterManager.hpp`](https://github.com/SokuDev/SokuLib/blob/51486a0c400201313f6afff1155e8f84bbb9d809/src/Core/CharacterManager.hpp#L1879). La física de este prototipo sigue aproximada; esos IDs no certifican paridad de comportamiento.

## Verificación

- Host: 8/8 contratos aprobados. `fight_contract` cubre estados de movimiento, selección A, cadena hit-confirm 5A→5AA→5AAA→5AAAA y entrada B/C con cajas sintéticas PAT.
- VitaSDK: VPK interactivo y automático construidos desde la misma fuente.
- Vita3K SDL: cinco instalaciones frescas y corridas aprobadas. Cada una completa 600 frames, carga 7 DAT y 71 texturas, logra 11 impactos y deja la CPU con 8250/10000 HP; digest determinista `3845639945`, salida guest 0.
- Hash del VPK automático validado: `82f8acbeb7c3dcc342223214a1ce73932d85c142d10f1d8d8ed933483d4bee4b`. El interactivo se entrega en `artifacts/Touhou123Vita-combat-iter.vpk`.
- Se corrigió el runner para extraer el contenido antes de cerrar el ZIP. La serie antigua de cinco ejecuciones se invalidó; los resultados anteriores a este punto no se cuentan como pruebas de una instalación fresca.
- El smoke automático confirma que el runtime y los recursos siguen funcionando; todavía no automatiza las combinaciones nuevas ni mide FPS.

## Pendiente antes de llamarlo combate completo

Reproducir trazas PC para velocidad/física y transiciones; comprobar qué acciones B/C aparecen realmente en ambos PAT y validar sus cancelaciones contra la referencia; recuperar la creación/actualización de entidades para proyectiles y specials; resolver guardia, hitstop, knockback, rounds y victoria con reglas contrastadas; recorrer acciones de Reimu/Cirno para asegurar cobertura visual; añadir pruebas interactivas de teclado/Vita3K y medir FPS sostenidos. Después se repite en Vita real para ajustar rendimiento.
