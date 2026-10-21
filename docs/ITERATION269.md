# Iteración 2.169: timer action96 cruza el HUD con shim y avanza 1.200 ticks

La global `0x8985e8` corresponde a `SokuLib::v2::InfoManagerBase::instance` (`local/SokuLib/src/InfoManager.hpp`). El PE la crea en el inicializador `0x439680` (asignación de `0x688` bytes y constructor `0x47eaf0`); la vtable de InfoManager en `0x85b530` tiene slot `+0x18 = 0x47eb70`. Ese método calcula un HUD de jugador y entra a `0x47ed40`, que lee gauges/diseños. El harness no inicializa la UI original.

Se añadió un objeto de prueba de 0x688 bytes con la vtable original copiada y un shim únicamente para slot `+0x18`, que conserva el `ret 0xC` y registra los argumentos del refresco HUD. El primer intento usó por error `STOP+0x300`, ya ocupado por el stub de altura del escenario, y produjo un falso desbalance de pila; se movió a `STOP+0x500` y se confirmó el retorno al sentinel correcto. Tras la corrección, el timer y el updater originales ejecutan 1.200 ticks de action96 sin fetch inválido. Action permanece 96 (secuencia reportada 41); `Player+0x884` no recibe escrituras y termina en cero. El HUD shim recibe tres actualizaciones: `(kind=2, player=1, timer=0..2)`.

Esta corrida aún fuerza la entrada a action96 y sustituye su actualización de HUD; no prueba la transición natural del round ni reproduce la interfaz. El timer de juego, handler, PAT/fotogramas, input neutral y updater siguen siendo del PE original. Runtime Vita/VPK sin cambios.

El barrido de referencias existentes revela dos consumidores más del campo: `0x5100b0` en Alice (slot 10 de vtable `0x85c9f4`) y `0x765ab0` en Suwako (slot 10 de `0x85f2bc`). Ambos revisan/decrementan `+0x884` y lo limpian al llegar a 1; ninguno aparece como productor positivo. Junto con Suika `0x48b15a`, que solo lo limpia, esto sitúa la semántica en la familia de update de personaje pero deja el productor fuera de las referencias directas conocidas.

## Siguiente

Encontrar quién inicializa/cambia `Player+0x884` positivamente y qué estado de round dispara action96 de forma natural. Extender el rastreo a constructores/manager compartidos y escrituras calculadas, no solo vtables de Suika. Mantener aislado el callback de HUD mientras se reconstruye el ciclo de manager; cuando la ruta esté identificada, intentar inicializar InfoManager real con recursos/controladores requeridos y cotejar la transición contra replay.
