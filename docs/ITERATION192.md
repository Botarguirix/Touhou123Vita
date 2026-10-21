# Iteración 2.92: corregidos los límites del recorte PAT

Se ejecutó el constructor original de componente gráfico `0x406c60` del PE fijado (`f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`) con la consulta externa de tamaño de textura interceptada y dimensiones controladas. El nuevo oracle [`x86_sprite_component_probe.py`](../tools/x86_sprite_component_probe.py) usa tres casos, incluido `(tx,ty,tw,th)=(12,24,64,32)` sobre una textura 256×256. El PE crea un quad local 64×32 y UV `(0.046875,0.09375)→(0.296875,0.21875)`, equivalente a `(tx,ty)→(tx+tw,ty+th)` normalizado. Los vectores quedan en [`sprite-component-contract.json`](../artifacts/kernel/sprite-component-contract.json).

Ese contrato reveló un error en las llamadas del renderer Vita: la función Soft2D esperaba límites absolutos derecho/inferior, pero recibía PAT `tw/th` como límites. Jugadores y objetos ahora pasan `tx+tw` y `ty+th`. La regresión está añadida al test de renderer/cámara.

Validación:

- Oracle de componente gráfico: 3 fixtures del PE, todos pasan.
- `python -m unittest tests.test_stage_camera_oracle -v`: 10/10.
- `python -m unittest discover -s tests -p 'test_*.py'`: 110/110, ejecutado antes de añadir la aserción del nuevo oracle; la suite focalizada posterior pasó con la aserción.
- VitaSDK compiló VPK interactivo y automático; ambos tienen el mismo `eboot.bin`, SHA-256 `82963353ebf4c610204bfba41e8e8632755e52ab4941744b38363bb4ba8ac026`.
- Vita3K SDL aislado pasó schema46 y 600 cuadros, con gates de regresión, cámara, BG33, BG36, BG37 y BG38 aprobados.

Artefactos:

- Interactivo: [`Touhou123Vita-pat-crop.vpk`](../artifacts/Touhou123Vita-pat-crop.vpk), SHA-256 `2e6d9e9445040bffea8acce0f3a462eb0051305cc9d0137da130cac3b9d4e9dc`.
- Automático probado: [`Touhou123Vita-pat-crop-auto.vpk`](../artifacts/Touhou123Vita-pat-crop-auto.vpk), SHA-256 `fd15c4fdbbbb522c33f40a491b32cf67a7ad12d841b0313ad6f41983fa8f3b26`.
- Reporte: [`vita3k-result.json`](../artifacts/vita3k-result.json); captura: [`fight.bmp`](../artifacts/screenshots/fight.bmp).

Límites: el test automatizado actual no fuerza en runtime un PAT con `tx/ty` distintos de cero, y no hay captura sincronizada del ejecutable PC compatible con el PE fijado. El oracle valida tamaño y UV del quad; no cierra origen, escala de mundo/cámara ni paridad visual completa. Los DAT de usuario y artefactos VitaFS quedan fuera del VPK y del control de versiones.
