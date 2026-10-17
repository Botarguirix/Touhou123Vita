# Iteración 2.05: imports del CRT y límite del fixture para Remilia 801

El harness ahora proporciona contratos x86 controlados para los imports Windows que se observaron en la ruta 801: `TlsGetValue`, `GetModuleHandleA`, `GetProcAddress`, `DecodePointer`, `GetLastError`, `SetLastError`, `GetCurrentThreadId`, `IsDebuggerPresent`, `SetUnhandledExceptionFilter`, `UnhandledExceptionFilter`, `TlsAlloc`, `TlsSetValue` e `InterlockedIncrement`. El módulo KERNEL32 sintético expone una sección `.text` sin `.mixcrt`; las resoluciones del loader no sustituyen el dispatcher ni el update del juego. Se registran las llamadas para auditar el entorno simulado.

Con esas importaciones, la ejecución atraviesa la llamada anterior a `TlsGetValue`; después el CRT crea una excepción con código `0xc000000d` y llama `KERNEL32!TerminateProcess` con pseudo-handle `0xffffffff`. Se retiró el stub experimental de `0x47dcb0`: recibía `ECX=2`, no un objeto/lista, así que aquel camino era parte del manejo de error y no una limpieza de contenedor del juego. La actualización no supera el tick 4, por lo que no se puede afirmar ciclo de vida o daño.

La regresión del factory Suwako 808 aún crea el objeto y completa ocho updates. `py_compile` pasa. El reporte de Remilia 801 está en `artifacts/kernel/remilia-object801-factory.json` (ignorado), con import calls, traza y solicitud de terminación. `pytest` no está disponible en el Python local.

Siguiente: identificar qué estado incompleto hace que la capa CRT lance `0xc000000d` bajo este fixture, completar la inicialización compatible sin omitir lógica del personaje, y volver a correr seq.1/0; después alimentar el setup exacto emitido por Remilia 412 y comprobar contactos/daño. No cambia el runtime Vita ni el VPK.
