# Iteración 0.4: diagnóstico de acciones y catálogo integral

## Resultado

Se amplió el input experimental con botones B/C y se endureció la autoprueba para exigir impactos de esos ataques. La prueba encontró una hipótesis incorrecta: los movimientos 400 y 500 existen como transiciones PAT, pero sus poses no tienen daño ni cajas de ataque. En Vita3K, la corrida fresca de 600 frames cargó los tres DAT (7 archivos internos) y 60 texturas y terminó sin crash; el combate reportó `a_hits=4`, `b_hits=0`, `c_hits=0`, por lo que la validación B/C **falló**. El VPK automático tiene SHA256 `51e23ad8fa0331936a06670d0596eeaa43dd15fdd93dc12c6b81ccf9900d8679`.

El VPK interactivo compilado con el mismo código es `artifacts/Touhou123Vita-iter04.vpk`, SHA256 `34f624b2eb9b20f4e9f5a8b1d56562eac11b527965f1ba6113f1b4153e4591d2`. Es útil para revisar la demo A de Reimu/Cirno, pero B/C se muestran como experimentales y no deben contarse como mecánica recuperada. La instancia local de Vita3K se abrió con esta build para revisión.

## Inventario integral

Se generó un manifiesto desde los índices locales de `th123a/b/c.dat`: 11,283 entradas, 1,088,266,746 bytes sin comprimir, 22 carpetas PAT de personaje y 14 carpetas de escenario bajo `data/background`. La clasificación global incluye personajes, efectos, escenas, clima, cartas, música, sonido, menú y perfiles.

- [RESOURCE_INVENTORY.md](RESOURCE_INVENTORY.md): categorías y archivos por carpeta.
- [PAT_COVERAGE.md](PAT_COVERAGE.md): imágenes, bloques, aliases, poses y cuadros dañinos por cada PAT decodificado.
- Los datos completos de la corrida están bajo `artifacts/` y se regeneran con `resource_probe --manifest`, `resource_probe --pat-inventory` y los scripts de resumen.

## Siguiente paso técnico

Usar el input de Reimu/Cirno y el despachador común exportados con Ghidra para mapear botones, direcciones, condiciones de cancelación y objetos a acciones PAT específicas. En esta lectura, Reimu tiene cuadros dañinos en 408/418 y 540+, mientras Cirno tiene 408/409/418 y otros grupos; esas coincidencias de ID no bastan para determinar qué botón los inicia. La implementación debe quedar bloqueada hasta tener una traza o condición de referencia que lo confirme. Después se repite el catálogo para imágenes de escenarios y se construye un visor de cobertura, separando disponibilidad de recursos de comportamiento reconstruido.
