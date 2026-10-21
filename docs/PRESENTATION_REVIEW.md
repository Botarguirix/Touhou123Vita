# Revisión de presentación frente al original

Prioridad solicitada: posición de personajes y composición de escenarios. La presentación no se considera validada por el gate de combate.

## Evidencia disponible

- Se inspeccionó `artifacts/screenshots/fight-bg36.bmp`: muestra personajes separados de sus sombras y una composición dominada por el reloj. Es un frame de diagnóstico; no permite concluir por sí solo que el anclaje de reposo sea incorrecto, porque no registra aquí las poses y alturas de ambos jugadores.
- El reset común ejecutado del PE de referencia coloca los jugadores en (480,0) y (800,0), mirando hacia el centro; cámara (640,0), zoom 1. La proyección del port sitúa sus orígenes en (160,420) y (480,420), antes de los offsets PAT. Esto es evidencia de código ejecutado, no comparación visual del combate PC.
- El dibujo de sprites usa offsets PAT y cámara. Las sombras actuales son círculos de diagnóstico con desplazamiento vertical fijo de −22; su forma y posición no están contrastadas con el original. No deben usarse para calibrar el suelo.
- BG36 carga 25 tiles y cuatro auxiliares, pero su composición completa aún no tiene referencia visual equivalente. Contar texturas y draws no valida escala, perspectiva ni parallax.
- Se volvió a abrir la copia Ver1.01 del usuario desde F: mediante Computer Use. La captura devolvió `FrameArrived timed out`. No se observó gameplay original. Esta versión tampoco es el PE fijado que usan las sondas x86; mantener identificadas ambas versiones.
- El replay Sanae disponible recorre BG30/BG12/BG33. La asociación local de BG36 es `data/scenario/meirin/002.txt`, Meiling contra Marisa. No comparar esos fondos como si fueran el mismo escenario.

## Orden de trabajo

1. Capturar PC y Vita en el mismo escenario, personajes y estado de reposo, sin inputs. Registrar versión, frame, posiciones, pose y cámara cuando estén disponibles; conservar originales sin escalar.
2. Comparar sobre lienzo 640×480 el origen de cada personaje, su tamaño y el punto de apoyo. Aplicar offsets del PAT; no corregir cada personaje con desplazamientos arbitrarios.
3. Comparar suelo, horizonte y al menos tres puntos reconocibles del fondo. Separar errores de cámara de errores de origen/escala de cada capa. Revisar primero BG33, que tiene referencia posible en el replay disponible, y después BG36.
4. Repetir con acercamiento, separación hasta las paredes y salto. Verificar zoom, seguimiento vertical y parallax antes de dar por cerrado un escenario.
5. Sustituir sombras y HUD de diagnóstico con recursos/comportamiento comprobados. Repetir las capturas con la presentación normal y dejar el diagnóstico opcional.

## Criterios de cierre

Guardar pares de capturas comparables y una tabla de coordenadas/diferencias; señalar explícitamente los estados todavía sin referencia. Una corrida Vita3K o una prueba numérica aislada no cierra la paridad visual. No se fija todavía una tolerancia de píxeles sin comprobar filtrado y versión de referencia.

No se modificaron offsets de render ni se generó un nuevo VPK en esta revisión: todavía falta la referencia visual que justifique esos ajustes.
