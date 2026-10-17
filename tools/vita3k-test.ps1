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
New-Item -ItemType Directory -Force (Split-Path $report -Parent) | Out-Null
foreach($scene in @('menu','gallery','stage','stage-assets','stage-layout','practice','fight','fight-natural-a','object-probe')){
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
$portableRoot=Join-Path $emulatorCopy 'portable'
$portableFs=Join-Path $portableRoot 'fs'
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
$args=@('--load-config','--keep-config','--config-location',('"'+$testConfig+'"'),'--log-level','2','--installed-path','THSV12301')
if($Frontend -eq 'sdl'){$args=@('--frontend','sdl')+$args}
$started=[DateTime]::UtcNow
$p=Start-Process -FilePath $runnerExe -ArgumentList $args -WorkingDirectory $emulatorCopy -WindowStyle Hidden -PassThru -RedirectStandardOutput "$root/artifacts/vita3k-test.stdout.log" -RedirectStandardError "$root/artifacts/vita3k-test.stderr.log"
$deadline=$started.AddSeconds($TimeoutSeconds)
while([DateTime]::UtcNow -lt $deadline -and !(Test-Path $report) -and !$p.HasExited){Start-Sleep -Milliseconds 500;$p.Refresh()}
if(!(Test-Path $report)){
 if(!$p.HasExited){Stop-Process -Id $p.Id}
 $exitDetail=if($p.HasExited){"process exited with code $($p.ExitCode)"}else{'process was stopped at timeout'}
 $stderr=Get-Content -LiteralPath "$root/artifacts/vita3k-test.stderr.log" -Raw -ErrorAction SilentlyContinue
 throw "Vita3K did not produce fresh guest evidence; $exitDetail. stderr: $stderr"
}
$result=Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
$p.WaitForExit(5000) | Out-Null
$p.Refresh()
$runtimeLog=Get-Content "$root/artifacts/vita3k-test.stdout.log" -Raw
New-Item -ItemType Directory -Force "$root/artifacts/screenshots" | Out-Null
foreach($scene in @('menu','gallery','stage','stage-assets','stage-layout','practice','fight','fight-natural-a','object-probe')){
 $capture=Join-Path $fsPath "ux0/data/touhou123vita-$scene.bmp"
 if(!(Test-Path $capture)){throw "Guest framebuffer capture missing: $scene"}
 Copy-Item -LiteralPath $capture -Destination "$root/artifacts/screenshots/$scene.bmp" -Force
}
$result | Add-Member -NotePropertyName vpk_sha256 -NotePropertyValue (Get-FileHash $vpkPath -Algorithm SHA256).Hash.ToLowerInvariant()
$result | Add-Member -NotePropertyName started_utc -NotePropertyValue $started.ToString('o')
$result | ConvertTo-Json | Set-Content "$root/artifacts/vita3k-result.json"
$result | ConvertTo-Json
if($runtimeLog -match 'EXCEPTION_ACCESS_VIOLATION|\|C\||Assertion failed'){throw 'Vita3K runtime logged a critical failure; report and screenshots were saved'}
if($runtimeLog -match 'The app exited with code (?!0\b)'){throw 'Vita3K guest exited with a nonzero code; report and screenshots were saved'}
if($result.schema -ne 30 -or $result.status -ne 'passed' -or $result.frames -ne 600 -or !$result.menu -or !$result.gallery -or !$result.gallery_texture -or !$result.gallery_character -or !$result.gallery_action -or !$result.gallery_pose -or !$result.stage_view -or $result.stage -ne 'bg34' -or $result.stage_layer -ne 3 -or !$result.stage_layout -or !$result.stage_texture -or !$result.stage_navigation -or $result.stage_tiles -ne 30 -or $result.stage_alt_tiles -ne 30 -or $result.stage_static_assets -ne 4 -or $result.stage_object_assets -ne 30 -or $result.stage_animation_tick -ge 60 -or $result.stage_animation_frame -ne [math]::Floor($result.stage_animation_tick/2) -or !$result.practice -or !$result.fight -or !$result.jump -or $result.dash_gate_probe -ne 1 -or $result.object_route_probe -ne 5 -or $result.object_attack_routes -ne 4 -or $result.suwako_418_burst_spawns -ne 10 -or $result.object_anchor_probe -ne 2 -or !$result.object_sprite_seen -or !$result.object_render_capture -or !$result.pat_effect_fixture -or $result.dash_direct_hits -le 0 -or ($result.dash_direct_hits + $result.dash_no_direct_boxes) -ne 38 -or $result.hits -le 0 -or $result.a_hits -le 0 -or $result.dashes -le 0 -or $result.b_hits -le 0 -or $result.c_hits -le 0 -or !$result.skill_uses -or $result.skill_action -ne 560 -or $result.skill_image -lt 0 -or !$result.skill_sequence_ok -or $result.skill_start_sequence -ne 0 -or $result.skill_hit_sequence -ne 1 -or $result.skill_startup_hit_delta -ne 0 -or $result.skill_hit_delta -le 0 -or !$result.skill_air_launch_ok -or !$result.skill_landing_ok -or $result.skill_landing_sequence -ne 3 -or $result.skill_x_delta -le 0 -or !$result.skill_reverse_motion_ok -or $result.skill_102_action -ne 540 -or $result.skill_102_image -ne 774 -or !$result.skill_102_sequence_ok -or $result.skill_102_hit_delta -ne 1100 -or $result.skill_102_hit_sequence -ne 3 -or $result.skill_102_hit_image -ne 39 -or $result.skill_102_followup_ticks -ne 47 -or $result.skill_107_action -ne 565 -or $result.skill_107_image -ne 12 -or !$result.skill_107_sequence_ok -or $result.skill_107_hit_delta -ne 450 -or $result.skill_107_hit_sequence -ne 1 -or $result.skill_107_hit_image -ne 47 -or $result.skill_107_followup_ticks -ne 63 -or $result.skill_104_phase_mask -ne 7 -or $result.skill_104_action -ne 505 -or !$result.skill_104_sequence_ok -or $result.skill_104_spawn_count -ne 4 -or $result.skill_104_object_action -ne 811 -or !$result.skill_104_sprite_seen -or $result.skill_104_hit_delta -le 0 -or $result.cpu_hp -ge $result.max_hp -or $result.external_dat -ne 31 -or $result.textures_decoded -le 2 -or $result.roster_cards -ne 20 -or $result.roster_assets -ne 20 -or $result.roster_a_attack_mask -ne 1048575 -or $result.roster_a_natural_attack_mask -ne 1048575){throw "Guest DAT/roster/gallery/stage/dash/direct-hit/PAT-payload/B/C/ordered-skill/skill-flight/card104-505-volley validation failed (gallery=$($result.gallery), stage=$($result.stage)/layer $($result.stage_layer), directHits=$($result.dash_direct_hits), noDirectBoxes=$($result.dash_no_direct_boxes), patEffectFixture=$($result.pat_effect_fixture), cards=$($result.roster_cards)/20, combatSprites=$($result.roster_assets)/20, ArouteMask=$($result.roster_a_attack_mask), AnaturalMask=$($result.roster_a_natural_attack_mask), dashes=$($result.dashes), B=$($result.b_hits), C=$($result.c_hits), skillAction=$($result.skill_action), card104phases=$($result.skill_104_phase_mask), card104=$($result.skill_104_action)/spawn$($result.skill_104_spawn_count)/object$($result.skill_104_object_action)/sprite$($result.skill_104_sprite_seen)/damage$($result.skill_104_hit_delta), hitSequence=$($result.skill_hit_sequence), skillHitDelta=$($result.skill_hit_delta)); report and screenshots were saved"}
# Terminate only the child launched by this runner if emulator stays open after guest exit.
if(!$p.HasExited){Stop-Process -Id $p.Id}
