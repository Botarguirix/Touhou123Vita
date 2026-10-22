param(
 [string]$Vpk,
 [int]$TimeoutSeconds = 900,
 [ValidateSet('qt','sdl')][string]$Frontend = 'sdl'
)
# Runs the recompiled-game VPK (recomp/build_vita.py) in the project's isolated
# Vita3K and collects ux0:data/touhou123vita/recomp-result.txt, recomp-trace.log
# and recomp-screen.bmp into artifacts/recomp/<sha>/vita/run.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$sha = 'f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e'
$titleId = 'THSV12302'
if (!$Vpk) { $Vpk = Join-Path $root "artifacts/recomp/$sha/vita/T123Recomp.vpk" }
$vpkPath = (Resolve-Path -LiteralPath $Vpk).Path
$fs = (Resolve-Path -LiteralPath (Join-Path $root 'artifacts/vitafs')).Path
$data = Join-Path $fs 'ux0/data/touhou123vita'
New-Item -ItemType Directory -Force $data | Out-Null

# The user's files: the VPK carries no game data.
if (!(Test-Path (Join-Path $data 'th123.exe'))) { Copy-Item (Join-Path $root 'original/th123.exe') $data }
foreach ($dat in 'th123a.dat', 'th123b.dat', 'th123c.dat') {
 if (!(Test-Path (Join-Path $data $dat))) { Copy-Item (Join-Path $root "original/$dat") $data }
}
$exeHash = (Get-FileHash (Join-Path $data 'th123.exe') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($exeHash -ne $sha) { throw "ux0:data/touhou123vita/th123.exe is not the reference 1.10a executable ($exeHash)" }
foreach ($name in 'recomp-result.txt', 'recomp-trace.log', 'recomp-screen.bmp') {
 Remove-Item -LiteralPath (Join-Path $data $name) -Force -ErrorAction SilentlyContinue
}

# Install the VPK directly into the isolated VitaFS (no GUI install).
$appRoot = Join-Path $fs "ux0/app/$titleId"
if (Test-Path $appRoot) { Remove-Item -LiteralPath $appRoot -Recurse -Force }
New-Item -ItemType Directory -Force $appRoot | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($vpkPath)
try {
 $rootFull = [IO.Path]::GetFullPath($appRoot) + [IO.Path]::DirectorySeparatorChar
 foreach ($entry in $zip.Entries) {
  $target = [IO.Path]::GetFullPath((Join-Path $appRoot $entry.FullName))
  if (!$target.StartsWith($rootFull)) { throw 'Unsafe VPK entry' }
  if ($entry.FullName.EndsWith('/')) { New-Item -ItemType Directory -Force $target | Out-Null; continue }
  New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
  $in = $entry.Open()
  try { $o = [IO.File]::Create($target); try { $in.CopyTo($o) } finally { $o.Dispose() } } finally { $in.Dispose() }
 }
} finally { $zip.Dispose() }

# Project-local portable Vita3K whose VitaFS is a junction to artifacts/vitafs
# (prepared by tools/vita3k-test.ps1).
$emulator = Join-Path $root 'local/vita3k-isolated'
$exe = Join-Path $emulator 'Vita3K.exe'
$config = Join-Path $emulator 'portable/config.yml'
if (!(Test-Path $exe) -or !(Test-Path $config)) { throw 'Isolated Vita3K missing: run tools/vita3k-test.ps1 once to prepare it' }
$portableFs = Join-Path $emulator 'portable/fs'
if ((Get-Item -LiteralPath $portableFs).LinkType -ne 'Junction') { throw "$portableFs is not the VitaFS junction" }

$out = Join-Path $root "artifacts/recomp/$sha/vita/run"
New-Item -ItemType Directory -Force $out | Out-Null
$arguments = @('--load-config', '--keep-config', '--config-location', ('"' + $config + '"'), '--log-level', '2', '-r', $titleId)
if ($Frontend -eq 'sdl') { $arguments += @('--frontend', 'sdl') }
$started = Get-Date
$p = Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $emulator -WindowStyle Hidden -PassThru `
 -RedirectStandardOutput (Join-Path $out 'vita3k.stdout.log') -RedirectStandardError (Join-Path $out 'vita3k.stderr.log')
$result = Join-Path $data 'recomp-result.txt'
$deadline = $started.AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline -and !(Test-Path $result) -and !$p.HasExited) { Start-Sleep -Milliseconds 500; $p.Refresh() }
Start-Sleep -Seconds 2
if (!$p.HasExited) { Stop-Process -Id $p.Id -ErrorAction SilentlyContinue }
foreach ($name in 'recomp-result.txt', 'recomp-trace.log', 'recomp-screen.bmp') {
 $f = Join-Path $data $name
 if (Test-Path $f) { Copy-Item -LiteralPath $f -Destination $out -Force }
}
$log = Join-Path $emulator 'portable/vita3k.log'
if (Test-Path $log) { Copy-Item -LiteralPath $log -Destination (Join-Path $out 'vita3k.log') -Force }
$seconds = [int]((Get-Date) - $started).TotalSeconds
if (Test-Path $result) {
 "Vita3K run finished in $seconds s:"
 Get-Content $result
} else {
 "No recomp-result.txt after $seconds s (process exited: $($p.HasExited)). Last trace lines:"
 if (Test-Path (Join-Path $out 'recomp-trace.log')) { Get-Content (Join-Path $out 'recomp-trace.log') -Tail 15 }
 if (Test-Path (Join-Path $out 'vita3k.log')) { Select-String -Path (Join-Path $out 'vita3k.log') -Pattern 'error|crash|abort|exception' | Select-Object -Last 15 | ForEach-Object Line }
 exit 1
}
