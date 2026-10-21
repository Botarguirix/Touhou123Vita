# Instrucciones para agentes (Codex)

Proyecto: port de **Touhou 12.3 Hisoutensoku 1.10a** a PS Vita por **recompilación estática** del ejecutable original (x86 → C → ARM). Lee primero [docs/ROADMAP_RECOMP.md](docs/ROADMAP_RECOMP.md) y [docs/PE_INVENTORY.md](docs/PE_INVENTORY.md). Las tareas asignadas a Codex están en [docs/CODEX_TAREAS.md](docs/CODEX_TAREAS.md).

## Reparto con Claude

- Claude trabaja en el checkout principal y es dueño de `recomp/` (descubrimiento de funciones, lifter, runtime, capas de plataforma), de `docs/ROADMAP_RECOMP.md`, `docs/PE_INVENTORY.md`, `README.md`, `AGENTS.md` y `CMakeLists.txt`.
- Cada tarea de Codex indica **los únicos archivos que puede crear o editar**. Si necesitas cambiar otro archivo, no lo cambies: explícalo en el informe final.
- `legacy/` está congelado. Solo se toca si la tarea lo dice expresamente.

## Entorno (Windows, PowerShell 7)

| Herramienta | Ruta |
|---|---|
| git (no está en PATH) | `C:\Users\Andy PC\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe` |
| Python 3.12 | `python` (pefile, capstone y unicorn se cargan desde `local/python-deps`; ver `tools/disassemble_pe_windows.py`) |
| GCC host | `C:\msys64\ucrt64\bin\gcc.exe` |
| VitaSDK | `C:\vitasdk` (`$env:VITASDK`) |
| Ghidra 12.1.4 / JDK 21 | `C:\Users\Andy PC\Documents\Chatgpt\VaganteVita\_local\toolchain\` (el proyecto es del usuario `ikari`: `JAVA_TOOL_OPTIONS=-Duser.name=ikari`; ver `tools/export-functions.ps1`) |
| Vita3K | `local/vita3k-isolated` (ver `tools/vita3k-test.ps1`) |

Checkout principal: `C:\Users\Andy PC\Documents\Chatgpt\Touhou_123\Touhou123Vita`.

## Cómo empezar una tarea (worktree propio)

Trabaja siempre en un worktree aparte para no pisar el checkout de Claude. `original/`, `local/` y `artifacts/` están en `.gitignore`, así que se enlazan con junctions:

```powershell
$git = "C:\Users\Andy PC\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe"
$main = "C:\Users\Andy PC\Documents\Chatgpt\Touhou_123\Touhou123Vita"
$n = "T1"   # número de la tarea
$wt = "C:\Users\Andy PC\Documents\Chatgpt\Touhou_123\codex-$n"
& $git -C $main worktree add -b "codex/$n" $wt main
foreach ($d in 'original','local','artifacts') { New-Item -ItemType Junction -Path "$wt\$d" -Target "$main\$d" | Out-Null }
Set-Location $wt
```

Al terminar: commit **solo** de tus archivos en la rama `codex/<n>` con el mensaje `codex <n>: <resumen>`. **No hagas push, merge ni rebase**, y no borres el worktree: Claude lo revisa e integra.

## Reglas fijas

1. **Nada comercial en git**: ni el `.exe`, ni DAT, ni recursos extraídos, ni pseudocódigo o desensamblado completo, ni shaders o blobs extraídos, ni el C generado. Esas salidas van a `artifacts/...` (ignorado). En `docs/` solo van metadatos agregados: conteos, direcciones, nombres, conclusiones.
2. Toda herramienta que lea el PE verifica su SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e` y falla si no coincide.
3. Las herramientas siguen el estilo de `tools/`: Python 3 con `argparse`, sin dependencias nuevas fuera de `local/python-deps`, y salida reproducible (orden estable, sin marcas de tiempo).
4. Cada herramienta nueva lleva una prueba `tests/test_<nombre>.py`. Si la prueba necesita el PE, debe saltarse (`skipUnless`) cuando falte `original/th123.exe`.
5. **No inventes resultados.** Si algo no se pudo verificar, dilo en el informe con el motivo. Distingue lo medido de lo inferido.
6. La documentación se escribe en español.

## Informe final (obligatorio)

Al terminar, responde con:

- rama y commit;
- archivos creados o editados;
- comandos de verificación ejecutados y su resultado literal (pasó o falló);
- hallazgos, con direcciones y nivel de confianza;
- dudas y cosas que quedaron sin verificar.
