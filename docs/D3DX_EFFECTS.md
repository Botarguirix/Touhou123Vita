# T2: efectos D3DX embebidos

Se extrajeron los tres blobs FX9 del PE 1.10a fijado a SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. Los tamaños proceden de los argumentos inmediatos del juego; el parser consume exactamente esos tamaños. No se publican blobs ni shaders en git.

## Identidad y creación

| Blob VA | Bytes | Callsite del wrapper | Destino |
|---|---:|---|---|
| `0x85A608` | 1 232 (`0x4D0`) | `0x471665` | Campo `this+0x40` de la construcción del escenario |
| `0x85F908` | 6 944 (`0x1B20`) | `0x7FB030` | Objeto global `0x89AAFC` |
| `0x861428` | 1 668 (`0x684`) | `0x7FB049` | Objeto global `0x89AB04` |

Los tres llaman a `0x418190`, que invoca `D3DXCreateEffect` en `0x4181C7`, vía thunk `0x81F6B2` e IAT `0x8572A8`. El dispositivo procede del global `0x8A0E30`. Confianza alta para direcciones, argumentos, estructura binaria e instrucciones decodificadas; media para el propósito visual inferido. No se ejecutaron los shaders ni se compararon imágenes PC/Vita.

## Parámetros, técnicas y estados

Todos usan la técnica llamada `SampleTexhnique` (ortografía original); los parámetros no declaran semántica ni arrays. Los valores iniciales escalares/vectoriales son cero.

| Efecto | Parámetros |
|---|---|
| `0x85A608` | `Tex0`: texture/object; `v4Arg0`, `v4Arg1`: float4/vector; `pshaderBlend`: pixelshader/object; `s0`: sampler/object |
| `0x85F908` | `v4Arg0`, `v4Arg1`: float4/vector; `width`, `height`, `x`, `y`: float/scalar; siete pixelshader/object: `pshaderMask`, `pshaderFlash`, `pshaderDP`, `pshaderDPFlash`, `pshaderEx0`, `pshaderEx0Mask`, `pshaderEx0DP` |
| `0x861428` | `v4Arg0`: float4/vector; tres pixelshader/object: `pshaderEx0Limit`, `pshaderEx0MaskLimit`, `pshaderEx0DPLimit` |

La unión de estados explícitos de passes es `VertexShader`, `PixelShader`, `PixelShaderConstant1` y `PixelShaderConstant2`. El sampler `s0` del primer efecto tiene una referencia `Texture` a `Tex0`. Los passes no especifican aquí estados de blending, profundidad, culling ni filtros; **no asumir que todo el juego prescinde de ellos**: se fijan también por llamadas D3D9 externas al FX (T3).

| Efecto / pass | Shader de píxel | Constantes de píxel | Shader de vértices |
|---|---|---|---|
| `0x85A608` P0 | Blend | c0, c1 | No se fija en el FX |
| `0x85F908` P0 | Mask | c0 | No se fija |
| P1 | Flash | c0 | No se fija |
| P2 | DP | c0 | No se fija |
| P3 | DPFlash | c0 y un bloque de dos registros desde c1 | No se fija |
| P4 | Ex0 | No se fija | VS del recurso de P4 |
| P5 | Ex0Mask | c0 | VS del recurso de P5 |
| P6 | Ex0DP | c0 | VS del recurso de P6 |
| `0x861428` P0 | Ex0Limit | No se fija | No se fija |
| P1 | Ex0MaskLimit | c0 | No se fija |
| P2 | Ex0DPLimit | c0 | No se fija |

Las referencias por nombre de los recursos FX enlazan esos estados con los parámetros de shader. El JSON conserva índices, tipos, offsets, valores y bindings; no confunde los IDs del objeto de estado con los IDs del parámetro al que se refiere.

## Shaders y reconstrucción de los cálculos

Se encontraron **14 programas delimitados por recursos FX: 11 `ps_1_1` y tres `vs_1_1`**. No se cuentan cadenas del compilador como programas. El conteo de instrucciones incluye `def`, `dcl` y `tex`, y excluye comentarios y END.

