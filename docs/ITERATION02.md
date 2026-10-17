# Iteración 0.2: datos externos y animación original

Fecha: 2026-10-13. Clon principal indicado por el usuario para GitHub Desktop: `C:/Users/ikari/Documents/Vita_Touhou75/Touhou123Vita`.

Cambios verificables:

- VPK de código y fuente propia; sprites y paquetes comerciales excluidos.
- Interpretación directa de los tres DAT de la instalación limpia 1.01, prioridad C/B/A.
- Decodificación CV2/PAL y parser PAT v5 con aliases/reemplazos y límites.
- Kernel de animación contrastado en 4096 casos con funciones x86 reales de 1.01 y 1.10a. El refresco gráfico queda interceptado fuera del contrato.
- Comparación independiente: 4436 poses Reimu, 3429 Cirno y sprites RGBA idénticos a Shady Packer.
- Arena utiliza poses, cajas y daño de 5A de los archivos originales; vida de 10000.
- Vita3K: 600 frames, menú/práctica/pelea/salto, 14 impactos, CPU termina con 8200 HP, 54 texturas decodificadas de DAT externos, salida 0 sin fallo crítico.
- Host: 8/8 contratos aprobados, incluyendo parsers truncados y ambos oráculos x86.

VPK automático medido: `c01a36e0d2f19bc036fb140bd8e76a0e8cfce18855f644fb61ccebbe62f1805d`.
VPK interactivo medido: `8408ed2077d82eca201e59e0c36b400e07b38889592a5f983757896eb293e9ce`.

La primera autoprueba de esta iteración falló porque intentaba saltar durante 5A. Se corrigió el escenario para solicitar salto antes del ataque; no se redujo el criterio de validación.

Esta iteración no entrega el juego completo ni paridad de combate PC/Vita. Faltan física original, input buffering, hitstop, reacción al golpe, guardia completa, proyectiles, specials, cartas, clima, audio, escena completa y replay determinism. Los controles físicos y Vita real siguen pendientes.
