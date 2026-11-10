# Teclado en pantalla y modo ADHOC: investigación y diseño

Fecha: 5 de noviembre de 2026. Todo lo de este documento sale del `th123.exe` 1.10a (SHA-256 `f0db9366…a16731e`) y del descubrimiento de funciones; las direcciones son del PE. Lo marcado como **hipótesis** no está comprobado en una Vita.

## 1. Teclado en pantalla (nombre de perfil, direcciones IP)

### Cómo recibe texto el juego

| Dirección | Qué es |
|---|---|
| `0x7fb560` | `wndproc` de la clase `th123_110a` (33 bytes): salta a `0x408260` |
| `0x408260` | Manejador de mensajes: si `[this+0x2b] != 0` pasa el mensaje a `0x40f000`; maneja Alt+Enter y el cierre |
| `0x40f000` | Editor de texto (616 bytes, usa `ToAscii`): despacha `WM_KEYDOWN` (0x100), `WM_CHAR` (0x102), `WM_IME_COMPOSITION` (0x10f), `WM_IME_ENDCOMPOSITION` (0x10e) y `WM_IME_CHAR` (0x286) |
| `0x8a0cff` (byte) | **Campo de texto activo**: es el disparador |
| `0x8a02f8` | Búfer del texto (Shift-JIS, máx. 1023 bytes), con el cursor en `0x8a0d00` y el máximo en `0x8a0cf8` |
| `0x40ec50(c)` | Añade un carácter al búfer (maneja bytes de cabecera Shift-JIS) |
| `0x40ea60`, `0x40ead0` | Leen `ImmGetCompositionStringA` (composición y resultado del IME) |
| `0x40d400` | Pegado del portapapeles (`OpenClipboard`, `GetClipboardData`, `GlobalLock`); lo llama `0x449160` |

Conclusión: el texto entra por **mensajes de ventana**. En el host actual `PeekMessageA` nunca devuelve nada y `DispatchMessageA` no llama al `wndproc`, por eso no se puede escribir.

### Diseño

1. **Cola de mensajes sintéticos.** `PeekMessageA` devuelve, si la hay, una entrada de la cola (`hwnd`, `message`, `wParam`, `lParam`, tiempo); con `PM_REMOVE` la saca. `DispatchMessageA` pasa a llamar al `wndproc` del juego (el que registró `RegisterClassExA`) con `guest_invoke`. Así los mensajes se procesan en el hilo del propio juego, sin carreras.
2. **Disparador.** En cada frame (en `render_present`), leer el byte `0x8a0cff`. Al pasar de 0 a 1, abrir el diálogo de teclado de la Vita (`sceImeDialogInit` con `SceImeDialogParam`), con el texto actual del búfer (Shift-JIS → UTF-16) como valor inicial y `maxTextLength` tomado de `0x8a0cf8`.
3. **Mientras el diálogo está abierto:** presentar con `vglSwapBuffers(GL_TRUE)` y llamar a `sceCommonDialogUpdate`; el juego sigue corriendo debajo.
4. **Al terminar con Aceptar:** convertir UTF-16 → Shift-JIS (tabla inversa de `sjis_table.h`), enviar `WM_CHAR` con la tecla borrar (8) tantas veces como bytes tenga el campo, luego un `WM_CHAR` por cada byte del texto nuevo, y por último `WM_KEYDOWN` con `VK_RETURN` para cerrar el campo. Con Cancelar: `WM_KEYDOWN` con `VK_ESCAPE`.
5. **Bibliotecas:** `SceCommonDialog_stub` ya está en el enlace; las funciones están en `<psp2/ime_dialog.h>` y `<psp2/common_dialog.h>`.

Riesgos y puntos a confirmar:
- **Hipótesis:** `VK_RETURN` y `VK_ESCAPE` llegan por `WM_KEYDOWN` y cierran el campo. Se confirma mirando la tabla de saltos de `0x40f000` (`0x40f268` y `0x40f28c`) o probando.
- **Hipótesis:** el borrado por `WM_CHAR` con 8 funciona como en un teclado real.
- El IME de la Vita escribe en el idioma del sistema; las kanas y kanjis dependen de él.
- El VPK anterior a la pérdida tenía esta función (cadenas `# keyboard: text field active`, `typing N characters`, `GetClipboardData: N characters`) y pegaba el texto por el portapapeles. La vía de mensajes elegida aquí es independiente de ese código perdido.

## 2. Modo ADHOC (dos Vitas)

### Superficie de red del juego

El juego importa solo 14 funciones de `WS2_32`: `WSAStartup`, `WSACleanup`, `WSAGetLastError`, `socket`, `bind`, `sendto`, `recvfrom`, `closesocket`, `shutdown`, `htons`, `ntohs`, `htonl`, `inet_addr` y `gethostbyname`. **No importa `select`, ni `connect`, ni `send`/`recv`:** es UDP puro con `sendto` y `recvfrom`. Funciones del juego: apertura de socket en `0x413090`, cierre en `0x413250`, `bind` en `0x413300`, envío en `0x413350` y `0x4133f0`.

