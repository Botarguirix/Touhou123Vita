# Estado del proyecto

Fecha de esta evaluación: 2026-10-13 (America/Mexico_City).

## Verificado

- Inventario local generado con SHA256 y metadatos PE.
- Ejecutable aportado: 4,816,896 bytes, SHA256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.
- Ghidra identifica `x86:LE:32:default`; importaciones incluyen Direct3D 9, D3DX9, WinMM y Winsock.
- Se exportaron 30 funciones iniciales a pseudocódigo local. La primera coincide en dirección con la referencia de comienzo de render de SokuLib; el comportamiento requiere análisis adicional.
- El análisis automático alcanzó el límite de 600 segundos. El post-script, guardado e importación finalizaron correctamente; no se da por terminado el análisis del motor.
- Extracción de `th123a.dat`, conversión local de sprites/paletas y recursos de escenario.
- Pruebas host `core_contract`, `fight_contract` y `tools_contract`: 3/3 aprobadas.
- Compilación ARM/SELF/VPK del prototipo interactivo y de la variante automática completada.

## En validación

- Escenario automático de 600 frames dentro de Vita3K.
- Controles manuales, lectura visual del menú y pelea. El control de computadora se detuvo mediante Escape; no se afirma una verificación visual del prototipo.
- Repositorio remoto: la primera publicación fue bloqueada por la revisión automática del payload. Se cambió a una lista explícita de código/documentación; publicación pendiente de verificación.

## Pendiente del port original

Ninguna parte del combate original ha sido reconstruida y validada contra PC. El núcleo jugable actual es un prototipo propio. No están implementados los movimientos reales, decks, clima, animaciones originales, sonido, historia, netplay ni paridad de replays. PS Vita física no probada.

Los resultados locales completos están bajo `artifacts/`; no se publican recursos comerciales ni pseudocódigo bruto.
