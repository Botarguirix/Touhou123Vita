# Iteración 2.132: timing y reacción del burst Suika 623B

Se cotejó la ventana de vida del PAT 821 de la acción 530 con el flujo x86 ya instrumentado. El objeto se resuelve una sola vez en el cuadro de creación y `life=1` lo retira al siguiente update, antes de otro chequeo de colisión. La respuesta aterrizada conserva la acción 50 y el timer de 20 frames observado por el resolver, en lugar de reiniciar el estado con el helper genérico de acciones.

La prueba integrada usa a Suika como atacante y un defensor en tierra colocado en la zona de spawn. Ahora exige una sola conexión de 800, acción de reacción 50/timer 20 al impacto, objeto inactivo en el update siguiente y HP/hits sin cambios adicionales. Vita3K SDL pasó schema46/600 frames y la máscara Suika 623B aumentó de 63 a 127 para exigir este contrato junto a las rutas previas. También pasaron los gates existentes de Suika 623C, objetos, sprites y BG33/36/37/38.

Artefactos generados con VitaSDK 2026.08:

- Autotest: [Touhou123Vita-suika623b-burst-fidelity.vpk](../artifacts/Touhou123Vita-suika623b-burst-fidelity.vpk), SHA-256 `5812B15F9B7EBD889CB3B403863887CEFE799BC4DE90C5231DFC9C7FB9A8D71D`.
- Interactivo: [Touhou123Vita-suika623b-burst-fidelity-interactive.vpk](../artifacts/Touhou123Vita-suika623b-burst-fidelity-interactive.vpk), SHA-256 `BA448F651311D27E333647746CF1DE1F4145B9ACEE30F7ABE63FE6CF36AFEDE4`.
- Ambos incluyen el mismo `eboot.bin`, SHA-256 `A73266F7FD99CA01203635558D3FCCEDB015533046EAF9949D200B3E3CD78E04`.
- Reporte fresco: [vita3k-result.json](../artifacts/vita3k-result.json), `status=passed`, schema 46, 600 frames, route mask 127.

El fixture prueba el timing del motor con colocación controlada; aún falta comprobarlo en una partida con movimiento natural y alinear el RNG global compartido del original. WSL no pudo arrancar por `E_ACCESSDENIED`, y Windows no tiene libc/toolchain host para recompilar `fight_tests`; el código ARM sí compiló con warnings como errores mediante `build-vita-native.ps1` y se ejecutó bajo Vita3K. No es evidencia de paridad completa, todos los personajes/escenarios ni hardware físico.
