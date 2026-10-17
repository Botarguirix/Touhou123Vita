# Iteración 2.05: imports del CRT y límite del fixture para Remilia 801

El harness ahora proporciona contratos x86 controlados para los imports Windows que se observaron en la ruta 801: `TlsGetValue`, `GetModuleHandleA`, `GetProcAddress`, `DecodePointer`, `GetLastError`, `SetLastError`, `GetCurrentThreadId`, `IsDebuggerPresent`, `SetUnhandledExceptionFilter`, `UnhandledExceptionFilter`, `TlsAlloc`, `TlsSetValue` e `InterlockedIncrement`. El módulo KERNEL32 sintético expone una sección `.text` sin `.mixcrt`; las resoluciones del loader no sustituyen el dispatcher ni el update del juego. Se registran las llamadas para auditar el entorno simulado.

Con esas importaciones, la ejecución ya atraviesa el punto anterior de `TlsGetValue` y alcanza el constructor/update auxiliar asociado al objeto 801. El harness omite la limpieza de una lista recién asignada en `0x47dcb0`, pues sus vtables están nulas; después la rutina original itera/destruye otra lista desde `0x439950` y el fixture cae en una recursión hasta escritura fuera de memoria. Esto muestra que aún faltan contratos/constructores de contenedores en el objeto de prueba. No se puede atribuir esa falla al combate 801 ni afirmar ciclo de vida o daño.

La regresión del factory Suwako 808 aún crea el objeto y completa ocho updates. `py_compile` pasa. El reporte de Remilia 801 está en `artifacts/kernel/remilia-object801-factory.json` (ignorado), con import calls, traza e invalid-memory address. `pytest` no está disponible en el Python local.

Siguiente: reconstruir el constructor/sentinela de los contenedores que consume el update de 801 y volver a correr el estado real de seq.1/0; después hay que alimentar el setup exacto emitido por Remilia 412 y comprobar los contactos/daño. No cambia el runtime Vita ni el VPK.
