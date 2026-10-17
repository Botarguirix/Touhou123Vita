# Iteración 1.44: primera skill de Reimu jugable y contrastada en Vita3K

## Ruta implementada

Se conectó la entrada `IN_SPELLCARD` a una primera ruta explícita: personaje Reimu (índice 0), carta de prueba 103, acción PAT 560. La acción 560 tiene una variante de arranque (índice 0) sin daño y una variante ofensiva (índice 1) que el inventario PAT define con 1200 de daño y dos cajas. El selector de ataques ahora elige la variante con cobertura ofensiva disponible para acciones 500–599; no inventa cajas ni daño y deja las acciones sin cajas en su variante 0.

En controles reales de Vita, `L + Circle` activa esta ruta experimental. La carta 103 se asigna como slot fijo al perfil de Reimu para el prototipo; todavía no existe mano seleccionable, costo, descarte, mejora, cancelación por flags, ejecución aérea, ni los objetos de otras skills. El byte `Player+0x836` y los gates del handler original siguen sin portarse. Esta interfaz es una sonda jugable, no una implementación general del sistema de cartas.

## Evidencia

El build VitaSDK produjo `artifacts/Touhou123Vita-skill-probe.vpk` (SHA-256 `85fa80fd88f7df8f3addc067d6e5eb413e3139750b28588382658ee78ffcdecf`). El runner lo ejecutó en Vita3K SDL sobre el VitaFS local con **schema 20**, 600 frames y estado `passed`. La traza guest registra `skill_action=560`, `skill_image=81` (pose PAT ofensiva) y `skill_hit_delta=1`: el golpe conectó y aplicó el daño/caja PAT a un rival colocado por el probe a partir de sus hitboxes/hurtboxes. Después se restauró Marisa para mantener la regresión existente de B/C. El mismo reporte conserva 20/20 recursos de personaje, BG34, 35 impactos de dash directos, objetos y el resto de contratos de combate.

La build interactiva para probar manualmente es `artifacts/Touhou123Vita-skill-demo.vpk` (SHA-256 `2a9b7967d2ad0c1b022f695deb84e527a531e15b8d8275e0de467ea325647a52`). Selecciona Reimu y en combate pulsa `L + Circle` para la carta/skill experimental. La entrada comparte `L` con el toggle de CPU, que se suprime mientras se mantiene la combinación.

El contrato C de `tests/fight_tests.c` también cubre la entrada y el golpe sobre un fixture controlado, aunque en este entorno no se pudo ejecutar CTest host: `cmake` no está disponible y WSL devuelve `E_ACCESSDENIED`. Sí se completaron el build cruzado VitaSDK y la corrida funcional del VPK en Vita3K.

## Siguiente paso

Portar la mano/costo/consumo y los gates de activación de `handleInputs`, comparar los frames de la skill 560 con una captura x86/replay PC y probar el control de la build interactiva. Después recuperar los objetos para las skills restantes de Reimu, incluyendo la primera carta 100/acción 500, y extender personaje por personaje.
