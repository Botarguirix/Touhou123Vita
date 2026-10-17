# Iteración 1.59: separar el transform del proyectil y el spawn del jugador

Al revisar el flujo de Suwako 418 confirmé que la evidencia de `00438fc0` se había atribuido demasiado ampliamente. Sus únicos callsites conocidos (`00789ed2` y `00789f0e`) están dentro del callback de actualización del objeto 808, no en el handler del jugador `0076f3b4`. El adaptador transforma los metadatos del frame y `object+0x37c` en los campos de transform de ese objeto. Los offsets PAT `ox/oy` de 808/seq. 0 describen, por tanto, la geometría de dibujo del proyectil; no prueban por sí mismos dónde nace el proyectil.

Separé esa conclusión en `tools/analyze_object_motion.py`. En una pasada enfocada a la llamada de creación de `0076f3b4` confirmé que el objeto `0x328`/808 usa `Player+0x158` como registro de offsets: `x = Player+0xec + signed(Player+0x104) * s32(record+0x98)` y `y = Player+0xf0 - s32(record+0x9c)`. El PE fija la fórmula y el objeto creado; aún no he localizado quién llena ese registro ni sus valores durante 418. El port conserva su trayectoria provisional.

El análisis confirmado del handler sigue en pie: `0076f3b4` tiene la ventana de ajuste de pose 5–17 y el gate separado de diez emisiones mediante contador impar 1–19. El mapeo de esa cronología a PAT sigue siendo inferido por el port, no una traza sincronizada del juego original.

## Verificación

- `tools/analyze_object_motion.py original/th123.exe` validó las nuevas firmas de la llamada y fórmula contra el PE SHA-256 esperado.
- Suite Python: 23/23 aprobadas; `git diff --check` sin errores (solo avisos de fin de línea en archivos preexistentes).
- No se modificó ni reconstruyó el VPK en esta iteración; el cambio corrige el alcance de la evidencia y evita consolidar una posición de spawn sin verificar.

## Siguiente paso

Rastrear el productor del registro `Player+0x158` y obtener los dos valores que usa la acción. Después integrar las coordenadas y cotejar spawn, trayectoria y colisión en Vita3K.
