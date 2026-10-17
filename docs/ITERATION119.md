# Iteración 2.19: primer intento de update original del defensor

Después de construir al defensor con el constructor base `0x46b7f0` y seleccionar acción 602 con el setter/initializer/selector originales, el harness ejecuta el dispatcher de personaje desde `0x587bab`. La prueba mantiene el estado del PAT neutral Remilia seq.0/pose0 (`frameFlags=0x3041`) y crea la relación de dueño `defender+0x170 → PLAYER`, igual a la relación usada después por la resolución de pares.

El update no completa ni avanza la pose. La ruta llega al CRT del PE y solicita `TerminateProcess` con `0xc000000d` (`STATUS_INVALID_PARAMETER`); el `EXCEPTION_RECORD` asociado señala `0x81ff7c`. El informe conserva este resultado para evitar interpretar el setup como un tick válido. La resolución de pares aún aplica 120 de daño (1000→880) en el mismo caso, pero cae después por el callback nulo de presentación.

Conclusión: el constructor base y el action setter bastan para alimentar la geometría/daño original, pero no para ejecutar el update común de un personaje. El harness carece de estado derivado/manager necesario o entra con un contrato ABI incompleto. Siguiente paso: rastrear el caller del invalid-parameter en el dispatcher desde el prologue original y recuperar el constructor derivado y sus campos, en lugar de inyectar más punteros sin evidencia. No cambia el runtime, el VPK ni la evidencia de Vita3K.

Verificación focalizada:

```powershell
& 'C:\Users\Andy PC\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_remilia_412_spawn_probe.py -q -k original_pair_dispatch_applies_pat_damage_on_real_vulnerable_pose
```

Resultado observado: `1 passed, 3 deselected`; Unicorn también imprime una excepción nativa de acceso a memoria al iniciar la prueba en Windows, por lo que no se considera una corrida limpia de la suite completa.
