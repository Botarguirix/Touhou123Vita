# Iteración 2.27: diagnóstico B/C con orientación correcta

Fecha: 2026-10-17.

## Cambio en la sonda

`probe_character_natural_bc()` cargaba el personaje candidato en slot 0, pero el input de aproximación siempre era `IN_RIGHT`. Al quedar el rival en su slot real (Reimu), personajes cargados a la derecha se alejaban de él. La prueba ahora aproxima usando el `face` calculado por el combate, refleja las direcciones relativas al rival, fija el CPU a 380 unidades y busca once offsets de airtime para ataques aéreos (antes cinco). Las rutas dash siguen generando NRNR y verificando acción 200 antes del ataque.

La corrida no encontró que la orientación o el tiempo explicaran los casos ausentes. Para la build de diagnóstico B es `0x0EBBBE` (15/20) y C `0x0BF9B7` (15/20), comparado con la lectura anterior `0x0EBBBE/0x0BF9BF`. La única máscara que cambió fue C: Suwako dejó de conectar en este probe por objeto, lo cual confirma que el fixture geométrico aún no es estable para todas las rutas object-backed. No debe convertirse en requisito del runtime ni tomarse como regresión de juego sin comparar la pelea de referencia.

## Alcance de las máscaras

El probe explora ataques neutrales, direccionales, aéreos y de dash seleccionados desde PAT, y valida daño directo o algunos objetos. No ejecuta el `handleInputs` original del personaje ni llena `Player+0x7c8` con comandos reales, niveles/costos de skill o flags internos. El CFG de Suika `0x609dc0` documenta branches 623C y 623B (bits `0x400/0x200`) y checks de nivel antes de despachar a `useSkill`; esos specials quedan fuera de los bits B/C actuales. Por ello, un cero en la máscara significa “esta ruta de sonda no detectó impacto”, no “el personaje carece de ataque”.

## Verificación

- VPK diagnóstico: `artifacts/Touhou123Vita-bc-probe-next.vpk`, SHA-256 `0339fb5e6e16c955b31fc22d1295ca1eb3516d84d308291e0cbc5b4c00893e02`.
- Vita3K SDL aislado schema31: `passed`, 600 frames; el reporte `artifacts/vita3k-result.json` coincide con el hash del paquete.
- A natural 20/20; PAT/sprites/tarjetas 20/20; BG34 tiles 30/30, alternos 30/30, 4 recursos estáticos y 30 objetos; skills de regresión 102/103/104/107 aprobadas.
- La sonda extendida tomó más tiempo de arranque porque se ejecuta dentro de auto-test, pero no alteró los 600 frames de juego ni el resultado de los otros gates.

## Siguiente paso

La próxima mejora debe construir un probe de player/handler x86 con input producer, buffer de movimiento, vtable del personaje, PAT y estado de cartas/controlados en puntos explícitos. Debe registrar acción, variante, pose, objetos y daño; luego se portan únicamente transiciones confirmadas. También se debe estabilizar la colisión de objetos por orientación antes de convertir la máscara C en gate. Paridad de los otros escenarios y del match completo sigue pendiente.
