param(
 [string]$Frontend='sdl',
 [string]$Vpk='artifacts/Touhou123Vita-combat-iter.vpk',
 [string]$Vita3K
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(!(Split-Path $Vpk -IsAbsolute)){$Vpk=Join-Path $root $Vpk}
$vpkPath=(Resolve-Path -LiteralPath $Vpk).Path
$fsPath=(Resolve-Path -LiteralPath (Join-Path $root 'artifacts/vitafs')).Path
$sharedHome=$env:VITA3K_HOME
if(!$sharedHome){$sharedHome='G:\Vita3k'}
if(!$Vita3K){$Vita3K=Join-Path $sharedHome 'Vita3K.exe'}
$emulatorCopy=Join-Path $root 'local/vita3k-isolated'
$runnerExe=Join-Path $emulatorCopy 'Vita3K.exe'
if(!(Test-Path -LiteralPath $runnerExe)){
 $sharedExe=(Resolve-Path -LiteralPath $Vita3K).Path
 New-Item -ItemType Directory -Force $emulatorCopy | Out-Null
 Copy-Item -Path (Join-Path (Split-Path $sharedExe -Parent) '*') -Destination $emulatorCopy -Recurse -Force
}
$portableRoot=Join-Path $emulatorCopy 'portable'
$portableFs=Join-Path $portableRoot 'fs'
New-Item -ItemType Directory -Force $portableRoot | Out-Null
if(Test-Path -LiteralPath $portableFs){
 $item=Get-Item -LiteralPath $portableFs
 if($item.LinkType -ne 'Junction' -or (Resolve-Path -LiteralPath $item.Target).Path -ne $fsPath){throw 'The local Vita3K portable VitaFS points to a different path.'}
}else{New-Item -ItemType Junction -Path $portableFs -Target $fsPath | Out-Null}
$config=Join-Path $portableRoot 'config.yml'
if(!(Test-Path -LiteralPath $config)){
 $sourceConfig=Join-Path (Split-Path $Vita3K -Parent) 'config.yml'
 if(!(Test-Path -LiteralPath $sourceConfig)){throw "Vita3K config not found: $sourceConfig"}
 $content=Get-Content -LiteralPath $sourceConfig -Raw
 $content=$content -replace '(?m)^pref-path:.*$',('pref-path: '+$fsPath.Replace('\','/')+'/')
 $content=$content -replace '(?m)^initial-setup:.*$','initial-setup: false'
 Set-Content -LiteralPath $config -Value $content
}
$appRoot=Join-Path $fsPath 'ux0/app/THSV12301'
New-Item -ItemType Directory -Force $appRoot | Out-Null
# Keep the autostart marker out of the interactive VPK install.
$autoFlag=Join-Path $appRoot 'auto-test.txt'
if(Test-Path -LiteralPath $autoFlag){Move-Item -LiteralPath $autoFlag -Destination (Join-Path $root "artifacts/auto-test.$([DateTime]::UtcNow.Ticks).txt")}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[System.IO.Compression.ZipFile]::OpenRead($vpkPath)
try{
 $base=[System.IO.Path]::GetFullPath($appRoot)+[System.IO.Path]::DirectorySeparatorChar
 foreach($entry in $zip.Entries){
  $target=[System.IO.Path]::GetFullPath((Join-Path $appRoot $entry.FullName))
  if(!$target.StartsWith($base,[System.StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe VPK entry'}
 }
 foreach($entry in $zip.Entries){
  $target=[System.IO.Path]::GetFullPath((Join-Path $appRoot $entry.FullName))
  if($entry.FullName.EndsWith('/')){New-Item -ItemType Directory -Force $target | Out-Null;continue}
  New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
  $inputStream=$entry.Open()
  try{$outputStream=[System.IO.File]::Create($target);try{$inputStream.CopyTo($outputStream)}finally{$outputStream.Dispose()}}finally{$inputStream.Dispose()}
 }
}finally{$zip.Dispose()}
$args=@('--load-config','--keep-config','--config-location',('"'+$config+'"'),'--installed-path','THSV12301','--log-level','2')
if($Frontend -eq 'sdl'){$args=@('--frontend','sdl')+$args}
$p=Start-Process -FilePath $runnerExe -ArgumentList $args -WorkingDirectory $emulatorCopy -WindowStyle Normal -PassThru -RedirectStandardOutput (Join-Path $root 'artifacts/vita3k-play.stdout.log') -RedirectStandardError (Join-Path $root 'artifacts/vita3k-play.stderr.log')
Write-Output "Interactive VPK launched in the project-local portable Vita3K (process $($p.Id)). Press X at the menu to enter practice."
