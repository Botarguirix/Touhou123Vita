# Requisitos y decisiones

## Entradas necesarias

- Instalación de Touhou 12.3 aportada por el usuario, ejecutable y `th123a/b/c.dat`.
- La ruta aportada contiene también archivos TH10.5 y módulos de SokuLauncher. Mantener un manifiesto por versión; los datos adicionales se analizan por separado.
- Replays cortos de referencia, capturas y mediciones de PC para validar precisión del motor recuperado.
- Replay candidato disponible en el VitaFS local: `ux0/data/Touhou123Vita/replay/story/090815_2219_sanae_story.rep` (67,881 bytes, SHA256 `6905658c1f5fb09089eecd5d5b7323f581b4b2030293f27c0323dafb9895de3e`). Es un archivo binario de historia; falta confirmar que la build/referencia 1.01 o 1.10a lo reproduzca antes de usarlo como oráculo.
- VitaSDK, CMake, compilador C11, Python y Pillow; JDK compatible y Ghidra.
- Vita3K con firmware instalado para regresiones de emulador; PS Vita real para dar por verificados rendimiento, sonido y compatibilidad física.

## Arquitectura

`src/fight.c`: práctica de dos personajes, estados base, ataques A direccionales y cadenas hit-confirm sobre poses PAT. `src/animation.c`: kernel original de poses validado con x86. `src/resources.c` y `src/pattern.c`: interpretación nativa DAT/CV2/PAL/PAT. `src/vita_main.c`: escenas, caché de texturas y autoprueba. `src/soft2d.c`: framebuffer. El mundo/cámara y la física siguen siendo provisionales; todavía no representa el juego completo.

El exe original es PE32 x86. Las DLL de mods y llamadas a direcciones absolutas no pueden vincularse directamente al ejecutable ARM. Ghidra genera evidencia para reconstruir funciones, tipos y flujo; su pseudocódigo no es automáticamente código compilable ni una certificación de equivalencia.

El renderizador copia texturas en CPU; requiere optimización/GPU para el juego completo. El fondo usa una única pieza de escenario, no su composición original. Los personajes reproducen poses y duraciones PAT originales con kernel recuperado; la máquina de estados completa sigue pendiente.

## Riesgos técnicos

1. Recuperación incompleta de acciones por personaje y precisión de collision/hitstop.
2. Diferencias entre exe vanilla, traducción y hooks de mods.
3. Memoria de texturas, audio y cargas; los paquetes completos no se cargan en RAM.
4. Determinismo de coma flotante, RNG, entradas y replays PC/ARM.
5. Diferencias de Vita3K frente a hardware real; un pase del emulador no valida la consola.

## Publicación

Subir solo código propio, scripts y documentación. Los recursos de la instalación permanecen en carpetas ignoradas. Auditar licencias de cualquier código externo antes de integrarlo; en esta fase se usan herramientas externas locales y enlaces, sin copiar implementaciones al runtime.
