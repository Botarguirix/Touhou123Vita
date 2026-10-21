# Iteración 2.45: fórmula de ranuras del renderer BG33

Fecha: 2026-10-17.

Se contrastó el helper local de BG33 contra el renderer completo `0x473620` del PE fijado por SHA-256. El renderer calcula cuatro fases de 256 ticks, avanza seis índices fuente por fase, dibuja 30 slots, reutiliza la cuadrícula de 24 sprites, corrige el wrap vertical sumando `0x400`, indexa objetos con stride `0xe8` y suma `Background+0x44/+0x48` antes de enviar el sprite al sistema gráfico. Se añadieron pruebas sobre las instrucciones originales del loop y sobre las 30 ranuras en todas las fases con distintos contadores, incluido el wrap de 10 bits.

El renderizador de slots aún no está integrado en la página animada de BG33 ni en el escenario de combate: faltan los límites de tiempo de los sprites, la matriz/cámara compartida y la proyección de mundo. Por tanto, no se afirma paridad visual. El VPK de esta iteración conserva el visor y el gate anteriores mientras la comprobación exacta del nuevo helper corre en host.

Nota de precisión añadida en Iteración 2.49: la descripción inicial del helper como coordenadas de ancla no era correcta. Las anclas ya están en la matriz base del sprite; el helper debe devolver el desplazamiento de scroll y el wrap, que es el contrato vigente y probado.

Verificación: 75 pruebas Python aprobadas; build con VitaSDK; Vita3K SDL aislado pasó 600 frames, `schema=42`, `regression_gate=1`, layout BG33 capturado, 24 tiles y cuatro updates. VPK: `artifacts/Touhou123Vita-latest.vpk`, 104,127 bytes, SHA-256 `8abc90573fded56fc1f9713fc2efdaf911e01dcbbd7f54dbd865365a9d8df536`.
