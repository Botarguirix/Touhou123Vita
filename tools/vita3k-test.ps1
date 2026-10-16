param(
 [Parameter(Mandatory)][string]$Vita3K,
 [Parameter(Mandatory)][string]$Config,
 [Parameter(Mandatory)][string]$VitaFS,
 [Parameter(Mandatory)][string]$Vpk,
 [ValidateSet('qt','sdl')][string]$Frontend='qt',
 [int]$TimeoutSeconds=90
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$vpkPath=(Resolve-Path -LiteralPath $Vpk).Path
$fsPath=(Resolve-Path -LiteralPath $VitaFS).Path
$report=Join-Path $fsPath 'ux0/data/touhou123vita-smoke.json'
New-Item -ItemType Directory -Force (Split-Path $report -Parent) | Out-Null
foreach($scene in @('menu','practice','fight')){
 $capture=Join-Path $fsPath "ux0/data/touhou123vita-$scene.bmp"
 if(Test-Path $capture){Move-Item -LiteralPath $capture -Destination "$capture.$([DateTime]::UtcNow.Ticks).previous"}
}
# Archive stale evidence; never accept a previous run's report.
if(Test-Path $report){Move-Item -LiteralPath $report -Destination "$report.$([DateTime]::UtcNow.Ticks).previous"}
$content=Get-Content -LiteralPath $Config -Raw
$content=$content -replace '(?m)^pref-path:.*$',('pref-path: '+$fsPath.Replace('\','/')+'/')
$content=$content -replace '(?m)^initial-setup:.*$','initial-setup: false'
$testConfig=Join-Path $root 'artifacts/vita3k-test.yml'
Set-Content -LiteralPath $testConfig -Value $content
# Install the generated VPK directly in the isolated VitaFS to avoid GUI install dialogs.
$appRoot=Join-Path $fsPath 'ux0/app/THSV12301'
New-Item -ItemType Directory -Force $appRoot | Out-Null
$zip=[System.IO.Compression.ZipFile]::OpenRead($vpkPath)
try {
 foreach($entry in $zip.Entries){
  $target=[System.IO.Path]::GetFullPath((Join-Path $appRoot $entry.FullName))
  if(!$target.StartsWith([System.IO.Path]::GetFullPath($appRoot)+[System.IO.Path]::DirectorySeparatorChar)){throw 'Unsafe VPK entry'}
 }
}finally{$zip.Dispose()}
[System.IO.Compression.ZipFile]::ExtractToDirectory($vpkPath,$appRoot,$true)
# Vita3K validates -r against its default config before parsing --config-location.
# Keep a local copy of the requested emulator so its default config is isolated too.
$emulatorCopy=Join-Path $root "local/vita3k-$Frontend"
if(!(Test-Path (Join-Path $emulatorCopy 'Vita3K.exe'))){
 Copy-Item -LiteralPath (Split-Path $Vita3K -Parent) -Destination $emulatorCopy -Recurse
}
Set-Content -LiteralPath (Join-Path $emulatorCopy 'config.yml') -Value $content
$runnerExe=Join-Path $emulatorCopy 'Vita3K.exe'
$args=@('--load-config','--keep-config','--config-location',('"'+$testConfig+'"'),'--log-level','2','--installed-path','THSV12301')
if($Frontend -eq 'sdl'){$args=@('--frontend','sdl')+$args}
$started=[DateTime]::UtcNow
$p=Start-Process -FilePath $runnerExe -ArgumentList $args -WorkingDirectory $emulatorCopy -WindowStyle Hidden -PassThru -RedirectStandardOutput "$root/artifacts/vita3k-test.stdout.log" -RedirectStandardError "$root/artifacts/vita3k-test.stderr.log"
$deadline=$started.AddSeconds($TimeoutSeconds)
while([DateTime]::UtcNow -lt $deadline -and !(Test-Path $report) -and !$p.HasExited){Start-Sleep -Milliseconds 500;$p.Refresh()}
if(!(Test-Path $report)){
 if(!$p.HasExited){Stop-Process -Id $p.Id}
 throw 'Vita3K did not produce fresh guest evidence before timeout'
}
$result=Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
if($result.schema -ne 3 -or $result.status -ne 'passed' -or $result.frames -ne 600 -or !$result.menu -or !$result.practice -or !$result.fight -or !$result.jump -or $result.hits -le 0 -or $result.cpu_hp -ge $result.max_hp -or $result.external_dat -ne 7 -or $result.textures_decoded -le 2){throw 'Guest DAT/animation validation failed'}
$p.WaitForExit(5000) | Out-Null
$runtimeLog=Get-Content "$root/artifacts/vita3k-test.stdout.log" -Raw
if($runtimeLog -match 'EXCEPTION_ACCESS_VIOLATION|\|C\||Assertion failed'){throw 'Vita3K runtime logged a critical failure'}
if($p.HasExited -and $p.ExitCode -ne 0){throw "Vita3K exited with code $($p.ExitCode)"}
New-Item -ItemType Directory -Force "$root/artifacts/screenshots" | Out-Null
foreach($scene in @('menu','practice','fight')){
 $capture=Join-Path $fsPath "ux0/data/touhou123vita-$scene.bmp"
 if(!(Test-Path $capture)){throw "Guest framebuffer capture missing: $scene"}
 Copy-Item -LiteralPath $capture -Destination "$root/artifacts/screenshots/$scene.bmp" -Force
}
$result | Add-Member -NotePropertyName vpk_sha256 -NotePropertyValue (Get-FileHash $vpkPath -Algorithm SHA256).Hash.ToLowerInvariant()
$result | Add-Member -NotePropertyName started_utc -NotePropertyValue $started.ToString('o')
$result | ConvertTo-Json | Set-Content "$root/artifacts/vita3k-result.json"
$result | ConvertTo-Json
# Terminate only the child launched by this runner if emulator stays open after guest exit.
if(!$p.HasExited){Stop-Process -Id $p.Id}
