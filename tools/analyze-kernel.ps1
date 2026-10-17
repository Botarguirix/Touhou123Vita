param([Parameter(Mandatory)][string]$GhidraHome,[Parameter(Mandatory)][string]$JdkHome)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$sha=(Get-FileHash "$root/original/th123.exe" -Algorithm SHA256).Hash.ToLowerInvariant()
$out="$root/artifacts/kernel/$sha/input-state"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$env:JAVA_HOME=$JdkHome;$env:PATH="$JdkHome/bin;$env:PATH"
& "$GhidraHome/support/analyzeHeadless.bat" "$root/artifacts/ghidra" "T123-$($sha.Substring(0,12))" -process th123.exe -readOnly -noanalysis -scriptPath "$PSScriptRoot/ghidra" -postScript ExportKernel.java $out $sha -log "$out/analysis.log"
if($LASTEXITCODE -ne 0){throw 'Targeted analysis failed'}
