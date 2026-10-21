param(
 [string]$Vita3K,
 [string]$Config,
 [string]$VitaFS,
 [Parameter(Mandatory)][string]$Vpk,
 [ValidateSet('qt','sdl')][string]$Frontend='sdl',
 [int]$TimeoutSeconds=90
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(!$Vita3K){
 $sharedVita3K=$env:VITA3K_HOME
 if(!$sharedVita3K){$sharedVita3K='G:\Vita3k'}
 $Vita3K=Join-Path $sharedVita3K 'Vita3K.exe'
}
if(!$Config){$Config=Join-Path (Split-Path -Parent $Vita3K) 'config.yml'}
if(!$VitaFS){$VitaFS=Join-Path $root 'artifacts/vitafs'}
$vpkPath=(Resolve-Path -LiteralPath $Vpk).Path
$fsPath=(Resolve-Path -LiteralPath $VitaFS).Path
$report=Join-Path $fsPath 'ux0/data/touhou123vita-smoke.json'
$bcReport=Join-Path $fsPath 'ux0/data/touhou123vita-bc-natural.tsv'
New-Item -ItemType Directory -Force (Split-Path $report -Parent) | Out-Null
# Retain the current run's evidence and discard only archived copies from older
# executions; these captures are regenerated below and otherwise grow without bound.
Get-ChildItem -LiteralPath (Split-Path $report -Parent) -File -Filter 'touhou123vita-*.bmp.*.previous' -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -LiteralPath (Split-Path $report -Parent) -File -Filter 'touhou123vita-smoke.json.*.previous' -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -LiteralPath (Split-Path $report -Parent) -File -Filter 'touhou123vita-bc-natural.tsv.*.previous' -ErrorAction SilentlyContinue | Remove-Item -Force
foreach($scene in @('menu','gallery','stage','stage-assets','stage-layout','stage-bg02-segment','stage-bg12-assets','stage-bg12-layout','stage-bg33-assets','stage-bg33-layout','stage-bg33-scroll','stage-bg36-assets','stage-bg36-layout','stage-bg37-assets','stage-bg37-scroll','stage-bg38-assets','stage-bg38-scroll','practice','fight','fight-bg36','fight-natural-a','object-probe')){
 $capture=Join-Path $fsPath "ux0/data/touhou123vita-$scene.bmp"
 if(Test-Path $capture){Move-Item -LiteralPath $capture -Destination "$capture.$([DateTime]::UtcNow.Ticks).previous"}
}
# Archive stale evidence; never accept a previous run's report.
if(Test-Path $report){Move-Item -LiteralPath $report -Destination "$report.$([DateTime]::UtcNow.Ticks).previous"}
if(Test-Path $bcReport){Move-Item -LiteralPath $bcReport -Destination "$bcReport.$([DateTime]::UtcNow.Ticks).previous"}
$content=Get-Content -LiteralPath $Config -Raw
$portableRoot=Join-Path (Join-Path $root 'local/vita3k-isolated') 'portable'
$portableFs=Join-Path $portableRoot 'fs'
$content=$content -replace '(?m)^pref-path:.*$',('pref-path: '+$portableFs.Replace('\','/')+'/')
$content=$content -replace '(?m)^initial-setup:.*$','initial-setup: false'
$testConfig=Join-Path $root 'artifacts/vita3k-test.yml'
Set-Content -LiteralPath $testConfig -Value $content
# Install the generated VPK directly in the isolated VitaFS to avoid GUI install dialogs.
$appRoot=Join-Path $fsPath 'ux0/app/THSV12301'
New-Item -ItemType Directory -Force $appRoot | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[System.IO.Compression.ZipFile]::OpenRead($vpkPath)
try {
 foreach($entry in $zip.Entries){
  $target=[System.IO.Path]::GetFullPath((Join-Path $appRoot $entry.FullName))
  if(!$target.StartsWith([System.IO.Path]::GetFullPath($appRoot)+[System.IO.Path]::DirectorySeparatorChar)){throw 'Unsafe VPK entry'}
 }
 foreach($entry in $zip.Entries){
  $target=[System.IO.Path]::GetFullPath((Join-Path $appRoot $entry.FullName))
  if($entry.FullName.EndsWith('/')){New-Item -ItemType Directory -Force $target | Out-Null;continue}
  New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
  $inputStream=$entry.Open()
  try{$outputStream=[System.IO.File]::Create($target);try{$inputStream.CopyTo($outputStream)}finally{$outputStream.Dispose()}}finally{$inputStream.Dispose()}
 }
}finally{$zip.Dispose()}
# Vita3K portable mode keeps configuration, logs, and VitaFS under this local
# copy. A junction reuses the project's isolated VitaFS without duplicating it.
$emulatorCopy=Join-Path $root 'local/vita3k-isolated'
$sharedExe=(Resolve-Path -LiteralPath $Vita3K).Path
$runnerExe=Join-Path $emulatorCopy 'Vita3K.exe'
$syncEmulator=!(Test-Path $runnerExe)
if(!$syncEmulator){$syncEmulator=(Get-FileHash -LiteralPath $sharedExe -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $runnerExe -Algorithm SHA256).Hash}
if($syncEmulator){
 New-Item -ItemType Directory -Force $emulatorCopy | Out-Null
 Copy-Item -Path (Join-Path (Split-Path $sharedExe -Parent) '*') -Destination $emulatorCopy -Recurse -Force
}
New-Item -ItemType Directory -Force $portableRoot | Out-Null
if(Test-Path -LiteralPath $portableFs){
 $portableFsItem=Get-Item -LiteralPath $portableFs
 if($portableFsItem.LinkType -ne 'Junction'){throw "Portable VitaFS path exists and is not a junction: $portableFs"}
 $existingFs=(Resolve-Path -LiteralPath $portableFsItem.Target).Path
 if($existingFs -ne $fsPath){throw "Portable VitaFS already points elsewhere: $existingFs"}
}else{
 New-Item -ItemType Junction -Path $portableFs -Target $fsPath | Out-Null
}
$testConfig=Join-Path $portableRoot 'config.yml'
Set-Content -LiteralPath (Join-Path $emulatorCopy 'config.yml') -Value $content
Set-Content -LiteralPath $testConfig -Value $content
$portableData=Join-Path $portableFs 'ux0/data'
New-Item -ItemType Directory -Force $portableData | Out-Null
foreach($dataFile in @('th123a.dat','th123b.dat','th123c.dat')){
 $sourceData=Join-Path $fsPath "ux0/data/touhou123vita/$dataFile"
 if(!(Test-Path -LiteralPath $sourceData)){throw "Required game data file is missing: $sourceData"}
 Copy-Item -LiteralPath $sourceData -Destination (Join-Path $portableData $dataFile) -Force
}
$args=@('--load-config','--keep-config','--config-location',('"'+$testConfig+'"'),'--log-level','2','-r','THSV12301')
if($Frontend -eq 'sdl'){$args=$args+@('--frontend','sdl')}
$started=[DateTime]::UtcNow
$p=Start-Process -FilePath $runnerExe -ArgumentList $args -WorkingDirectory $emulatorCopy -WindowStyle Hidden -PassThru -RedirectStandardOutput "$root/artifacts/vita3k-test.stdout.log" -RedirectStandardError "$root/artifacts/vita3k-test.stderr.log"
$deadline=$started.AddSeconds($TimeoutSeconds)
while([DateTime]::UtcNow -lt $deadline -and !(Test-Path $report) -and !$p.HasExited){Start-Sleep -Milliseconds 500;$p.Refresh()}
if(!(Test-Path $report) -and !$p.HasExited){
 $portableLog=Join-Path $portableRoot 'vita3k.log'
 if(Test-Path $portableLog){
  $logText=Get-Content -LiteralPath $portableLog -Raw
  if($logText -match 'Opening file ux0:/data/touhou123vita/th123a.dat' -and $logText -match 'Opening file app0:/auto-test.txt'){
   $extendedDeadline=[DateTime]::UtcNow.AddSeconds(180)
   while([DateTime]::UtcNow -lt $extendedDeadline -and !(Test-Path $report) -and !$p.HasExited){Start-Sleep -Milliseconds 500;$p.Refresh()}
  }
 }
}if(!(Test-Path $report)){
 if(!$p.HasExited){Stop-Process -Id $p.Id}
 $exitDetail=if($p.HasExited){"process exited with code $($p.ExitCode)"}else{'process was stopped at timeout'}
 $stderr=Get-Content -LiteralPath "$root/artifacts/vita3k-test.stderr.log" -Raw -ErrorAction SilentlyContinue
 throw "Vita3K did not produce fresh guest evidence; $exitDetail. stderr: $stderr"
}
$result=Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
if($result.arena_spawn_contract -ne 1){throw 'Guest PAT round-start positions/camera do not match the recovered reset'}
if($result.udonge_409_contract -ne 1){throw 'Guest dedicated Udonge 409:1 first-pose contact contract failed'}
if($result.battle_stage_selected_interactively -ne 1){throw "Guest practice stage selector failed (selected=$($result.battle_stage_selected_interactively)); report and screenshots were saved"}
if($result.suika_623c_probe -ne 1 -or $result.suika_623c_action_seen -ne 1 -or $result.suika_623c_skill_uses -ne 1 -or $result.suika_623c_hit_delta -ne 1000 -or $result.suika_623c_level5_hit_delta -ne 500 -or $result.suika_623c_level9_action_seen -ne 1 -or $result.suika_623c_531_hit_delta -ne 800 -or $result.suika_623c_531_objects -ne 2 -or $result.suika_623c_route_mask -ne 31){throw "Guest Suika 623C/PAT gate failed (probe=$($result.suika_623c_probe), action=$($result.suika_623c_action_seen), uses=$($result.suika_623c_skill_uses), damage=$($result.suika_623c_hit_delta), projectileDamage=$($result.suika_623c_531_hit_delta), objects=$($result.suika_623c_531_objects), routeMask=$($result.suika_623c_route_mask)); report saved"}
if($result.suika_623b_probe -ne 1 -or $result.suika_623b_route_mask -ne 127 -or $result.suika_623b_hit_delta -ne 1000 -or $result.suika_623b_level5_hit_delta -ne 500 -or $result.suika_623b_level9_action_seen -ne 1 -or $result.suika_623b_level9_hit_delta -ne 800 -or $result.suika_623b_level9_objects -ne 1 -or [math]::Abs([double]$result.suika_623b_level9_object_x-350.62018) -gt 0.01 -or [math]::Abs([double]$result.suika_623b_level9_object_y-81.13174) -gt 0.01){throw "Guest Suika 623B PAT/reaction gate failed (probe=$($result.suika_623b_probe), routeMask=$($result.suika_623b_route_mask), damage=$($result.suika_623b_hit_delta), level5Damage=$($result.suika_623b_level5_hit_delta), level9Action=$($result.suika_623b_level9_action_seen), level9Damage=$($result.suika_623b_level9_hit_delta), level9Objects=$($result.suika_623b_level9_objects), object=[$($result.suika_623b_level9_object_x),$($result.suika_623b_level9_object_y)]); report saved"}
$bg36LargeExpected=-400.0;$bg36SmallExpected=-300.0
for($i=0;$i -lt $result.stage_bg36_scroll_ticks;$i++){
 $bg36LargeExpected-=1.5;if($bg36LargeExpected -lt -1200.0){$bg36LargeExpected=800.0}
 $bg36SmallExpected-=1.0;if($bg36SmallExpected -lt -800.0){$bg36SmallExpected=800.0}
}
$bg36LargeExpected=[math]::Truncate($bg36LargeExpected)
$bg36SmallExpected=[math]::Truncate(320.0+$bg36SmallExpected)
$battleBg36LargeExpected=-400.0;$battleBg36SmallExpected=-300.0
for($i=0;$i -lt $result.battle_bg36_updates;$i++){
 $battleBg36LargeExpected-=1.5;if($battleBg36LargeExpected -lt -1200.0){$battleBg36LargeExpected=800.0}
 $battleBg36SmallExpected-=1.0;if($battleBg36SmallExpected -lt -800.0){$battleBg36SmallExpected=800.0}
}
foreach($stage in @('bg37','bg38')){
 $largeExpected=-400.0;$smallExpected=-300.0
 $ticksProperty='stage_'+$stage+'_scroll_ticks'
 if($stage -eq 'bg37'){$largeProperty='stage_bg37_tori1_x';$smallProperty='stage_bg37_clowd_l_x'}
 else{$largeProperty='stage_bg38_cloud_l_x';$smallProperty='stage_bg38_cloud_s_x'}
 $ticks=[int]$result.PSObject.Properties[$ticksProperty].Value
 for($i=0;$i -lt $ticks;$i++){
  $largeExpected-=1.5;if($largeExpected -lt -1200.0){$largeExpected=800.0}
  $smallExpected-=1.0;if($smallExpected -lt -800.0){$smallExpected=800.0}
 }
 $largeActual=[double]$result.PSObject.Properties[$largeProperty].Value;$smallActual=[double]$result.PSObject.Properties[$smallProperty].Value
 if([math]::Abs($largeActual-$largeExpected) -gt 0.01 -or [math]::Abs($smallActual-$smallExpected) -gt 0.01){
  throw "$stage cloud update diverged: ticks=$ticks, actual=$largeActual/$smallActual, expected=$largeExpected/$smallExpected"
 }
}
if([double]::IsNaN([double]$result.battle_bg36_capture_camera_x) -or [double]::IsInfinity([double]$result.battle_bg36_capture_camera_x) -or [double]::IsNaN([double]$result.battle_bg36_capture_camera_y) -or [double]::IsInfinity([double]$result.battle_bg36_capture_camera_y) -or [double]::IsNaN([double]$result.battle_bg36_capture_camera_zoom) -or [double]::IsInfinity([double]$result.battle_bg36_capture_camera_zoom) -or [double]$result.battle_bg36_capture_camera_zoom -lt 0.5 -or [double]$result.battle_bg36_capture_camera_zoom -gt 1.01){ throw "BG36 capture camera is invalid: x=$($result.battle_bg36_capture_camera_x), y=$($result.battle_bg36_capture_camera_y), zoom=$($result.battle_bg36_capture_camera_zoom)" }
if([math]::Abs([double]$result.battle_bg36_clowd_l_x-$battleBg36LargeExpected) -gt 0.01 -or [math]::Abs([double]$result.battle_bg36_clowd_s_x-$battleBg36SmallExpected) -gt 0.01){
 throw "Battle BG36 cloud update diverged: updates=$($result.battle_bg36_updates), actual=$($result.battle_bg36_clowd_l_x)/$($result.battle_bg36_clowd_s_x), expected=$battleBg36LargeExpected/$battleBg36SmallExpected"
}
$p.WaitForExit(5000) | Out-Null
$p.Refresh()
$runtimeLog=Get-Content "$root/artifacts/vita3k-test.stdout.log" -Raw
New-Item -ItemType Directory -Force "$root/artifacts/screenshots" | Out-Null
foreach($scene in @('menu','gallery','stage','stage-assets','stage-layout','stage-bg02-segment','stage-bg12-assets','stage-bg12-layout','stage-bg33-assets','stage-bg33-layout','stage-bg33-scroll','stage-bg36-assets','stage-bg36-layout','stage-bg37-assets','stage-bg37-scroll','stage-bg38-assets','stage-bg38-scroll','practice','fight','fight-bg36','fight-natural-a','object-probe')){
 $capture=Join-Path $fsPath "ux0/data/touhou123vita-$scene.bmp"
 if(!(Test-Path $capture)){throw "Guest framebuffer capture missing: $scene"}
 Copy-Item -LiteralPath $capture -Destination "$root/artifacts/screenshots/$scene.bmp" -Force
}
if(!(Test-Path -LiteralPath $bcReport)){throw 'Guest natural B/C diagnostic is missing'}
Copy-Item -LiteralPath $bcReport -Destination "$root/artifacts/roster-bc-natural.tsv" -Force
$bg36Capture=Join-Path $root 'artifacts/screenshots/fight-bg36.bmp'
if((Test-Path $bg36Capture) -and (Test-Path (Join-Path $fsPath 'ux0/data/touhou123vita-fight-bg36.bmp'))){
 $bmp=[IO.File]::ReadAllBytes((Join-Path $fsPath 'ux0/data/touhou123vita-fight-bg36.bmp'))
 if($bmp.Length -lt 54 -or $bmp[0] -ne 0x42 -or $bmp[1] -ne 0x4d){throw 'BG36 capture is not a valid BMP'}
 $pixelBytes=0;for($i=54;$i -lt $bmp.Length;$i+=97){if($bmp[$i] -ne 0 -or $bmp[$i+1] -ne 0 -or $bmp[$i+2] -ne 0){$pixelBytes++}}
 if($pixelBytes -lt 100){throw "BG36 framebuffer capture is blank ($pixelBytes sampled non-black pixels)"}
 # Check actual output pixels: world sprites must not paint the 4:3 side bars.
 $pixelOffset=[BitConverter]::ToInt32($bmp,10)
 if([BitConverter]::ToInt32($bmp,18) -ne 960 -or [math]::Abs([BitConverter]::ToInt32($bmp,22)) -ne 544 -or [BitConverter]::ToInt16($bmp,28) -ne 24){throw 'Unexpected BG36 capture dimensions or format'}
 for($y=0;$y -lt 544;$y++){
  foreach($start in @(0,843)){
   for($x=$start;$x -lt $start+117;$x++){
    $offset=$pixelOffset+($y*960+$x)*3
    if($bmp[$offset] -ne 0 -or $bmp[$offset+1] -ne 0 -or $bmp[$offset+2] -ne 0){throw "BG36 draw escaped the fitted 4:3 canvas at ($x,$y)"}
   }
  }
 }
}
$bcRows=Import-Csv -LiteralPath $bcReport -Delimiter "`t"
$remiliaC=$bcRows | Where-Object {$_.character -eq 'remilia'} | Select-Object -First 1
if(!$remiliaC -or $remiliaC.c_candidates -ne '0x04' -or $remiliaC.c_hit_action -ne '412' -or $remiliaC.c_hit_frame -ne '16' -or $remiliaC.c_damage -ne '120' -or $remiliaC.c_source -ne '801' -or $remiliaC.c_pose -ne '1'){
 throw "Remilia 2C/object801 regression failed (candidates=$($remiliaC.c_candidates), action=$($remiliaC.c_hit_action), frame=$($remiliaC.c_hit_frame), damage=$($remiliaC.c_damage), source=$($remiliaC.c_source), pose=$($remiliaC.c_pose)); report saved to artifacts/roster-bc-natural.tsv"
}
$suikaMotionC=$bcRows | Where-Object {$_.character -eq 'suika'} | Select-Object -First 1
if(!$suikaMotionC -or $suikaMotionC.motion_c_base_action -ne '521' -or $suikaMotionC.motion_c_base_damage -ne '1000' -or $suikaMotionC.motion_c_level5_action -ne '526' -or $suikaMotionC.motion_c_level5_damage -ne '500' -or $suikaMotionC.motion_c_level9_action -ne '531' -or $suikaMotionC.motion_c_level9_damage -ne '800'){
 throw "Suika motion-C inventory failed (base=$($suikaMotionC.motion_c_base_action)/$($suikaMotionC.motion_c_base_damage), level5=$($suikaMotionC.motion_c_level5_action)/$($suikaMotionC.motion_c_level5_damage), level9=$($suikaMotionC.motion_c_level9_action)/$($suikaMotionC.motion_c_level9_damage)); report saved to artifacts/roster-bc-natural.tsv"
}
$udongeB=$bcRows | Where-Object {$_.character -eq 'udonge'} | Select-Object -First 1
# The natural sweep first hits with 408:1 on its command update. The dedicated
# 409:1 contract above preserves aerial-B coverage independently of route order.
if(!$udongeB -or $udongeB.b_reached_mask -ne '0x20' -or $udongeB.b_408_variant -ne '1' -or $udongeB.b_409_variant -ne '1' -or $udongeB.b_hit_action -ne '408' -or $udongeB.b_hit_frame -ne '0' -or $udongeB.b_damage -ne '800'){
 throw "Udonge first B contact failed (reached=$($udongeB.b_reached_mask), variant=$($udongeB.b_408_variant), action=$($udongeB.b_hit_action), frame=$($udongeB.b_hit_frame), damage=$($udongeB.b_damage)); report saved to artifacts/roster-bc-natural.tsv"
}
$result | Add-Member -NotePropertyName vpk_sha256 -NotePropertyValue (Get-FileHash $vpkPath -Algorithm SHA256).Hash.ToLowerInvariant()
$result | Add-Member -NotePropertyName started_utc -NotePropertyValue $started.ToString('o')
$result | ConvertTo-Json | Set-Content "$root/artifacts/vita3k-result.json"
$result | ConvertTo-Json
if($runtimeLog -match 'EXCEPTION_ACCESS_VIOLATION|\|C\||Assertion failed'){throw 'Vita3K runtime logged a critical failure; report and screenshots were saved'}
if($runtimeLog -match 'The app exited with code (?!0\b)'){throw 'Vita3K guest exited with a nonzero code; report and screenshots were saved'}
if($result.schema -ne 46 -or !$result.regression_gate -or !$result.sprite_region_crop_contract -or !$result.stage_viewport_contract -or !$result.stage_camera_pair_contract -or !$result.stage_bg36_aux_projection_contract -or !$result.stage_bg33_quad_contract -or !$result.stage_bg33_layout -or !$result.stage_bg33_layout_capture -or !$result.stage_bg33_scroll -or !$result.stage_bg33_scroll_capture -or $result.stage_bg33_slots -ne 1073741823 -or $result.stage_bg33_quad_draws -ne 30 -or $result.stage_bg33_tiles -ne 24 -or $result.stage_bg33_updates -le 0 -or $result.stage_bg33_counter -ne ($result.stage_bg33_updates -band 1023) -or $result.stage_bg36_cloud_quads_projected -lt 2 -or $result.battle_bg33_tiles -ne 24 -or $result.battle_bg33_draws -le 0 -or $result.battle_bg33_updates -le 0 -or $result.battle_bg33_slots -ne 1073741823 -or $result.battle_bg36_base_tiles -ne 25 -or $result.battle_bg36_base_draws -ne 25 -or $result.battle_bg36_base_slot_mask -ne 1073739676 -or $result.battle_bg36_capture_seen -ne 1 -or $result.battle_bg36_loaded -ne 4 -or $result.battle_bg36_draws -lt 4 -or $result.battle_bg36_updates -le 0 -or $result.battle_bg36_draw_mask -ne 15 -or !$result.stage_bg37_scroll_capture -or !$result.stage_bg38_scroll_capture -or $result.stage_bg37_scroll_ticks -le 0 -or $result.stage_bg38_scroll_ticks -le 0 -or $result.status -ne 'passed' -or $result.frames -ne 600){throw "Guest regression/PAT-crop/BG33/BG36/BG37/BG38 stage update gate failed (status=$($result.status), regression=$($result.regression_gate), PAT-crop=$($result.sprite_region_crop_contract), BG36base=$($result.battle_bg36_base_tiles)/$($result.battle_bg36_base_slot_mask), BG36aux=$($result.battle_bg36_loaded)/$($result.battle_bg36_draw_mask)/$($result.battle_bg36_updates), BG37=$($result.stage_bg37_scroll_capture)/$($result.stage_bg37_scroll_ticks), BG38=$($result.stage_bg38_scroll_capture)/$($result.stage_bg38_scroll_ticks)); report and screenshots were saved"}
# Terminate only the child launched by this runner if emulator stays open after guest exit.
if(!$p.HasExited){Stop-Process -Id $p.Id}
