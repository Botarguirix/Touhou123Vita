# Iteración 2.184: VPK válido con LiveArea y gate fresco en Vita3K

El validador de VPK descubrió que los paquetes anteriores se podían ejecutar en Vita3K pero carecían de los recursos LiveArea requeridos para una instalación correcta (`sce_sys/icon0.png`, `bg.png`, `startup.png` y `template.xml`). El proceso nativo ahora genera esos recursos localmente con PNG indexado (tipo de color 3, aceptado por Vita) e incluye los cuatro en cada paquete. Se agregó `tools/make_livearea_assets.py`; sus dimensiones/template tienen una prueba unitaria.

Se reconstruyeron desde las fuentes actuales con VitaSDK:

- Autotest: `artifacts/Touhou123Vita-current-auto.vpk`, 106,680 bytes, SHA-256 `5c96965a2009caafcc061441899db3ffb449cbcca9e3c2b58b19190456d54613`.
- Interactivo: `artifacts/Touhou123Vita-current.vpk`, 106,514 bytes, SHA-256 `69d56fd332580c510fc71f661149d1c053c2464aea76649a503d6297d06bb82e`.
- Ambos contienen el mismo `eboot.bin`, SHA-256 `edeabed9bb5bcdcb09a851a54a86ba2a59fa6ba0bef2ac843f4ddb51fd2b90f6`; solo el VPK automático incluye `auto-test.txt`.

`check_vpk.py` informó cero errores y cero advertencias en ambos paquetes (8 y 7 entradas). El autotest recién generado se ejecutó con Vita3K SDL aislado: schema 46, 600 frames, `status=passed`, `regression_gate=1`; `artifacts/vita3k-result.json` registra el mismo SHA-256 del VPK. Pasaron 137 pruebas Python y la prueba focalizada del generador LiveArea (1/1). No se probó el paquete interactivo por separado en Vita3K; contiene el mismo `eboot.bin`. Esto verifica la instalación/emulación del prototipo actual, no paridad completa ni ejecución en hardware.

Siguiente: continuar integrando escenas y mecánicas completas con referencia x86/PC; mantener este gate para cada VPK y reemplazar los placeholders visuales de LiveArea cuando haya arte final del proyecto.
