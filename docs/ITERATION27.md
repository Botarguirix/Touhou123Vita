# Iteración 1.23: productor de input respaldado por el PE

## Resultado

Se completa el mapeo estático del word de entrada que construye `0046d5d0` (ejecutable 1.10a con SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`). Los ejes de dirección ocupan el nibble bajo, A/B/C/D los bits 4–7 y change-card/spellcard los bits 8–9. `fight.c` empaqueta la abstracción de controles de Vita en el mismo formato.

El probe automático ahora comprueba `0x019` (izquierda, abajo, A) y `0x3e6` (derecha, arriba, B, C, D, change-card, spellcard) antes de sus pruebas de dash. Esto prueba el puente de controles de la demo y el historial del combate, no la adquisición de bindings PC.

## Revisión del proyecto Touhou75Vita

Se leyó el chat **Configurar Touhou75Vita** y su registro de trabajo. Su runtime semántico mínimo pasó una prueba smoke en Linux, pero el VPK de aquel repositorio solo inspecciona cabeceras PE; la compilación VitaSDK no quedó validada en aquel entorno debido a una respuesta HTTP 403 del proxy. Su pipeline de funciones, CFG/reachability, cobertura de opcodes, manifiesto por hash y pruebas fail-loud sirven como método para el análisis futuro de Touhou 12.3. No se incorporó código del repositorio.

## Validación

- `tools/test_input_arm_oracle.py`: 401/401 vectores x86/ARM aprobados.
- Build con VitaSDK: completado; VPK [Touhou123Vita-input-producer.vpk](../artifacts/Touhou123Vita-input-producer.vpk), SHA-256 `a808bc56cc95b9e2e61a6dc477275edd9c3ca195871d2c9eeffd14828d57ddfc`.
- Vita3K aislado: `status=passed`, 600 frames, `dash_gate_probe=1`, tres dashes, B/C=1/1, 31 DAT, 137 texturas, roster/cards/PAT 20/20, 30+30 tiles y 4+30 recursos del escenario BG34. Reporte: `artifacts/vita3k-result.json`.

Las instrucciones fuente y los límites de la inferencia están registrados en [INPUT_STATE.md](INPUT_STATE.md). Esto valida el empaque de la abstracción actual de Vita y el smoke de combate; faltan el polling/bindings configurados PC y sus replays.
