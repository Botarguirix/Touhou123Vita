# Iteración 1.62: origen del descriptor activo de Suwako 418

El barrido limitado a referencias ejecutables del PE encontró la escritura pertinente de `Player+0x158` en `00464ae0`. Esa rutina lee la lista de secuencia desde `Player+0x15c`, toma el puntero al arreglo en `[sequence+4]`, indexa el descriptor con `Player+0x140 * 0xa8` y escribe el resultado tanto en `Player+0x158` como en `Player+0x150`.

Esto resuelve el productor del puntero: durante la emisión de 418, `Player+0x158` identifica el descriptor de la pose actual. La rutina de spawn lee los dos enteros en descriptor `+0x98` y `+0x9c`. Sigue faltando mapear esos desplazamientos del descriptor de 168 bytes al registro PAT serializado, para extraer sus valores efectivos y comprobarlos contra el juego. Los offsets `ox/oy` visibles del sprite no son una sustitución válida sin esa correspondencia.

Añadí firmas del selector y su stride al analizador PE, además de los campos de procedencia en su reporte JSON. El oracle dinámico de la iteración anterior sigue verificando la aritmética de creación, sin fingir que conoce los valores de la partida.

## Verificación

- `tools/analyze_object_motion.py original/th123.exe`: valida las firmas de selección de pose y del spawn para el PE fijado.
- Suite Python: 25 pruebas aprobadas.
- No se recompiló el VPK: esta iteración afina la procedencia de datos; todavía no cambia el runtime.

## Siguiente paso

Reconstruir el layout de carga que transforma los bytes PAT en el descriptor x86 `0xa8`, identificar los campos que acaban en `+0x98/+0x9c` y cotejar valores de Suwako 418 antes de modificar el port.
