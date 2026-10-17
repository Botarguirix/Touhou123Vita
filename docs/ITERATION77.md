# Iteración 1.77: retoma, auditoría TH75 y baseline compilado

## Revisión de Touhou75Vita

Se inspeccionó el hilo **Configurar Touhou75Vita** y su evaluación previa. El trabajo de ese chat probó un runtime semántico x86→C con un guest sintético (registros y una global prefijados); VitaSDK quedó sin validar por error HTTP 403 y no se produjo un VPK probado. TH75 sí aporta metodología: inventario y CFG acotado, cobertura cuantitativa, contratos ABI y diagnóstico de operaciones no soportadas. TH123 ya dispone de oráculos x86 específicos y un runner aislado, que son la evidencia de autoridad. No se copió código/offsets/recursos TH075.

## Regresión y artefactos

- Suite Python: 37/37 aprobada.
- Se regeneró `artifacts/x86-suwako-808-factory-probe.json` desde `original/th123.exe` (hash fijado) y los DAT locales. Constructor/lista, factory 808 y dispatcher terminaron en la dirección de retorno esperada. El factory retornó acción 808, seq.1, posición `(300,400)`, color `ffffffff`/alpha 255 y campo raw `+0x34c=1`. Heap, trigonometría, RNG, renderer, piso y colisión son servicios controlados; no es una ejecución nativa de combate.
- Se compiló desde fuentes actuales `artifacts/Touhou123Vita-TH75-review-current.vpk` (95,972 bytes; SHA-256 `c360c89d923e554bcff0cccf7c7ecb94164d3825f84958bcf7314e30daae9129`). Vita3K SDL aislado, schema28, 600 frames: `status=passed`; PAT/assets/cartas 20/20, BG34 con 30+30 tiles, cuatro assets estáticos y 30 objetos; dashes y hits A/B/C; rutas de skill 560, 540, 565 y 505; 148 texturas, máscara de fallos de textura en cero.

## Límite y siguiente gate

El harness invoca manager/list constructor antes del factory, pero no ejecuta todavía el loop de manager sobre la colección. El próximo paso es resolver una inicialización real controlada del objeto manager, instrumentar su iteración/virtuales y encontrar el consumidor de `object+0x34c`. Con ese loop probar si cero retira/reutiliza el objeto; luego seguir límites y colisión/impacto, especialmente seq.1 sin cajas PAT declaradas. Solo después se integra el resultado en Vita y se extiende la gate. El VPK de esta iteración es baseline de regresión y no valida el ataque 808.
