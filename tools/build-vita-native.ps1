param(
    [Parameter(Mandatory)][string]$Output,
    [string]$VitaSDK=$env:VITASDK,
    [switch]$AutoTest
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(!$VitaSDK){throw 'Set VITASDK or pass -VitaSDK'}
$cc=Join-Path $VitaSDK 'bin/arm-vita-eabi-gcc.exe'
$ar=Join-Path $VitaSDK 'bin/arm-vita-eabi-ar.exe'
foreach($tool in @($cc,$ar,'vita-elf-create.exe','vita-make-fself.exe','vita-mksfoex.exe','vita-pack-vpk.exe')){
    $path=if([IO.Path]::IsPathRooted($tool)){$tool}else{Join-Path $VitaSDK "bin/$tool"}
    if(!(Test-Path -LiteralPath $path)){throw "Missing VitaSDK tool: $path"}
}
$mode=if($AutoTest){'auto'}else{'interactive'}
$build=Join-Path $root "artifacts/manual-vita-$mode"
New-Item -ItemType Directory -Force $build | Out-Null
$include=Join-Path $root 'include';$source=Join-Path $root 'src'
$coreNames=@('core.c','fight.c','animation.c','resources.c','pattern.c','input.c');$objects=@()
foreach($name in $coreNames){
    $object=Join-Path $build ($name+'.o')
    & $cc '-I' $include '-O3' '-DNDEBUG' '-std=gnu11' '-Wall' '-Wextra' '-Werror' '-c' (Join-Path $source $name) '-o' $object
    if($LASTEXITCODE -ne 0){throw "Core compile failed: $name"};$objects+=,$object
}
$library=Join-Path $build 'libt123_core.a';& $ar rcs $library @objects
if($LASTEXITCODE -ne 0){throw 'Core archive failed'}
$mainObject=Join-Path $build 'vita_main.c.o';& $cc '-I' $include '-O3' '-DNDEBUG' '-std=gnu11' '-c' (Join-Path $source 'vita_main.c') '-o' $mainObject
if($LASTEXITCODE -ne 0){throw 'Vita application compile failed'}
$rendererObject=Join-Path $build 'soft2d.c.o';& $cc '-I' $include '-O3' '-DNDEBUG' '-std=gnu11' '-c' (Join-Path $source 'soft2d.c') '-o' $rendererObject
if($LASTEXITCODE -ne 0){throw 'Renderer compile failed'}
$elf=Join-Path $build 'touhou123vita';& $cc '-Wl,-q' '-O3' '-DNDEBUG' '-Wl,-z,nocopyreloc' $mainObject $rendererObject '-o' $elf $library '-lSceDisplay_stub' '-lSceSysmem_stub' '-lSceCtrl_stub' '-lm'
if($LASTEXITCODE -ne 0){throw 'Vita link failed'}
$velf=Join-Path $build 'touhou123vita.velf';& (Join-Path $VitaSDK 'bin/vita-elf-create.exe') $elf $velf
if($LASTEXITCODE -ne 0){throw 'vita-elf-create failed'}
$self=Join-Path $build 'touhou123vita.self';& (Join-Path $VitaSDK 'bin/vita-make-fself.exe') '-c' $velf $self
if($LASTEXITCODE -ne 0){throw 'vita-make-fself failed'}
$sfo=Join-Path $build 'param.sfo';& (Join-Path $VitaSDK 'bin/vita-mksfoex.exe') '-s' 'APP_VER=00.01' '-s' 'TITLE_ID=THSV12301' 'Touhou123Vita Prototype' $sfo
if($LASTEXITCODE -ne 0){throw 'vita-mksfoex failed'}
$vpk=(Resolve-Path -LiteralPath (Split-Path $Output -Parent)).Path
$vpk=Join-Path $vpk (Split-Path $Output -Leaf)
$packArgs=@('-a',((Join-Path $root 'assets/font.rgba')+'=assets/font.rgba'))
if($AutoTest){$packArgs+=@('-a',((Join-Path $root 'tests/auto-test.txt')+'=auto-test.txt'))}
$packArgs+=@('-s',$sfo,'-b',$self,$vpk)
& (Join-Path $VitaSDK 'bin/vita-pack-vpk.exe') @packArgs
if($LASTEXITCODE -ne 0){throw 'VPK packaging failed'}
Get-FileHash -LiteralPath $vpk -Algorithm SHA256 | Format-List
Get-Item -LiteralPath $vpk | Select-Object FullName,Length,LastWriteTime
