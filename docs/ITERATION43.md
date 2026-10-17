# Iteración 1.39: revisión actualizada de Touhou75Vita

## Qué revisé

Inspeccioné el chat **Configurar Touhou75Vita** y su resumen del repo `Botarguirix/Touhou75Vita`. El resultado separa tres piezas con diferente utilidad:

- El análisis del PE (límites de funciones, CFG/reachability, histogramas, lifting a IR y generación semántica C) aporta metodología. El runtime experimental mantiene registros/memoria y un smoke test host; el test pasó y mostró valores de registros, stack, EIP y una global.
- El VPK documentado solo reconoce encabezados PE del juego y el parche de traducción, escribe el diagnóstico y sale. No ejecuta Touhou 7.5 ni constituye un juego recompilado. El build VitaSDK quedó sin validar porque el proxy del entorno devolvió HTTP 403 durante el bootstrap.
- El frontend `vdpm` descrito en la configuración más reciente administra un cliente Pacman aislado bajo `$VITASDK`, selecciona canales verificados mediante firma y prueba transacciones Windows. Puede servir para preparar el compilador en una máquina donde VitaSDK no esté configurado.

## Aplicación en Touhou 12.3

La metodología de hash fijado, inventarios alcanzables, cobertura de opcodes, lifting acotado y pruebas diferenciales ya se aplica aquí. En esta iteración además quedó documentado que `vdpm` es una opción de gestión del toolchain; no cambia el runtime del juego. La ruta local de build ya usa VitaSDK existente por `tools/build-vita-native.ps1`, por lo que no hay razón para instalar o copiar el bootstrap de Touhou75 a ciegas.

Las direcciones x86, tablas de acciones, structs, assets y semántica de combate pertenecen al ejecutable/version de cada juego. Cualquier patrón compartido debe volver a probarse contra `original/th123.exe`. No copié código del repo Touhou75: en los materiales consultados no se confirmó una licencia clara. Tampoco copié nada de `vdpm`, cuyo propio chat declara componentes y licencias separadas que habría que auditar antes de reutilizar.

## Resultado y límites

Esto actualiza la revisión de [ITERATION25.md](ITERATION25.md) y [PORT_REFERENCES.md](PORT_REFERENCES.md): ya conocemos una contribución práctica nueva, la opción `vdpm` para instalar/consultar VitaSDK. El port 12.3 no recibió cambios de motor ni se generó un VPK en esta iteración. El siguiente paso de juego sigue siendo recuperar las rutas de selección/cancelación de skills del handler Reimu y contrastarlas con los datos PAT y el x86 original; en paralelo, si el VitaSDK local falla, comprobar la instalación con `vdpm` sin mezclarla con el código del juego.
