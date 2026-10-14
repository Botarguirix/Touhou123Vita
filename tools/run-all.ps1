param(
 [Parameter(Mandatory)][string]$Vita3K,
 [Parameter(Mandatory)][string]$Config,
 [Parameter(Mandatory)][string]$VitaFS,
 [string]$Distribution='Ubuntu',
 [string]$VitaSDK='/home/bota/vitasdk',
 [string]$Frontend='sdl'
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(!(Test-Path "$root/assets/font.rgba")){throw 'Generate font/assets first; see README'}
& wsl -d $Distribution --cd $root -- env "VITASDK=$VitaSDK" bash tools/build.sh
if($LASTEXITCODE -ne 0){throw 'Host/Vita build or tests failed'}
& wsl -d $Distribution --cd $root -- env "VITASDK=$VitaSDK" cmake -S . -B build-vita-auto -DT123_VITA=ON -DT123_AUTOTEST=ON -DCMAKE_BUILD_TYPE=Release
if($LASTEXITCODE -ne 0){throw 'Automatic VPK configure failed'}
& wsl -d $Distribution --cd $root -- env "VITASDK=$VitaSDK" cmake --build build-vita-auto -j2
if($LASTEXITCODE -ne 0){throw 'Automatic VPK build failed'}
& "$PSScriptRoot/vita3k-test.ps1" -Vita3K $Vita3K -Config $Config -VitaFS $VitaFS -Vpk "$root/build-vita-auto/Touhou123Vita.vpk" -Frontend $Frontend