| Programa | Instrucciones | Cálculo inferido del bytecode |
|---|---:|---|
| Blend | 6 | Muestrea t0 y t1, multiplica por c0/c1, promedia sus RGB mediante división por dos y multiplica el resultado por el color de vértice. El alpha queda del primer producto; no promedia cuatro canales. |
| Mask | 3 | Interpola RGB entre la muestra y c0 usando c0.w; conserva alpha de la muestra y modula por color de vértice. |
| Flash | 4 | Suma c0 a la textura con saturación y modula por color de vértice. |
| DP | 4 | Producto escalar entre RGB de textura y c0, replicado en RGB; conserva alpha y modula por color de vértice. |
| DPFlash | 5 | Combina el RGB del producto escalar con c1 mediante su alpha, conserva alpha de textura y modula por color de vértice. |
| Ex0 | 6 | Clasifica la muestra con el producto escalar frente a `(0.26,-1,0.26)`. La condición CND, basada en el resultado frente a 0.5, elige entre t1 y t0; después modula por color de vértice. |
| Ex0Mask | 8 | Mismo selector entre t1/t0, modulación por color, suma saturada de c0 y una segunda modulación por color. |
| Ex0DP | 9 | Mismo selector y primera modulación; transforma RGB por producto escalar con c0, conserva alpha y modula otra vez por color. |
| Ex0Limit | 6 | Sustituye la segunda textura por negro con alpha 1 en el selector; después modula por color de vértice. |
| Ex0MaskLimit | 8 | Variante Limit con suma saturada y segunda modulación. |
| Ex0DPLimit | 9 | Variante Limit con producto escalar RGB y segunda modulación. |
| VS P4, VS P5, VS P6 | 13 cada uno | Transforma coordenadas de píxel a clip mediante escalas 2/640 y −2/480 y desplazamiento (−1,+1). Propaga color y UV0, y genera UV1 usando constantes c0..c3 y factor 1/256. |

Para vitaGL hacen falta variantes de fragment shader con esa selección, saturación, alpha y orden de modulaciones, además del vertex shader de coordenadas/UV. No reducir todos los programas a un tintado genérico. Los parámetros width/height/x/y y los recursos de expresiones FX deben conservar su enlace a constantes. La herramienta mantiene como binarios los payloads auxiliares que no son bytecode de shader; **no implementa un evaluador de expresiones/preshaders FX**. Su evaluación y validación de píxeles quedan para la capa D3DX y sus pruebas.

La relación del primer efecto con mezcla de escenario se infiere del constructor, nombre Blend y cálculo. La función concreta de Ex0/Limit en cada escena requiere trazar sus usuarios y capturar un frame. No se atribuyen estos efectos a clima o cartas específicos sin esa evidencia.

## Herramienta y verificación

```powershell
python -m unittest tests.test_extract_d3dx_effects -v
python tools/extract_d3dx_effects.py
```

Resultado: 7 pruebas, `OK`; extracción de 3 efectos. Se verifica el hash antes de crear salidas, límites del binario, consumo exacto, END de shader, rechazo visible de opcodes no soportados y reproducibilidad del JSON. La prueba del PE usa skipUnless si falta la copia local. No es un parser universal: structs y extensiones desconocidas fallan explícitamente; el conjunto observado sí se decodifica.

Salidas locales: `artifacts/pe-inventory/<sha>/effects/`: tres `.fxo`, catorce `.asm`, catorce bytecodes `.bin` y `effects.json`. No se modificó `recomp/`, el renderer ni CMake; no se generó un VPK nuevo con estos efectos.

Se consultaron las estructuras del formato de [Wine, effect.c](https://github.com/wine-mirror/wine/blob/master/dlls/d3dx9_36/effect.c) y las constantes de los encabezados DirectX ya presentes en `local/SokuLib/directx/`. El parser Python inspecciona los datos locales del usuario; no incorpora los shaders comerciales ni copia el parser de Wine.
