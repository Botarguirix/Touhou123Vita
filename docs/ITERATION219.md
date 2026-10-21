# Iteración 2.119: decoder Story enlazado al contador por invocación

Se cerró estáticamente el tramo interno de una llamada al slot 5 del manager Story usando el ejecutable original de 2009, fijado por SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`.

La secuencia es:

1. El slot 5 apunta a `0x47f810` y llama al slot 16 en `0x47f82e`; el slot 16 Story (`0x47ee10`) consulta el estado y llega al decoder `0x42a410`.
2. Después, `0x47f810` llama al helper `0x478640` en `0x47f84e`.
3. El helper despacha el slot 15 (`+0x3c`) en `0x478648`. En el vtable Story el destino es `0x47f7c0`, que reinicia `[0x85d74c]` y salta a `0x4787f0`.
4. `0x4787f0` invoca un método desde `[0x85eb70]` y luego incrementa `[0x85eb58]` en `0x478851`.

Esto prueba que cada ejecución de `0x47f810` alcanza el decoder y luego una vez el incremento de `[0x85eb58]`. El objeto `[0x85eb70]` es distinto del manager Story `[0x85eb64]`, por lo que su método no se etiqueta como callback del manager. Tampoco se conoce todavía cuántas veces se ejecuta el slot 5 por tick de simulación o cuadro renderizado; la cadencia exige hallar el caller externo y obtener playback frame-stepped.

El probe SHA-pinned `tools/x86_replay_manager_selection_probe.py` ahora valida esta cadena. `python -m unittest tests.test_replay_manager_selection_probe` pasa (1/1); el reporte contiene 53 condiciones verificadas en `artifacts/kernel/replay-manager-selection-original-2009.json`. No hubo cambios al runtime Vita ni a los VPK en esta iteración.

## Siguiente paso

Identificar el caller externo de `0x47f810` y correlacionar cursor del replay, `[0x85eb58]`, tick de simulación y render mediante una sesión frame-stepped. Hasta entonces, el resultado es por invocación, no por cuadro.
