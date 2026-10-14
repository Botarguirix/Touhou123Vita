# Requisitos y decisiones

## Entradas necesarias

- Instalación de Touhou 12.3 aportada por el usuario, ejecutable y `th123a/b/c.dat`.
- La ruta aportada contiene también archivos TH10.5 y módulos de SokuLauncher. Mantener un manifiesto por versión; los datos adicionales se analizan por separado.
- Replays cortos de referencia, capturas y mediciones de PC para validar precisión del motor recuperado.
- VitaSDK, CMake, compilador C11, Python y Pillow; JDK compatible y Ghidra.
- Vita3K con firmware instalado para regresiones de emulador; PS Vita real para dar por verificados rendimiento, sonido y compatibilidad física.

## Arquitectura

`src/fight.c`: modelo determinista del prototipo, sin APIs Windows. `src/vita_main.c`: escenas, controles y escenario automático. `src/soft2d.c`: framebuffer y texturas RGBA. El mundo lógico provisional usa 640x480 y se escala a 544 píxeles de alto con barras laterales; geometría y timings originales requieren confirmación posterior.

El exe original es PE32 x86. Las DLL de mods y llamadas a direcciones absolutas no pueden vincularse directamente al ejecutable ARM. Ghidra genera evidencia para reconstruir funciones, tipos y flujo; su pseudocódigo no es automáticamente código compilable ni una certificación de equivalencia.

El primer renderizador copia texturas en CPU. Sirve para probar plataforma y controles; tendrá que reemplazarse o optimizarse para el juego completo. El fondo provisional usa una única pieza de un escenario, no su composición original. Los personajes muestran sprites de referencia, no animaciones o movesets recuperados.

## Riesgos técnicos

1. Recuperación incompleta de acciones por personaje y precisión de collision/hitstop.
2. Diferencias entre exe vanilla, traducción y hooks de mods.
3. Memoria de texturas, audio y cargas; los paquetes completos no se cargan en RAM.
4. Determinismo de coma flotante, RNG, entradas y replays PC/ARM.
5. Diferencias de Vita3K frente a hardware real; un pase del emulador no valida la consola.

## Publicación

Subir solo código propio, scripts y documentación. Los recursos de la instalación permanecen en carpetas ignoradas. Auditar licencias de cualquier código externo antes de integrarlo; en esta fase se usan herramientas externas locales y enlaces, sin copiar implementaciones al runtime.
