# Iteración 2.93: test de recorte desplazado dentro del guest

La base PAT local se auditó en los veinte personajes de `th123c.dat`: se analizaron 17,586 secuencias. Ocho frames presentan `tx/ty` no cero; siete usan `alpha000.bmp` y uno `attackAa000.bmp` (hallazgo clasificado en [ITERATION194.md](ITERATION194.md)). Los demás frames examinados tienen origen de recorte cero y dimensiones positivas. El rasterizador sintético valida recortes desplazados, pero aún no interpreta esos frames reales.

Para probar de todos modos el código real del rasterizador ante un origen desplazado, `soft2d_texture_region_crop_contract()` crea en runtime una textura sintética 4×4 con un valor distinto por píxel, dibuja el recorte `[1,3)×[1,3)` y verifica sus cuatro colores, además de los bordes externos. El auto-VPK ejecuta este contrato al inicio y el gate falla si `sprite_region_crop_contract` no vale 1. Esta prueba comprueba Soft2D y se combina con el oracle PE de la iteración 2.92, que establece el cálculo PAT `(tx,ty,tw,th) → (tx,ty,tx+tw,ty+th)`; no sustituye una fixture visual basada en DAT ni la comparación contra el juego de PC.

Validación:

- `python -m unittest discover -s tests -p 'test_*.py'`: 110/110.
- VitaSDK compiló el VPK interactivo y el automático.
- Vita3K SDL aislado: schema46, 600 frames, `status=passed`, `sprite_region_crop_contract=1`, `regression_gate=1` y contratos de cámara/BG33/BG36–BG38 aprobados.
- El interactivo y el auto-VPK comparten `eboot.bin`, SHA-256 `d1d730c7849097d8b78a09e75ccc708b2668a9b39cf1e716c9a39abd2879fdf5`.

Artefactos:

- Interactivo: [`Touhou123Vita-pat-crop-guest.vpk`](../artifacts/Touhou123Vita-pat-crop-guest.vpk), SHA-256 `c511fb78937fe3b12a2b686220f860420ab3729ad784c96e242730a05601b46d`.
- Auto-test probado: [`Touhou123Vita-pat-crop-guest-auto.vpk`](../artifacts/Touhou123Vita-pat-crop-guest-auto.vpk), SHA-256 `96e1782e6bdf7c5dd6a5e627d8b2b52fd1ac4e415136fc603b772815bdab6b71`.
- Reporte del guest: [`vita3k-result.json`](../artifacts/vita3k-result.json); catálogo de quad x86: [`sprite-component-contract.json`](../artifacts/kernel/sprite-component-contract.json).

La captura de pelea permanece orientativa; el auto-overlay tapa parte del escenario y no existe una corrida del juego original sincronizada con este build. VitaFS local conserva los DAT montados y evidencia bajo `artifacts/vitafs`; el VPK no incorpora recursos comerciales. Quedan pendientes las rutas de efectos alpha, la calibración visual con referencia, un combate integral y la cobertura total de personajes/escenarios.
