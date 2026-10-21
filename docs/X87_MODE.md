# T1: flags D3D9 y modo x87

PE 1.10a fijado: SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. El análisis no modifica `recomp/` ni el motor congelado.

## Resultado para el lifter

**Recomendación: modelo mixto, con control word y redondeo por hilo.** No adoptar `float` con redondeo al más cercano como semántica global. La creación de D3D9 no solicita preservar la FPU, pero el juego llama después a funciones que cambian el redondeo, y su CRT usa también precisión de 53 y 64 bits de significando.

Esto decide la arquitectura del estado x87, no demuestra todavía determinismo de replays. Un camino rápido con aritmética nativa requiere pruebas de equivalencia bajo el PC/RC activo. `float`, `double` y el `long double` del host no son sustitutos universales de x87: también importan el exponente, las conversiones, las operaciones trascendentes y los valores de 80 bits. Mantener `fldcw`, guardado/restauración y redondeo explícitos; evitar contracción FMA.

## Creación del dispositivo: evidencia ejecutada, confianza alta

`Direct3DCreate9` está en IAT `0x8572A0`, thunk `0x81F6B8`, llamada `0x414EF0`. El resultado se almacena en `0x8A0E2C`; el dispositivo sale en `0x8A0E30`. Los tres intentos leen el slot 16 (`+0x40`) de esa interfaz.

| Callsite | Condición | DeviceType | BehaviorFlags | Interpretación |
|---|---|---|---|---|
| `0x415028` | Primer intento | HAL (1) | `0x44` | MULTITHREADED + HARDWARE_VERTEXPROCESSING |
| `0x415049` | HRESULT negativo del primero | HAL (1) | `0x24` | MULTITHREADED + SOFTWARE_VERTEXPROCESSING |
| `0x41506B` | HRESULT negativo del segundo | REF (2) | `0x24` | MULTITHREADED + SOFTWARE_VERTEXPROCESSING |

Ninguna máscara contiene `D3DCREATE_FPU_PRESERVE` (`0x2`). Los inmediatos se preparan en `0x414FBC`, `0x415042` y `0x415063`; no salen de config en este fragmento. `Windowed` se escribe a 1 en ambos valores del argumento booleano de entrada ensayado; no se atribuye a ese argumento un significado no recuperado.

La herramienta ejecuta `0x414FA2` hasta éxito (`0x41508F`) o fallo de los tres intentos (`0x415071`) con Unicorn. Solo intercepta el método COM externo para observar los siete argumentos y devolver los HRESULT controlados. Ocho casos: ambos valores booleanos por cero, uno, dos y tres fallos. No reemplaza las instrucciones del juego ni ejecuta D3D9.

Según [Microsoft, D3DCREATE](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dcreate), sin FPU_PRESERVE el comportamiento predeterminado es precisión simple y redondeo al más cercano. Esa consecuencia es documental: **no se midió el control word de una DLL D3D9 real ni de un combate Windows**.

## El juego cambia el redondeo

En `FUN_00407DB0`, la llamada `0x407E02` consulta `_controlfp_s` (`0x82198E`) con máscara cero. En `0x407E1B` se pasa `new=0x200`, `mask=0x300`; en `0x408083` se pasa `new=0x9001F`, `mask=0xFFFFFFFF`. El contexto de las tres llamadas queda en el JSON local. La identidad de la función proviene del rango Ghidra, no de un nombre semántico deducido para el hilo.

**No confundir máscaras abstractas del CRT y bits físicos del CW:** en la API MSVC `0x300` selecciona RC, mientras que PC usa `0x30000`. Ejecutando el `_controlfp_s` y `_control87` originales con SSE deshabilitado explícitamente:

| CW inicial | new / mask | PC final | RC final |
|---|---|---|---|
| `0x007F`, `0x027F`, `0x037F` | `0 / 0` | Sin cambio | Sin cambio |
| Los mismos | `0x200 / 0x300` | 24 / 53 / 64 respectivamente | Hacia +∞ (2) |
| Los mismos | `0x20000 / 0x30000` | 24 | Al más cercano (0) |

Se ejecutaron nueve casos sin sustituir instrucciones del CRT; todos retornaron errno 0. Se verifican PC/RC, no una igualdad de bits reservados: la conversión de máscaras del CRT normaliza el bit 6 en algunos caminos. Estos casos prueban el cambio de estado solicitado, no qué hilo recorre cada camino durante una partida ni el estado SSE real de Windows.

Entradas identificadas: `_controlfp_s` `0x82198E`, `_control87` `0x82C962` y helper de CW físico `_ctrlfp` `0x82D67C`. Se inventariaron 33 referencias directas a esas entradas; las llamadas indirectas o wrappers no identificados pueden añadir otras.

## Censo de FLDCW

Se reproducen los **290 candidatos del barrido lineal**, todos con dirección, operando, contexto local, procedencia inferida y candidatos de rango de función Ghidra. No son 290 instrucciones ejecutables demostradas: el barrido incluye tablas dentro de `.text`. En particular `0x781D34` tiene contexto compatible con datos y queda sin resolver. Los rangos Ghidra también son incompletos y sus tamaños agregados no prueban pertenencia al CFG.

| Clasificación local automática | Sitios | Efecto |
|---|---:|---|
| CW guardado OR `0xC00` | 92 | RC hacia cero; preserva PC |
| Restauración de un slot guardado | 84 | Recupera el CW previamente guardado |
| CW guardado OR `0x300` / `0x33F` | 8 | PC de 64 bits; la segunda máscara también enmascara excepciones |
| Constante recuperada | 5 | Tres cargas de `0x027F` desde `0x8680F8`; dos de `0x133F` |
| Sin procedencia resuelta por el slice local | 101 | Requiere análisis de flujo/pilas, CRT o separar datos; no se atribuye un modo inventado |

Ejemplos: `0x4201F9` carga la variante para truncar y `0x420214` restaura; `0x8215B7`, `0x821C47`, `0x82220B` cargan `0x027F` (PC=53, RC=nearest). `__trandisp1` y `__trandisp2` cargan `0x133F` en `0x8275F2` y `0x827659` (PC=64, RC=nearest). Las modificaciones OR `0x33F` AND `0xF3FF` del CRT y las cargas calculadas de `_control87` también figuran, aunque el clasificador conservador no las reduce a una sola etiqueta.

El censo es completo respecto al barrido lineal reproducido; **no está cerrada la procedencia de todos los CW ni la cobertura de ejecución**. Los 101 casos sin resolver no son una afirmación de 101 cambios nuevos de precisión. El JSON añade candidatos `frstor` para no ignorar posibles cargas de estado, igualmente sin dar por probado que sean código. No se ejecutó un replay completo ni se probó equivalencia ARM.

## Reproducción y resultados

```powershell
python -m unittest tests.test_x87_mode_probe -v
python tools/x87_mode_probe.py
```

Resultado: 9 pruebas, `OK`. El informe reproducible se escribe en `artifacts/pe-inventory/<sha>/x87-mode.json`; no se publica el contexto desensamblado ni el PE. La prueba omite los casos dependientes del PE si falta `original/th123.exe`; un hash distinto falla.

Los tres archivos de T1 entregan las flags y una recomendación basada en evidencia, además del inventario con sus incertidumbres. Cerrar todos los slices y medir el estado de cada hilo en el juego real siguen pendientes. No se cambió el runtime del lifter, propiedad de Claude según AGENTS.md.
