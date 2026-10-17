# Iteración 0.6: recuperación de la demo A

Se retiró el avance automático entre índices PAT y se mantuvo el mapeo provisional de entradas hacia acciones B/C para seguir investigándolo. Los ocho contratos host pasan. VitaSDK generó VPK interactivo y automático desde una copia Linux temporal.

La corrida automática fresca en Vita3K recorrió menú, práctica y combate durante 600 frames; el invitado salió con código 0, abrió 7 DAT internos y decodificó 77 texturas. Resultado: `a_hits=4`, `b_hits=0`, `c_hits=0`, CPU `9400/10000` HP. La demo A está recuperada; la prueba de combate B/C sigue fallando y no se presenta como completa.

- VPK interactivo: `artifacts/Touhou123Vita-iter06.vpk`, SHA256 `8130299143940dfadb7a9911684738349f8182f0d2d1d1601ceb197fb5d53a11`.
- VPK de autotest: `artifacts/Touhou123Vita-iter06-auto.vpk`, SHA256 `636a5aea70d44b8ddb42ee85d832f88aab009975134d1e66c2038719c58763b2`.
- La build interactiva quedó abierta en la instancia local de Vita3K (proceso 23256).

## Hallazgo de input para la siguiente iteración

El enum SokuLib identifica `408=66B` y `418=66C`; el catálogo PAT confirma cajas dañinas en esos movimientos para Reimu y Cirno. La etiqueta pública aclara que `00487ba0` es `useSkill`, por lo que la siguiente exportación Ghidra debe cubrir `handleGroundBE` (`00487990`), `handleAirBE` (`00487ab0`) y `checkAllMotionInputs`, además de las funciones por personaje ya exportadas. Para B/C aún falta asociar entradas, selección de índice, objetos y colisiones. Después se añade una galería de roster y escenarios; la cobertura actual sigue limitada a Reimu/Cirno. Ver [KERNEL.md](KERNEL.md).
