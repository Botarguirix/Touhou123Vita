# Iteración 2.08: dispatch y temporizador de Remilia 412 → objeto 801

Se añade y amplía `tools/x86_remilia_412_spawn_probe.py`. En el PE fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`, la probe ejecuta el setter/initializer original `0x464930 → 0x438ca0 → 0x465370 → 0x59aaa0 → 0x59ad64 → 0x4636b0`; el setter de pose original `0x464b50` llama `0x464ae0` y carga duración 4 para cada pose del fixture PAT seq.0.

En cada tick del action dispatch se ejecuta `0x438c60`: incrementa `+0x142`, compara con duración activa `+0x14c` y, al agotarla, usa el slot 8 de Remilia para llamar a `0x464b70`, que avanza pose y vuelve a cargar el siguiente frame. Los estados medidos fueron pose0/subframe1..3, pose1/subframe0..3, pose2/subframe0..3, pose3/subframe0..3 y pose4/subframe0. El handler `0x58cce7` solicita ID 801 al llegar a pose4 en el tick 16, sin forzar el campo de pose.

El flujo probado empieza en la comparación `0x587bab`, sigue por `0x58a3a1 → 0x58cce7`, ejecuta los helpers `0x47a9e0`, `0x487870`/`0x820230` y el lookup `0x464980`. Para `(x,y)=(320,180)`, el spawn fue `(403,360)` con facing `+1` y `(237,360)` con facing `-1`; medidor 1000→800, gauge 0→50 y bloque temporal `[-70,12,0]`.

Límites: el prólogo completo `0x5879a0` y gates anteriores se omiten; EBX=1 se siembra según el valor de `0x5879cf`. Los frames PAT se representan con su duración, no con todos sus descriptores. La consulta `0x487ca0`, tabla de callback, manager/handle y dispatcher externo `0x401d50` son fixtures. La prueba no ejecuta la función callback real, factory/update/colisión de 801 ni el daño de combate.

Validación: las dos orientaciones producen la secuencia esperada y la suite Python pasa 40/40. Sin cambio de runtime Vita ni VPK. Reportes `artifacts/` ignorados; probe, test y documentos se versionan.
