param([Parameter(Mandatory)][string]$GameExe,[Parameter(Mandatory)][string]$GhidraHome,[Parameter(Mandatory)][string]$JdkHome)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$exe=(Resolve-Path -LiteralPath $GameExe).Path
$sha=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
$out=Join-Path $root "artifacts/ghidra/$sha"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$env:JAVA_HOME=$JdkHome
$env:PATH="$JdkHome/bin;$env:PATH"
& "$GhidraHome/support/analyzeHeadless.bat" "$root/artifacts/ghidra" "T123-$($sha.Substring(0,12))" -import $exe -analysisTimeoutPerFile 600 -scriptPath "$PSScriptRoot/ghidra" -postScript ExportT123.java $out $sha -log "$out/analysis.log"
if($LASTEXITCODE -ne 0){throw "Ghidra failed: $LASTEXITCODE"}
