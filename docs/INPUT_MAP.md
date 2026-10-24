# T9: teclado SDL2 y botones Vita a DirectInput

Módulo independiente `recomp/host/input_map.[ch]`. No incluye SDL, DirectX,
VitaSDK ni Win32: usa sus valores numéricos públicos. No se modificó media.c
ni se conectó todavía a GetDeviceState. Claude integra las dos funciones.

## Tabla SDL2

Tabla de 512 bytes: **141 scancodes con DIK**, 371 posiciones cero. Los enteros
negativos o >=512 también devuelven cero. Se usan scancodes físicos, no
SDL_Keycode ni caracteres dependientes del idioma del teclado. El `.c` identifica
cada par por los nombres públicos; los índices no declarados se inicializan a 0.

Fuentes medidas localmente:

- `C:/msys64/ucrt64/include/SDL2/SDL_scancode.h`.
- `local/SokuLib/directx/dinput.h`.
- `C:/vitasdk/arm-vita-eabi/include/psp2common/ctrl.h`.
- Como comprobación primaria de teclas internacionales: [tabla Windows de SDL2](https://github.com/libsdl-org/SDL/blob/SDL2/src/events/scancodes_windows.h).

Se incluyen letras, fila numérica, F1..F15, signos, teclado numérico, edición y
navegación, modificadores izquierdo/derecho, teclas Windows, energía y las teclas
multimedia/web con equivalente. Se distingue Enter de keypad Enter (1C/9C),
Ctrl izquierdo/derecho (1D/9D), Alt (38/B8), multiplicación del keypad (37) y
PrintScreen (B7). NONUSHASH comparte backslash, SYSREQ comparte PrintScreen,
y MUTE/AUDIOMUTE comparten DIK_MUTE; esos alias son intencionados.

INTERNATIONAL1..5 se resuelven con los scancodes físicos Windows 73,70,7D,79,7B.
DIK_ABNT_C1 denomina 73 como tecla brasileña, pero SDL usa el mismo scan físico
para INTERNATIONAL1/Ro japonés. No convertir caracteres mediante el layout.

Quedan a cero, entre otros: F16..F24 (sin DIK_* en esta cabecera), acciones
clipboard/undo, USB Stop 120 (no confundir con DIK_STOP de PC98), LANG1..9,
INTERNATIONAL6..9 y operaciones extendidas de keypad sin correspondencia DIK.
No se deduce igualdad física de dos teclas solo por parecerse sus nombres.

## Teclado por defecto del juego

Evidencia del PE 1.10a, SHA-256
`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`.
Se verifica el hash antes de desensamblar. **Confianza alta estática**: stores
inmediatos al bloque keyboardBindings del perfil, corroborados por el layout
KeyBindings de `local/SokuLib/src/InputManager.hpp` y Profile.hpp.
No se presupone que los perfiles personalizados del usuario usen estos valores.

| Acción | Tecla | DIK | Dirección del store | Campo del perfil | Vita propuesto |
|---|---|---:|---|---|---|
| Arriba | flecha arriba | C8 | 0x435909 | +144 | cruceta arriba |
| Abajo | flecha abajo | D0 | 0x435913 | +148 | cruceta abajo |
| Izquierda | flecha izquierda | CB | 0x43591D | +14C | cruceta izquierda |
| Derecha | flecha derecha | CD | 0x435927 | +150 | cruceta derecha |
| A, melee | Z | 2C | 0x435931 | +154 | × |
| B, proyectil débil | X | 2D | 0x43593B | +158 | ○ |
| C, proyectil fuerte | C | 2E | 0x435945 | +15C | □ |
| D, dash | A | 1E | 0x43594F | +160 | △ |
| Cambio de carta | S | 1F | 0x435959 | +164 | L |
| Uso de carta | D | 20 | 0x435963 | +168 | R |
| Pausa | Q | 10 | 0x43596D | +16C | Start |

El mapa global de menús repite direcciones y seis acciones desde `0x442B2E`,
pero su último campo se inicializa a **Escape, DIK 01**, en `0x442B9C`, y se pasa
a `0x40A160` en `0x442BA7`. No confundirlo con la pausa Q del perfil.

La interfaz fija carece de contexto de escena: Start genera **Q solamente**.
La integración debe decidir si necesita traducir Start a Escape en menús; no se
inyectan Q y Escape simultáneamente sin verificar su interacción. Enter/Escape
están disponibles desde el teclado SDL, pero el módulo no genera Enter desde
otro botón Vita. Las confirmaciones/cancelaciones con Z/X corresponden al juego.

## Estado y comprobaciones

`dik_state_from_vita_buttons` sobrescribe exactamente 256 bytes por llamada,
con 0x80 para pulsadas y 0 para liberadas; ignora bits desconocidos. Un estado
nulo es un no-op. Direcciones opuestas se preservan como dos teclas; no aplica
SOCD, repetición, deadzones ni persistencia entre frames. Para combinar teclado
y Vita, el host debe OR los estados después, no pasar una salida de teclado
esperando que esta función la conserve.

```powershell
python -m unittest tests.test_input_map -v
C:/vitasdk/bin/arm-vita-eabi-gcc.exe -std=gnu11 -O1 -Wall -Wextra -Werror -c recomp/host/input_map.c -o artifacts/t9-input-map-arm.o
```

Resultado literal: **3 pruebas, OK**; compilación ARM **pasó, código 0**.
El harness recorre las 2048 combinaciones de los once botones con guardas de
memoria y comprueba liberación, bits desconocidos, números/letras, flechas,
Shift, Enter, Escape y extremos de índices. Se comparan las 512 salidas del
binario con las constantes de las cabeceras y los stores originales con Capstone.
Las pruebas PE usan skipUnless cuando falta el ejecutable; las de compilación
cuando falta GCC. `git diff --check` pasó.

Sin verificar: recepción en el juego, navegación de menús con mando, perfiles
personalizados, otros layouts físicos, Vita3K y consola. No cambia `recomp/host/media.c`.
