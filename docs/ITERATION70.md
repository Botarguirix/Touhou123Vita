# Iteración 1.70: secuencia 808 obtenida desde customData

El análisis anterior de las rutas de objeto (Iteración 1.30, documento `ITERATION34.md`) ya había establecido que el initializer de Suwako toma `customData[2]` como índice de secuencia mediante `setSequence`. Los hijos del split llevan `[ángulo, magnitud, 1]`; el oracle ya deriva el selector de ese tercer float en vez de inferirlo de `arg4`, que es un argumento separado de `createObject`.

La ejecución del initializer original `0x799000` confirma con Unicorn que ambos custom data seleccionan `+0x13e = 1` y aplican la transformación radial. Se regeneró `artifacts/x86-suwako-808-child-trajectories.json` (24 callbacks por hijo) con el cadence del handler. Los finales controlados son `(-20°,12): (287.6873,428.4290)` y `(-30°,14): (279,430.9731)`.

La prueba no ejecuta el factory/manager virtual real. El incremento del subframe entre callbacks se inyecta como reloj externo porque el handler mismo solo compara/resta 8; debe confirmarse en el loop de objetos del PE o una traza PC. Suelo, RNG, colisión y helper seno también se controlan. No se cuentan estas posiciones como resultado end-to-end natural.

Pruebas: `tests/test_suwako_808_object_oracle.py` 7/7; suite Python completa en la validación final. Sin cambio del runtime Vita ni nuevo VPK.
