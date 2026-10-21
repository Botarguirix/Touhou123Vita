# Iteración 2.98: revalidación Vita3K del VPK con recorte PAT

Se volvió a ejecutar en la instancia aislada de Vita3K el auto-VPK más reciente, `artifacts/Touhou123Vita-pat-crop-guest-auto.vpk`, con la copia compartida en `G:\Vita3k` y el VitaFS local. El runner produjo evidencia fresca y terminó con código 0.

Resultado: schema46, `status=passed`, 600 frames, `regression_gate=1`, `sprite_region_crop_contract=1`, probes de dash/objetos/Suwako/Remilia aprobados y contratos viewport/cámara/BG33/BG36/BG37/BG38 aprobados. La corrida confirmó 30 draws/24 tiles BG33, 4 quads proyectados BG36, scroll de BG37 durante 2 ticks y de BG38 durante 4. El reporte completo está en [`vita3k-result.json`](../artifacts/vita3k-result.json); la captura fresca de pelea, en [`fight.bmp`](../artifacts/screenshots/fight.bmp). La captura demuestra que el build dibuja a Reimu y Cirno con el fondo de prueba; el overlay automático cubre parte de la escena, por lo que no es evidencia de paridad visual con el PC.

El VPK automático probado tiene SHA-256 `96e1782e6bdf7c5dd6a5e627d8b2b52fd1ac4e415136fc603b772815bdab6b71`. El VPK interactivo hermano tiene SHA-256 `c511fb78937fe3b12a2b686220f860420ab3729ad784c96e242730a05601b46d`. Se abrieron ambos archivos como ZIP y sus `eboot.bin` miden 96,219 bytes y coinciden exactamente, SHA-256 `d1d730c7849097d8b78a09e75ccc708b2668a9b39cf1e716c9a39abd2879fdf5`. La corrida integral usó el VPK automático; el interactivo comparte el mismo ejecutable, aunque el paquete interactivo no se instaló en esta corrida.

Comando ejecutado:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/vita3k-test.ps1 `
  -Vpk artifacts/Touhou123Vita-pat-crop-guest-auto.vpk `
  -Vita3K G:\Vita3k\Vita3K.exe -Config G:\Vita3k\config.yml `
  -VitaFS artifacts/vitafs -Frontend sdl -TimeoutSeconds 120
```

Esta prueba valida el estado actual de compilación y el alcance cubierto por el gate; no cierra la paridad total, los ataques B/C/skills de todo el roster, el round completo, todos los callbacks de escenarios ni la comparación sincronizada contra el juego de PC.
