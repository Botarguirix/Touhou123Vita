# Iteración 2.87: actualización completa por tick de cámara

Se añadió `T123StageCamera` para guardar los targets X/Y/zoom y el estado actual, junto con `t123_stage_camera_step`. Cada llamada calcula el target de dos jugadores, calcula target Y con el zoom actual y después aplica zoom, X y Y en ese orden, usando los helpers contrastados individualmente con `FUN_00428E20` y `FUN_00429040`.

El contrato C y el gate Vita comparan el paso siguiente al constructor del PE para la pareja `(200,0)` y `(900,-500)`: se conserva X=550, zoom=0.59145278 y Y pasa de −76.820335 a aproximadamente −72.893845. Python completo: 109/109. VitaSDK compiló el VPK y Vita3K SDL pasó 600 frames, schema46, `regression_gate=1` y `stage_camera_pair_contract=1`.

VPK auto-test: `artifacts/Touhou123Vita-camera-state-auto.vpk`, SHA-256 `590ae74f9bad57f761e4a00630168bc9490f9fe89a2088fa00eefca51602063c`. VPK interactivo: `artifacts/Touhou123Vita-camera-state.vpk`, SHA-256 `78f75bbf5fe38b145aee00202c3cc0aa3fcb1793f57cb09e0dd3d67774535720`.

Este paso consolida las fórmulas en una actualización reutilizable, pero el estado aún no está integrado a `Fight` ni al renderer. El jugador simplificado vive en coordenadas X 35–605 y altura positiva desde el piso; el renderer/escenario original usa otro marco y offsets. La relación no se puede afirmar por semejanza visual: hay que medirla con posiciones/capturas del PE. Siguiente tarea: recuperar esa conversión y validar proyección de luchadores y escenario como un conjunto antes de conectar la cámara dinámica.
