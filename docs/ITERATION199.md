# Iteración 2.99: revalidación del lector x86 con todo el replay Sanae

Se ejecutó con Unicorn el método original `0x481040` del PE 2009 sobre cada valor almacenado en `090815_2219_sanae_story.rep`. Los hashes se validaron antes de cargar: PE `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`; replay `6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e`.

| Registro | Words ejecutados | Words con bit `0x2000` o `0x4000` |
|---:|---:|---:|
| 0 | 8,720 | 34 |
| 1 | 6,932 | 175 |
| 2 | 18,168 | 320 |
| **Total** | **33,820** | **529** |

En cada word, el probe comprobó que el método lee el índice solicitado, conserva el valor de input, llama al setter con los estados esperados para IDs `0x3c/0x3d`, e incrementa el índice en uno. También verificó la guarda al final del vector: el lector de palabra vuelve al índice 0 y el cursor queda en 1. Todas las verificaciones pasaron para todos los words. Esto valida la semántica por invocación con los datos reales del replay y fortalece el contrato del cursor C de Iteración 2.66.

La inspección estática del dispatcher confirma que los métodos `0x47ee10` y `0x481040` llaman al decoder en modo replay y están conectados en slots virtuales distintos; `0x4600fe` hace peek/espera/comparación con el input global y consume después de igualdad. Aun así, la probe ejecuta una sola rutina con getters/decoder/reader/setter interceptados: no ejecuta el loop completo del combate y no establece cuántas invocaciones ocurren por frame renderizado, cómo se alternan los dos canales en juego natural, ni la sincronía entre jugador y reloj.

Evidencia local ignorada por Git: [`replay-update-method-all-words-original-2009.json`](../artifacts/kernel/replay-update-method-all-words-original-2009.json), [`replay-dispatch-original-2009.json`](../artifacts/kernel/replay-dispatch-original-2009.json). Reproducir desde la raíz del repo:

```powershell
python -m tools.x86_replay_update_method_probe `
  'F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\replay\story\090815_2219_sanae_story.rep' `
  --exe 'F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe' `
  --all-words --output artifacts/kernel/replay-update-method-all-words-original-2009.json
python -m tools.x86_replay_dispatch_probe `
  --exe 'F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\th123.exe' `
  --output artifacts/kernel/replay-dispatch-original-2009.json
```

No cambió el runtime ni el VPK. Un barrido lineal Capstone del código ejecutable del PE no encontró referencias absolutas a las tres direcciones de slots virtuales; ese resultado no excluye inicialización por offsets/constructores ni indirect calls y no identifica sus callers. Próximo: usar el replay compatible con el PE 2009 en PC, con ReplayInputView+/LabTool y frame-step, y capturar cursor, input, jugador y frame en 10–30 ticks. El intento de inspeccionar esta sesión mediante la automatización de UI local no pudo iniciar porque Windows no encontró los kernel assets requeridos. Una vez que tengamos la traza, resolver el gate `0x4600fe` y conectar el cursor al loop de combate Vita con cadence observada.
