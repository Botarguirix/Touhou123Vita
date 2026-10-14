param([string]$Frontend='sdl')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$emulator=Join-Path $root "local/vita3k-$Frontend/Vita3K.exe"
$vpk=Join-Path $root 'artifacts/Touhou123Vita.vpk'
$fs=Join-Path $root 'artifacts/vitafs'
$app=Join-Path $fs 'ux0/app/THSV12301'
if(!(Test-Path $emulator) -or !(Test-Path $vpk)){throw 'Run build and Vita3K setup/test first'}
# Preserve the test flag as evidence while keeping it out of the playable app.
$flag=Join-Path $app 'auto-test.txt'
if(Test-Path $flag){Move-Item -LiteralPath $flag -Destination (Join-Path $root "artifacts/auto-test.$([DateTime]::UtcNow.Ticks).txt")}
[System.IO.Compression.ZipFile]::ExtractToDirectory($vpk,$app,$true)
$args=@('--load-config','--keep-config','--config-location',('"'+(Join-Path $root 'artifacts/vita3k-test.yml')+'"'),'--installed-path','THSV12301','--log-level','2')
if($Frontend -eq 'sdl'){$args=@('--frontend','sdl')+$args}
# A visible window is required for the user to interact with the delivered demo.
$p=Start-Process -FilePath $emulator -ArgumentList $args -WorkingDirectory (Split-Path $emulator -Parent) -WindowStyle Normal -PassThru
Write-Output "Playable demo launched; process $($p.Id). X -> X enters practice."
