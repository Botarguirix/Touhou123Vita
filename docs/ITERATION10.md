# Iteración 1.0: ilustraciones originales de selección para todo el roster

## Resultado

Se implementó una caché de dos ilustraciones `data/stand/<slug>.cv2`, cargadas bajo demanda mientras el usuario cambia P1/P2. Los CV2 no se mezclan con el render del frame de pelea ni se cuentan como sprites idle. La captura guest muestra las ilustraciones originales de Reimu, Cirno y Yuyuko en sus escenas de selección/práctica.

La autoprueba de 600 frames dio:

| Medida | Resultado |
|---|---:|
| Menú / práctica / pelea / salto | alcanzados |
| PAT cargados | 20/20 |
| Arte de selección decodificado | 20/20 |
| Sprite idle de combate decodificado | 11/20 |
| Texturas de poses cargadas | 93 |
| Impactos A / B / C | 3 / 0 / 0 |
| CPU | 9600/10000 HP |
| DAT internos / guest exit | 7 / 0 |
| Digest | `2562787365` |

La prueba integral sigue fallando por los nueve sprites idle sin resolver y B/C. El runner ahora conserva resultado y capturas aun con la gate fallida.

- VPK: `artifacts/Touhou123Vita-iter10-diagnostic.vpk`
- SHA-256: `3cdfc9f4cd5028d1289fd589608478223e1cc5cf6f3cada446375ddfd00539a9`
- Reporte: `artifacts/vita3k-result.json`
- Capturas guest: `artifacts/screenshots/{menu,practice,fight}.bmp`

## Investigación de sprites

Se verificaron los tres DAT de juego frente a la instalación de referencia; sus SHA-256 coinciden. `data/stand/<slug>.cv2` existe para los 20 personajes candidatos y decodifica como textura RGBA 640×480. Es arte completo de selección. No corresponde al atlas de frames del combate, por lo que no se usó para suplir poses.

Se amplió `resource_probe --pat-detail` para incluir `tx`, `ty`, `tw` y `th`; el catálogo regenerado tiene 76,357 poses y 7,975,746 bytes. Por ejemplo, los seis frames idle de Sakuya miden 64×128 y cada pose indica origen (0,0), lo cual concuerda con seis texturas de imagen separadas, no con seis recortes distintos de `data/stand/sakuya.cv2`. Sin el loader original, la ubicación de esos nombres sigue sin explicación.

## Validación y siguientes pasos

La suite host de la build anterior pasó 8/8; iter10 recompiló correctamente con VitaSDK y generó un guest que terminó sin excepción en Vita3K. La gate B/C y la cobertura de poses sigue fallida. El diagnóstico siguiente debe inspeccionar los callers del loader de imagen y las rutas de lookup de PAT del EXE fijado a SHA `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`; después se hará el contrato de imágenes, no antes. La tabla de poses ya conserva los rectángulos necesarios para comparar esa lógica.
