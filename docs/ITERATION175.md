# Iteración 2.75: mapeo de slots de render BG36–BG38

Se corrigió la interpretación de los offsets de la iteración 2.74 cotejando el orden de carga de los constructores con las instrucciones de los renderers del PE `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. Los cálculos de velocidad/wrap eran correctos; algunos nombres de recursos no.

- BG36: `+0x68` mueve el auxiliar slot 0 (`tori1`) en y=−750; `+0x6c` mueve slot 1 (`tori2`) en y=−320. Las otras dos nubes cargadas siguen pendientes de mapear en su renderer.
- BG37: slot 0 `tori1` usa `+0x68`, y=−750; slot 1 `clowd_l` usa `+0x6c`, y=−320; slot 2 `clowd_s` se dibuja en x=492, y=−401 sin esos offsets.
- BG38: slot 0 `clowd_l` usa `+0x68`, y=−750; slot 1 `clowd_s` usa `+0x6c`, y=−320.

Se actualizaron los tipos C, el visor diagnóstico y los contratos automatizados del renderer para reflejar los slots y transforms verificados. VitaSDK generó el VPK interactivo (93.343 bytes, SHA-256 `9ac402f13f5858d18653d5f28d2ecff933f914d47061a5f4cea0809c4fd141bf`) y el automático (93.555 bytes, SHA-256 `82d2b32c4aceef8bfd472de76021f4a2d3dbffccb03d7a32b361616f212e450c`). Vita3K SDL pasó schema46/regresión de 600 cuadros; el gate capturó BG37/BG38 y observó −403/−302 tras 2 updates y −406/−304 tras 4. La suite Python completa pasó 100/100.

Capturas de las páginas de diagnóstico: [BG36](../artifacts/screenshots/stage-bg36-layout.bmp), [BG37](../artifacts/screenshots/stage-bg37-scroll.bmp), [BG38](../artifacts/screenshots/stage-bg38-scroll.bmp). Estas páginas muestran recursos y transforms locales en filas, no reproducen cámara, alpha, parallax ni el renderer integrado al combate; BG36 aún no modela las pasadas de nubes restantes. El replay/mecánicas de escenarios completos siguen pendientes.