Hoy todos los sockets fallan con `WSAENETDOWN` (`recomp/host/other.c`), así que el menú de red no conecta.

### Diseño

Implementar esas funciones sobre `sceNetAdhoc*`, sin tocar la lógica del juego:

| Llamada del juego | En ADHOC |
|---|---|
| `socket(AF_INET, SOCK_DGRAM)` | Reserva un descriptor propio (no se crea el PDP todavía) |
| `bind(puerto)` | `sceNetAdhocPdpCreate(mac propia, puerto, tamaño de búfer)` |
| `sendto(destino)` | `sceNetAdhocPdpSend(pdp, mac del rival, puerto, datos)` |
| `recvfrom` | `sceNetAdhocPdpRecv(...)` sin bloqueo; devuelve la IP ficticia del rival |
| `inet_addr`, `gethostbyname` | Resuelven cualquier texto a la IP ficticia del rival |
| `htons`, `ntohs`, `htonl` | Normales |

- **Emparejamiento:** antes de jugar, una pantalla propia (o automática) que une a todas las Vitas al grupo `T123` con `sceNetAdhocctlConnect` y obtiene la MAC del rival de `sceNetAdhocctlGetPeerList`. Con dos Vitas, el rival es el único par.
- **IP ficticia:** el juego pide una IP en "Cliente"; se acepta cualquiera, porque el destino real es la MAC del rival. En "Servidor" el que espera recibe de cualquiera.
- **Tamaño de paquete:** PDP limita los datagramas; hay que medir los del juego (están en `0x413350` y `0x4133f0`).
- **Latencia:** el juego usa retardo de entrada, no rollback; hay que medir el RTT del ADHOC.
- **Vita3K** probablemente no emula bien el ADHOC: esta parte se prueba solo en consolas reales.

Dependencia: para escribir la "IP" en el menú hace falta el teclado de la sección 1.

### Corrección del diseño (5 nov 2026): el ad-hoc de la Vita es por IP

Al leer los encabezados del VitaSDK resultó que el diseño de arriba (PDP con direcciones MAC) era el de la PSP. En la Vita el ad-hoc usa **direcciones IP** (rango 169.254.x.x, `SCE_NET_INADDR_AUTOIP`): `SceNetAdhocMatching` identifica a los pares con `SceNetInAddr`, `sceNetCtlAdhocGetInAddr` da la IP propia, y el SDK **no exporta** `sceNetAdhocctlConnect`: la conexión la establece el emparejamiento. Por eso la implementación (`recomp/vita/net_vita.c`) es:

- **Emparejamiento:** `SceNetAdhocMatching` en modo P2P con dos miembros. Al oír el `HELLO` del otro, pide el emparejamiento el que tiene la dirección más baja; el otro acepta el `REQUEST`. En `ESTABLISHED` guarda la IP del par.
- **Sockets:** las 14 funciones de `WS2_32` se mapean a sockets UDP de SceNet (`sceNetSocket`, `sceNetBind`, `sceNetSendto`, `sceNetRecvfrom` con un `SO_RCVTIMEO` de 100 ms para poder cerrar el hilo que bloquea en `recvfrom`). Con `adhoc.txt`, todo datagrama va a la IP del par emparejado, sea cual sea la IP que el jugador escribió; lo que llega de él se informa con la dirección que el juego usó, para que sus comprobaciones sigan valiendo.
- **`wifi.txt`:** los mismos sockets sobre el Wi-Fi normal, con la IP real escrita en el juego (sirve para Vita↔Vita por router y para Vita↔PC).
- **Sin ninguno de los dos archivos** la red sigue apagada (`WSAENETDOWN`), como antes.

**Hipótesis sin comprobar en hardware:** los números de evento de `SceNetAdhocMatching` (el SDK no los define; se usan los de la PSP: 1 HELLO, 2 REQUEST, … 7 ESTABLISHED), que los datagramas UDP normales viajen por la red ad-hoc una vez emparejados, y que no haga falta ninguna llamada más para unirse al grupo. El trace registra cada paso (`# adhoc: …`, `# net: …`) para corregirlo.

### Plan de pruebas con las 5 Vitas

1. Dos Vitas se ven en `sceNetAdhocctlGetPeerList` (solo la pantalla de emparejamiento).
2. Eco UDP: una envía y la otra recibe, con la longitud de los paquetes del juego.
3. Menú "Network → Servidor / Cliente": la conexión se establece.
4. Una pelea completa y reproducible dos veces sin desincronizarse.
5. Una tercera Vita como espectador, y dos parejas a la vez en la misma sala.

## 3. Orden de trabajo

1. Teclado (cola de mensajes, disparador, diálogo, conversión Shift-JIS).
2. WS2_32 sobre ADHOC (descriptores, PDP, IP ficticia) y la pantalla de emparejamiento.
3. Pruebas del plan anterior.
