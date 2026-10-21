param(
    [string]$VitaSDK='C:\vitasdk',
    [string]$Vita3K='G:\Vita3k\Vita3K.exe',
    [string]$VitaFS=(Join-Path (Split-Path $PSScriptRoot -Parent) 'artifacts/vitafs'),
    [ValidateSet('qt','sdl')][string]$Frontend='sdl',
    [int]$TimeoutSeconds=240
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$cc=Join-Path $VitaSDK 'bin/arm-vita-eabi-gcc.exe'
$ar=Join-Path $VitaSDK 'bin/arm-vita-eabi-ar.exe'
$build=Join-Path $root 'artifacts/manual-vita-pat-audit'
New-Item -ItemType Directory -Force $build | Out-Null
$core=@('core.c','fight.c','animation.c','resources.c','pattern.c')
$objects=@()
foreach($name in $core){
    $object=Join-Path $build ($name+'.o')
    & $cc '-I' (Join-Path $root 'legacy/include') '-O3' '-DNDEBUG' '-std=gnu11' '-Wall' '-Wextra' '-Werror' '-c' (Join-Path $root "legacy/src/$name") '-o' $object
    if($LASTEXITCODE -ne 0){throw "Core compile failed: $name"}
    $objects+=,$object
}
$library=Join-Path $build 'libt123_core.a'
& $ar rcs $library @objects
if($LASTEXITCODE -ne 0){throw 'Core archive failed'}
$probe=Join-Path $build 'resource_probe.o'
& $cc '-I' (Join-Path $root 'legacy/include') '-O3' '-DNDEBUG' '-std=gnu11' '-Wno-misleading-indentation' '-Dmain=t123_resource_probe_main' '-c' (Join-Path $root 'legacy/tests/resource_probe.c') '-o' $probe
if($LASTEXITCODE -ne 0){throw 'Resource probe compile failed'}
$runner=Join-Path $build 'pat_image_audit_main.o'
& $cc '-O3' '-DNDEBUG' '-std=gnu11' '-c' (Join-Path $PSScriptRoot 'pat_image_audit_main.c') '-o' $runner
if($LASTEXITCODE -ne 0){throw 'Audit runner compile failed'}
$elf=Join-Path $build 'pat_image_audit'
& $cc '-Wl,-q' '-O3' '-DNDEBUG' '-Wl,-z,nocopyreloc' $runner $probe '-o' $elf $library '-lm'
if($LASTEXITCODE -ne 0){throw 'Audit runner link failed'}
$velf=Join-Path $build 'pat_image_audit.velf'
& (Join-Path $VitaSDK 'bin/vita-elf-create.exe') $elf $velf
if($LASTEXITCODE -ne 0){throw 'vita-elf-create failed'}
$self=Join-Path $build 'pat_image_audit.self'
& (Join-Path $VitaSDK 'bin/vita-make-fself.exe') '-c' $velf $self
if($LASTEXITCODE -ne 0){throw 'vita-make-fself failed'}
$sfo=Join-Path $build 'param.sfo'
& (Join-Path $VitaSDK 'bin/vita-mksfoex.exe') '-s' 'APP_VER=00.01' '-s' 'TITLE_ID=THSAUD01' 'Touhou PAT Image Audit' $sfo
if($LASTEXITCODE -ne 0){throw 'vita-mksfoex failed'}
$vpk=Join-Path $root 'artifacts/Touhou123Vita-pat-image-audit.vpk'
& (Join-Path $VitaSDK 'bin/vita-pack-vpk.exe') '-s' $sfo '-b' $self $vpk
if($LASTEXITCODE -ne 0){throw 'Audit VPK packaging failed'}

$fs=(Resolve-Path -LiteralPath $VitaFS).Path
$app=Join-Path $fs 'ux0/app/THSAUD01'
New-Item -ItemType Directory -Force $app | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[IO.Compression.ZipFile]::OpenRead($vpk)
try{
    $base=[IO.Path]::GetFullPath($app)+[IO.Path]::DirectorySeparatorChar
    foreach($entry in $zip.Entries){
        $target=[IO.Path]::GetFullPath((Join-Path $app $entry.FullName))
        if(!$target.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe VPK entry'}
    }
    foreach($entry in $zip.Entries){
        $target=[IO.Path]::GetFullPath((Join-Path $app $entry.FullName))
        if($entry.FullName.EndsWith('/')){New-Item -ItemType Directory -Force $target | Out-Null;continue}
        New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
        $inputStream=$entry.Open()
        try{$outputStream=[IO.File]::Create($target);try{$inputStream.CopyTo($outputStream)}finally{$outputStream.Dispose()}}finally{$inputStream.Dispose()}
    }
}finally{$zip.Dispose()}

$fsReport=Join-Path $fs 'ux0/data/touhou123vita-pat-image-decode.tsv'
$fsSummary=Join-Path $fs 'ux0/data/touhou123vita-pat-image-decode-summary.txt'
foreach($path in @($fsReport,$fsSummary)){if(Test-Path $path){Move-Item -LiteralPath $path -Destination "$path.$([DateTime]::UtcNow.Ticks).previous"}}
$isolated=Join-Path $root 'local/vita3k-isolated'
$runnerExe=Join-Path $isolated 'Vita3K.exe'
if(!(Test-Path $runnerExe)){throw "Project-local Vita3K missing: $runnerExe"}
$config=Join-Path $isolated 'portable/config.yml'
if(!(Test-Path $config)){throw "Project-local Vita3K config missing: $config"}
$configText=Get-Content $config -Raw
$configText=$configText -replace '(?m)^pref-path:.*$',('pref-path: '+$fs.Replace('\','/')+'/')
Set-Content -LiteralPath $config -Value $configText
# Stop only a process owned by this project-local Vita3K copy before using its VitaFS.
$runnerFull=[IO.Path]::GetFullPath($runnerExe)
Get-Process Vita3K -ErrorAction SilentlyContinue | Where-Object { $_.Path -and [IO.Path]::GetFullPath($_.Path) -eq $runnerFull } | Stop-Process
$stdout=Join-Path $root 'artifacts/pat-image-audit-vita3k.stdout.log'
$stderr=Join-Path $root 'artifacts/pat-image-audit-vita3k.stderr.log'
$arguments=@('--load-config','--keep-config','--config-location',('"'+$config+'"'),'--log-level','2','--installed-path','THSAUD01')
if($Frontend -eq 'sdl'){$arguments=@('--frontend','sdl')+$arguments}
$process=Start-Process -FilePath $runnerExe -ArgumentList $arguments -WorkingDirectory $isolated -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
$deadline=[DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
while([DateTime]::UtcNow -lt $deadline -and !$process.HasExited){Start-Sleep -Milliseconds 500;$process.Refresh()}
if(!$process.HasExited){Stop-Process -Id $process.Id;throw "Vita3K audit exceeded ${TimeoutSeconds}s; partial output preserved at $fsReport"}
$process.Refresh()
if($process.ExitCode -ne 0){throw "Vita3K audit guest exited with code $($process.ExitCode). Logs: $stdout, $stderr"}
if(!(Test-Path $fsReport)){throw "Vita3K audit produced no report. Logs: $stdout, $stderr"}
Copy-Item -LiteralPath $fsReport -Destination (Join-Path $root 'artifacts/pat-image-decode.tsv') -Force
$summaryLine=Get-Content (Join-Path $root 'artifacts/pat-image-decode.tsv') -Tail 1
if($summaryLine -notmatch '^# summary pats=\d+ images=\d+ decoded=\d+ unreferenced=\d+ missing_resource=\d+ missing_palette=\d+ unsupported_or_invalid=\d+$'){throw 'Audit TSV is missing its terminal summary row'}
Set-Content -LiteralPath (Join-Path $root 'artifacts/pat-image-decode-summary.txt') -Value $summaryLine
Get-FileHash $vpk -Algorithm SHA256 | Select-Object Hash,Path
Get-Item (Join-Path $root 'artifacts/pat-image-decode.tsv') | Select-Object Length,LastWriteTime
Get-Content (Join-Path $root 'artifacts/pat-image-decode-summary.txt')
