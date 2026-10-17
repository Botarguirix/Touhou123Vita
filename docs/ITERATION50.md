# Iteración 1.46: regresión fresca y contrato de loop PAT

## Verificación

Se recompiló el probe automático desde el checkout actual con VitaSDK y se ejecutó en la instalación aislada de Vita3K usando `G:\Vita3k\Vita3K.exe`. La corrida terminó en 600 frames, schema 21, `status=passed`. Conservó roster/PAT/tarjetas 20/20, 31 DAT externos, BG34 (30+30 tiles, 4 recursos estáticos y 30 sprites de objetos), 35 impactos de dash, objetos, B/C y la comprobación de la secuencia inicial de la skill 560. La suite Python pasó 16/16.

VPK automático actualizado: `artifacts/Touhou123Vita-skill-sequence-probe.vpk`, SHA-256 `84983f9df10577f70889d0326a49f2b4b899afc24158d9e40e142c584b0ad37e`. El reporte fresco está en `artifacts/vita3k-result.json` y asocia esa huella con la corrida. Este probe confirma el startup y el primer impacto, no la terminación de la skill ni su paridad integral.

## Loop y salida de Reimu 560

La inspección de las funciones originales 1.10a (`00464b70`, `00464bf0`, `00438c60`) confirma que al terminar una pose, `nextPose` solo solicita avanzar de secuencia si el flag loop de la secuencia actual es cero. `nextSequence` sigue el puntero al siguiente registro y vuelve a evaluar la nueva secuencia. En el PAT de Reimu 560, seq. 0 y 1 no tienen loop, seq. 2 sí, y seq. 3 no. Por ello seq. 0 → 1 ocurre por tiempo; seq. 2 permanece activa y seq. 3 requiere una transición externa. No se debe hacer que todas las variantes con loop avancen por tiempo: eso contradice el contrato x86.

La salida/cancelación de la secuencia 2 sigue pendiente. El dispatch estático de cartas prueba que existen rutas a `useSkill`, pero no demuestra cuál input, gate o callback lleva la acción 560 a seq. 3. El siguiente trabajo debe ejecutar la ruta dinámica del handler de Reimu con estado/input controlados o capturar una traza PC y localizar la escritura que cambia la secuencia actual. La actualización de esta iteración no cambia semántica del runtime; retira la hipótesis de avance automático y deja un VPK/regresión frescos.

La compilación host/CTest no se repitió porque esta sesión no tiene CMake ni compilador host; WSL informa `E_ACCESSDENIED`. La build VitaSDK y Vita3K sí se ejecutaron y pasaron.
