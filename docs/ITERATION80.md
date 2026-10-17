# Iteración 1.80: bounds del GameObject y próximo gate 808

## Hallazgo de layout

El checkout local de SokuLib define para TH123 `GameObjectBase` con `BoxInfo` a `object+0x1b4`: puntero a `CharacterFrameData` en `+0x1c0`, conteo de hit en `+0x1cb` y de hurt en `+0x1cc`, cinco hurt boxes desde `+0x1d0`, cinco attack boxes desde `+0x220`, buffers rotados desde `+0x270` y punteros de rotación/collision box desde `+0x320`. `GameObjectBase` termina en `+0x34c`; `GameObject::lifetime` ocupa ese offset y el handle está en `+0x350`. El tamaño total base coincide con el campo que el manager consulta al retirar objetos.

El `FrameData.hpp` relacionado describe `CharacterFrameData` con `collisionBox`, vectores separados de hurt/attack boxes y metadatos de daño. El puntero de frame PAT de animación en `object+0x158` es distinto del `boxData.frameData` en `object+0x1c0`. La inspección del PE fijado confirma que `0x464b50` guarda la pose en `+0x140` y llama `0x464ae0`; este selecciona el descriptor PAT con stride `0xa8`, lo publica en `+0x158/+0x150`, reinicia subframe, copia duración desde descriptor `+8` a `+0x14c` y llama al setup de render `0x43a250`. Ese selector no escribe los contadores ni arreglos de cajas.

La rutina que faltaba es `0x465e10`. Su llamada en `0x47d1a7` ocurre dentro de una ruta del manager de objetos; la evidencia actual no demuestra que esa llamada resuelva colisiones. Compara `+0x158` con `boxData.frameData` (`+0x1c0`), publica la secuencia en `+0x1c4`, toma hit boxes del vector PAT `frame+0x6c` y hurt boxes de `frame+0x5c`, actualiza los conteos `object+0x1cb/+0x1cc` y genera arrays runtime hurt `+0x1d0` y hit `+0x220`.

El PAT de 808 seq.1 declara daño 150 pero cero collision/hurt/attack boxes; seq.0 tiene hurt `[-44,-44,44,44]` y hit `[-32,-32,32,32]`. La sonda Unicorn instala vectores PAT y ejecuta el factory original, `setPose` y `0x465e10`: con objeto en `(300,400)` y dirección 1, seq.0 publica una hurt box `[256,-444,344,-356]` y una hit box `[268,-432,332,-368]`; seq.1 publica ambos conteos en cero y no deja collisionBox. El harness restaura seq.1 antes de sus 32 ticks de dispatcher.

## Nivel de evidencia y límites

El sincronizador original ejecuta los helpers `0x4640b0` y convierte las cajas locales a bounds de mundo, reflejando X por dirección y restando Y de la posición: la caja hurt del PAT `[-44,-44,44,44]` resulta `[256,-444,344,-356]` en `(300,400)`. La sonda registra dos entradas nativas y cero interceptaciones. El probe no demuestra colisión geométrica, daño ni una pelea integrada. No se modifica el motor Vita.

`checkProjectileHit` tampoco queda validado como detector geométrico: el header lo define como auxiliar de densidad/collisions ya clasificadas.

## Touhou75Vita

Se releyó [TOUHOU75_REUSE_REVIEW.md](TOUHOU75_REUSE_REVIEW.md). Sus aportes útiles siguen siendo el inventario/CFG con cobertura explícita, contratos ABI, límites/watchdog, logs separados y pruebas diferenciales con vectores. No se transfiere runtime, offsets, renderer, imports ni datos del juego 7.5. El runner local TH123 ya cubre las corridas Vita3K frescas y el gate de 600 frames.

## Build y regresión

El VPK baseline disponible es [Touhou123Vita-TH75-review-current.vpk](../artifacts/Touhou123Vita-TH75-review-current.vpk), SHA-256 `c360c89d923e554bcff0cccf7c7ecb94164d3825f84958bcf7314e30daae9129`. No hay cambios de runtime desde ese baseline; no se recompila un VPK por esta auditoría. Suite Python del oráculo/analizadores: 37/37 aprobada. El VPK pasa el gate Vita3K schema28/600 frames según el reporte documentado en Iteración 1.79; esta iteración no generó evidencia Vita3K nueva.

## Siguiente paso

Determinar desde el CFG/desensamblado y una traza controlada qué ruta usa `0x465e10`, cuándo se invocan los helpers de transformación y cómo se calcula el primer impacto 808; después resolver si seq.1, sin cajas, participa por otra ruta. Integrar lifecycle/daño en el combate Vita con contratos diferenciales.
