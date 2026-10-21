# Iteración 2.61: suite host en WSL y localización del guard de versión `.rep`

## Validación host

La cifra preliminar 8/8 correspondía al build antiguo y quedó obsoleta al regenerar el build host con el árbol actual. El build fresco detectó fallos de `fight_contract`; tras corregir la posición inicial del trail secundario Remilia, WSL dejó de iniciar (`Wsl/Service/E_ACCESSDENIED`) antes de poder confirmar la reconstrucción. Por ello, CTest integral actualizado queda **pendiente**, no aprobado. El build contiene diez contratos, entre ellos `tools_contract` (51 pruebas Python) y las pruebas de escenario. El entorno usa paquetes Linux aislados en `local/wsl-tool-deps` (Capstone 5.0.7, Unicorn 2.1.4 y pefile 2024.8.26); Capstone 5.0.7 difiere del pin 5.0.9.

## Replay Sanae

Se regeneraron los reportes con `tools/x86_replay_compatibility_probe.py`. El archivo de 67,881 bytes (SHA-256 `6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e`, versión `0x100c8`) es compatible con la build 2009 proporcionada (PE SHA-256 `24e6149f729047fb3f5ceb24c8cdc055de2d1547babaa6724e0d6eba4530ded3`) y no con el ejecutable fijado actual (`0xd2/0x100d2`).

El desensamblado del PE 2009 localiza la lectura del DWORD inicial: el helper `0x42b4d0` abre la ruta, solicita cuatro bytes con `ReadFile` en `0x42b5b3` y cierra el handle en `0x42b5ce`. Su único caller encontrado es `0x42bdd1`; el resultado se compara en `0x42bdec` con el valor de `0x43ca50` (que retorna `0xc8/0x100c8`, o `0x100c8` según el modo). El branch compatible continúa en `0x42be2e`. La herramienta confirma la versión y este recorrido del encabezado; todavía no decodifica el cuerpo ni prueba playback.

La dirección `ADDR_INPUT_MANAGER_READ_REPLAY=0x42EAC0` de SokuLib no se puede aplicar a esta build 2009: en ese PE la dirección corresponde a código distinto; en el PE fijado más nuevo aparece el prólogo de la rutina de replay. La tabla de direcciones debe mantenerse ligada al hash/build correspondiente.

Siguiente paso: recuperar WSL para reconstruir y cerrar la suite fresca; en paralelo, seguir el branch `0x42be2e` y las lecturas posteriores para identificar el layout de registros de entrada, y validarlo contra una reproducción real antes de integrarlo al runtime Vita. No cambió el VPK.
