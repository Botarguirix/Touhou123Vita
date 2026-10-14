# Roadmap

Cada hito se cierra con evidencia, no con un porcentaje estimado de código escrito.

| Hito | Trabajo | Criterio para cerrar | Estado inicial |
|---|---|---|---|
| M0: referencias | Inventario, versión, hashes, fuentes y análisis Ghidra | Ejecutable identificado, análisis guardado, límites documentados | Análisis inicial realizado; análisis automático parcial por timeout |
| M1: plataforma | C11 portable, VitaSDK, VPK, controles, framebuffer, CI | Compilación host y ARM, pruebas host y arranque Vita3K | Host/ARM y arranque automático Vita3K verificados |
| M2: demo de práctica | Menú, práctica, movimiento, salto, golpe, disparo, guardia, CPU, reset | Escenario automático y controles manuales en Vita3K | Prueba automática y framebuffer revisados; teclado manual pendiente; reglas propias |
| M3: recursos originales | Paquetes, paletas, CV2/CV3, PAT, capas de escenario, caché | Importador reproducible; sprites/animaciones/audio verificados contra PC | Extracción y conversión inicial; layout y animación pendientes |
| M4: combate original mínimo | Recuperar selección, práctica, estados, gravedad, colisiones y acciones de dos personajes | Práctica original reconstruida; secuencias PC/Vita comparadas fotograma a fotograma | Pendiente |
| M5: sistema completo | Cartas, clima, spirit, combos, estados especiales, todos los personajes | Replays representativos sin desincronización contra referencia | Pendiente |
| M6: optimización y hardware | GPU, atlas, cargas asíncronas, sonido, perfiles de memoria | 60 Hz sostenidos en Vita real; sin fugas ni fallos en sesiones largas | Pendiente |
| M7: distribución | Importador de datos del usuario, documentación, releases | VPK sin datos comerciales, instalación reproducible y suite verde | Pendiente |

Prioridad siguiente: mapear vtables y funciones de práctica/combat manager, fijar una versión base japonesa compatible con referencias, recuperar formatos PAT y comparaciones observables de física. La edición SokuLauncher aportada incluye mods/traducción; no asumir direcciones o hashes intercambiables con otra edición.

Netplay, rollback y modo historia se posponen hasta que el combate offline sea correcto y determinista. No hay fecha fiable para un port completo: el motor no está disponible como fuente ARM portable en las referencias verificadas.
