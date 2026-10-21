# Iteración 2.67: replay original validado por perfil y herramienta de profiling documentada

## Evidencia del replay real

Se ejecutó `tools/inspect_replay_layout.py` sobre el replay aportado `090815_2219_sanae_story.rep` usando explícitamente el `th123.exe` de la instalación original como `--exe`. El perfil coincide con SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`; el `.rep` coincide con versión aceptada `0x100c8`, tamaño 67.881 bytes y SHA-256 `6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e`. El decoder de PE consume el archivo completo: tres registros y cero bytes finales. El replay también contiene canales por jugador de longitudes 20/3, 20/3 y 20/4, y vectores finales de 8.720, 6.932 y 18.168 words, respectivamente.

Al usar por error `original/th123.exe` del checkout, el probe rechaza el replay. Ese binario corresponde a otro perfil/build; para este análisis la referencia válida es el ejecutable de `F:\Download\Touhou\TH12.3 ~ Unthinkable Natural Law\`. No cambiar la aceptación del parser C a partir de este error: su formato admite versiones 0xc8 y 0x100c8 y sus pruebas C actuales son sintéticas.

Esta ejecución confirma compatibilidad estructural con el loader del PE fijado, no una reproducción de combate ni la semántica temporal de cada word. La serie alterna valores crecientes, retrocesos y ceros; no asumir que un word equivale a un frame, ni conectar el cursor al combate hasta identificar consumo y sincronización con evidencia dinámica/frame-step del juego original.

## Evaluación de psp2-tooling

Se revisó [Grarak/psp2-tooling](https://github.com/Grarak/psp2-tooling). Puede aportar una fase de validación en Vita física: instalar/lanzar VPK, enviar input por USB, capturar consola/dumps y medir CPU/GPU. No acelera la decompilación ni las corridas ya automatizadas en Vita3K. El upstream es Linux-only; `retail-cp` para una Vita retail requiere taiHEN y módulos DECI4p de un DevKit 3.65 que el repositorio no incluye, y su prueba retail declarada es PCH-2000, fw 3.65. Por eso queda como herramienta opcional de M7, condicionada a hardware/configuración compatibles; no se importa código ni se instala plugin ahora.

## Próximo paso

Analizar los xrefs de productor/consumidor para el vector final y hacer una captura sincronizada input/estado/tick con el PE original, usando step-frame o instrumentación reproducible. Solo después definir cuándo avanza `t123_replay_cursor` y añadir carga del replay de usuario al runtime.
