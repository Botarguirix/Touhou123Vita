# F1.1: descubrimiento propio de funciones y switch

Fecha: 21 de octubre de 2026. Primer entregable de F1 en el [roadmap de recompilación](ROADMAP_RECOMP.md). Criterio de salida (definido en [PE_INVENTORY.md](PE_INVENTORY.md)): cubrir al menos el 99 % de los bytes no-padding de `.text` y explicar el resto.

**Resultado: 99,40 %. Criterio cumplido.**

```powershell
python recomp/discover.py                       # ~90 s; salida local en artifacts/recomp/<sha>/
python -m unittest tests.test_recomp_discover -v
```

## Método (`recomp/analysis/discover.py`)

- **Descenso recursivo** con Capstone (modo detalle). No usa la lista de funciones de Ghidra.
- **Semillas, por orden de confianza:**
  1. punto de entrada;
  2. destinos de `call` directos;
  3. inmediatos que apuntan a código (`push offset`, `mov reg, offset`);
  4. punteros alineados en `.rdata`/`.data` (vtables, tablas de callbacks, EH);
  5. huérfanos que empiezan tras padding de alineación.

  Las semillas de baja confianza solo se aceptan si sus primeras instrucciones decodifican limpio, sin tocar tablas ni caer a otra alineación. Si dos funciones decodifican los mismos bytes de forma distinta, gana la de mayor confianza.
- **Switch de MSVC:**
  - `jmp [idx*4+tabla]`, opcionalmente detrás de `movzx idx, byte [reg+tabla_índice]` (dos niveles).
  - El tope se obtiene del `cmp`/`and` anterior, incluido `cmp idx, reg`, donde `reg` es un registro preservado cargado con una constante cerca del prólogo.
  - Se contemplan las tablas con sesgo `-4` del CRT.
  - Los bytes de tabla se marcan como datos y la exploración nunca los atraviesa.
- **Funciones noreturn** por punto fijo (sin `ret` ni tail call que regrese) para no decodificar lo que sigue a sus llamadas. Importaciones noreturn: `ExitProcess`, `TerminateProcess`, `ExitThread`, `FatalAppExitA`, `RaiseException`.
- **Tail calls dinámicos** (`jmp reg`, `jmp [reg+disp]`, típicos de thunks virtuales `mov eax,[ecx]; jmp [eax+N]`) se tratan como salida de la función, no como switch sin resolver.

## Resultados sobre `th123.exe` 1.10a

| Medida | Valor |
|---|---|
| Funciones | **6 414**: 3 144 por `call`, 2 545 por punteros en datos, 669 por inmediatos, 55 huérfanas tras padding, más el punto de entrada |
| Funciones noreturn | 137 |
| Bytes de código / tablas de salto / tablas índice | 4 383 458 / 52 168 / 44 879 |
| Padding | 35 091 |
| **Sin explicar** | **26 943 bytes (0,60 % de lo no-padding)** |
| Switch resueltos | 1 319 (1 229 por `cmp`, 10 por `and`, 80 heurísticos) |
| Saltos indirectos sin resolver | 9 (5 en `memcpy`/`memmove` del CRT) |
| Tail calls dinámicos | 69 |
| Instrucciones solapadas a otra alineación | 2 |
| Bytes de tabla decodificados también como código | 0 |

Comparación con el proyecto Ghidra (5 558 funciones y 2,37 MB dentro de funciones): coinciden 5 397 entradas, hay 1 017 nuevas, y de las 161 que solo tiene Ghidra, 156 caen dentro de código cubierto aquí (Ghidra corta funciones en otros puntos). Ghidra dejaba fuera de funciones cerca del 47 % de `.text`.

### Qué queda sin explicar

| Clase | Bytes | Comentario |
|---|---|---|
| Fragmentos con forma de código | 18 138 en 653 rangos | Sobre todo relleno de alineación multibyte dentro de funciones (`lea esp,[esp]`, `mov edi,edi`) y algunos cuerpos de `case` sin alcanzar. Los mayores están en `0x7f7fe0` (11 KB), `0x6048f2` (3,4 KB) y `0x7f78c0` (1,7 KB). |
| Fragmentos del CRT | 3 785 en 66 rangos | Rutinas x87 y `memcpy` del CRT; se reemplazarán por código nativo |
| Datos en `.text` | 4 972 | Tabla de punteros en `0x80f330` |
| Otros datos | 48 | Restos de tablas |

### Avisos para el lifter

- Los **80 switch heurísticos** (sin tope visible, 18 fuera del CRT) y los **9 saltos sin resolver** se compilarán con un respaldo en tiempo de ejecución: búsqueda de la dirección en el mapa de bloques de la función y `guest_fault` si no existe. Así un caso que falte se detecta en vez de quedar silencioso.
- Los **cuerpos de `case` no alcanzados** se compilarán dentro de la función vecina como bloques con etiqueta propia, no como funciones sueltas: comparten frame de pila con su función.

## Pruebas

`tests/test_recomp_discover.py` construye una imagen sintética con un mini ensamblador y comprueba:

- funciones halladas por `call` y por vtable, y que un puntero basura se rechaza;
- un switch acotado por `cmp`, con sus bytes de tabla clasificados como datos;
- un switch de dos niveles (tabla índice de bytes);
- que los bytes tras una llamada a `ExitProcess` no se decodifican.

Si existe `original/th123.exe`, la prueba comprueba además que el punto de entrada real decodifica.

## Actualización F1.3

La resolución de topes por flujo de datos de [F1_COVERAGE.md](F1_COVERAGE.md) cambió las cifras: 6 406 funciones, 99,48 % de cobertura, 48 switch heurísticos (2 en el juego) y 2 saltos indirectos sin resolver. Las tablas de este documento reflejan la versión de F1.1.

## Siguiente

F1.2: **lifter mínimo**. Traducir a C y compilar en PC el kernel de animación ya verificado (`tools/x86_animation_oracle.py`, 4 096 casos) y pasar su prueba de equivalencia. Antes hay que fijar el modelo x87 con el resultado de la tarea T1 de Codex ([CODEX_TAREAS.md](CODEX_TAREAS.md)).
