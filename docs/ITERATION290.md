# Iteración 2.190: cielo base BG36 detrás de sus capas

El renderer x86 BG36 calcula un color de cielo con base RGB `(126,206,244)` y dibuja ese campo antes de los tiles; con los tintes iniciales en cero, el port ahora reproduce ese fondo en la arena. El color coincide con el azul opaco del recurso `clowd_s`, por lo que sus bordes quedan integrados con el cielo. Se conserva el fondo BG10 solo como reserva si no hay stage renderer disponible.

El VPK autotest mide 108,453 bytes, SHA-256 `defd5c0c651e3ec2cd98821f82ec385f4ead6de64353960d9059b6e638285fed`. Vita3K SDL pasó 600 frames con `regression_gate=1`; la base BG36 dibujó 25/25 tiles presentes (máscara `477888511`), los cuatro auxiliares dibujaron y la captura se confirmó. El SHA del reporte fresco coincide con el VPK. El VPK interactivo mide 108,287 bytes, SHA-256 `3c5d77ab8fe346345fab777c8bd657337c7503c754369841638e2440a1b60216`. Ambos pasan `check_vpk.py` sin errores ni advertencias.

Los contratos unittest BG36 (3/3, incluida la nueva aserción del color base) y BG37/BG38 (4/4) pasan. La captura [fight-bg36.bmp](../artifacts/screenshots/fight-bg36.bmp) confirma que el fondo azul y el parche azul de nube se integran; todavía quedan posiciones/parallax, tintes variables y comparación sincronizada con el juego original. La suite pytest global sigue sin ejecutarse: falta pytest local y WSL denegó acceso. El roadmap queda en 27% porque un renderer parcial no cuenta como escenario terminado.

Siguiente: reconstruir los parámetros dinámicos de tinte y las fases/transformaciones de las capas auxiliares BG36 desde el PE; después comparar capturas equivalentes con PC y conectar selección del escenario al combate interactivo.
