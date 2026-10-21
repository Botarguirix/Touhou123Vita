# Iteración 2.198: reinicio de jugadores y cámara desde el PE

El reinicio común de Player (`0x46b9a0`) lee el lado en `+0x350`: `0x46ba2e..0x46ba63` calcula X = 480 + 320 × (lado == 1), escribe orientación +1/−1 en `+0x104` y después pone Y y velocidades a cero. Se ejecutó ese fragmento x86 sin sustituir instrucciones mediante `tools/x86_player_reset_probe.py`, fijado al hash `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. Resultado: izquierda (480,0), derecha (800,0), velocidades cero y orientación hacia el centro.

El constructor original de cámara, ejecutado con esos jugadores, devuelve X=640, Y=0 y zoom=1. El combate PAT del port usa ahora esas posiciones/cámara al enlazar personajes y reiniciar la ronda. Sus orígenes proyectados son (160,420) y (480,420) en el lienzo 640×480, antes de aplicar los offsets PAT del sprite. El fallback sin patrones conserva la disposición de demo y los guiones Story podrán sobrescribir posiciones cuando se implementen.

La selección muestra a los personajes/tarjetas en posiciones de presentación explícitas. Las sondas de ataques y sus reinicios también declaran su disposición histórica 190/450 y cámara 320; sus acciones, daños, tiempos y aserciones se mantienen. La primera corrida detectó precisamente una dependencia implícita del antiguo reset en la sonda de dash; se corrigió su disposición, no la aserción del comando. El arranque de producción se verifica por separado con `arena_spawn_contract`, requerido tanto por el guest como por el runner.

Validación:

- Prueba nativa `arena_tests`: inicio, orientación, proyección, reinicio por input y paredes/cámara de 40–1240 pasan.
- Python: 23/23 (cámara x86, reset, física, BG36/BG37/BG38).
- Vita3K SDL: schema46/600, status passed, regresión 1, `arena_spawn_contract=1`, dash 1, cinco sondas de objetos, cuatro rutas de ataque por objetos, BG36 25 tiles/cuatro auxiliares y bandas 4:3 válidas.
- Interactivo: 108,929 bytes; SHA-256 `b32275ded05242f541a63a40751c46328c4e97154b3af2988c1ace925d0c94ee`.
- Auto: 109,095 bytes; SHA-256 `3796f6f5d65192259c39c4c317c1f5369ca032de59f8520c2a124e747fb37d20`.
- Ambos VPK pasan check_vpk.py sin errores/advertencias; git diff --check sin errores de espacios.

La suite nativa general sigue fallando en el fixture Suika 530 ya identificado: el segundo bind reinicia el nivel configurado antes. No se declara verde esa suite. La captura BG36 del gate conserva su disposición diagnóstica y cámara 392; no es una captura del nuevo inicio de producción ni del PC original. La observación visual directa del PC sigue pendiente por fallo de captura de escritorio.

Siguiente: contrastar contra el PE la media escala de cajas PAT del resolvedor frente a la escala completa de sprites, conservando la fidelidad de contacto/daño por frame. El avance global sigue en 27%.
