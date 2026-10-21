# Iteración 2.95: ruta de dibujo para recortes PAT extremos

La sonda estática [`disassemble_pe_windows.py`](../tools/disassemble_pe_windows.py), fijada al PE `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`, confirmó la ruta común del sprite de jugador:

1. `0x466720` lee el descriptor PAT y llama a `0x406c60` con los campos del componente.
2. `0x406c60` inicializa el quad y delega el UV a `0x406d30`; con textura válida, el UV se calcula desde `tx/ty` y `tx+tw/ty+th` normalizados.
3. El render `0x4075d0` aplica el transform, liga la textura con `0x405190`, establece FVF y llama al método de dispositivo en `+0x14c` con primitive type 5, dos primitivas y stride `0x1c`.

El helper `0x4075d0` no tiene una rama que omita el draw por UV fuera de `[0,1]`, por `flags` o por tamaño PAT. Por tanto, si uno de estos descriptores llega al renderer, el PE envía el quad a Direct3D. La referencia importa `d3d9.dll` y crea el dispositivo con `Direct3DCreate9`; la documentación de D3D9 indica `WRAP` como valor predeterminado de ADDRESSU/V, que repite la textura para UV fuera del rango. Como el helper de sprite solo liga la textura y no cambia ADDRESSU/V localmente, la hipótesis más probable es que estos UV se repiten. No está demostrado que ninguna ruta global, efecto o bloque de estado modifique el sampler antes del draw; falta confirmar el estado efectivo/captura del original.

También se resolvieron los CV2 efectivos para los ocho registros y se inspeccionó la alpha de los bordes con la `palette000.pal` del personaje. Siete texturas tienen todos los píxeles del borde opacos; `sakuya/attackAa000.bmp` tiene el borde totalmente transparente. Esto no permite inferir wrap/clamp: es evidencia para comparar con el estado D3D global, no una razón para recortar o descartar en Vita.

El disassemblado repetible está en [`pat-crop-render-chain.tsv`](../artifacts/kernel/pat-crop-render-chain.tsv) y el constructor/normalizador en [`pat-component-constructor.tsv`](../artifacts/kernel/pat-component-constructor.tsv); ambos indican el hash del PE. No se cambió el runtime ni se generó un VPK porque la evidencia solo aclara el camino x86 y no determina aún la semántica de muestreo.

Pendiente inmediato: confirmar si una ruta global, efecto o bloque de estado cambia `ADDRESSU/ADDRESSV`; después reproducir uno de los frames concretos con una captura sincronizada del original y comparar el resultado con el rasterizador Vita. La hipótesis de WRAP se apoya en los defaults documentados por Microsoft ([enum de estados de sampler](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dsamplerstatetype), [direcciones de textura](https://learn.microsoft.com/en-us/windows/win32/direct3d9/texture-addressing-modes)), pero sigue pendiente de evidencia dinámica del juego.

**Seguimiento:** la Iteración 2.96 encontró la inicialización explícita de U/V a WRAP para samplers 0/1 y las rutas genéricas que pueden modificar U/V desde campos por objeto. El valor activo durante un frame extremo aún depende del orden de dibujo. Ver [ITERATION196.md](ITERATION196.md).
