param(
 [Parameter(Mandatory)][string]$GhidraHome,
 [Parameter(Mandatory)][string]$JdkHome,
 [string]$ProjectOwner='ikari'
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$sha=(Get-FileHash "$root/original/th123.exe" -Algorithm SHA256).Hash.ToLowerInvariant()
$projectName="T123-$($sha.Substring(0,12))"
$out=Join-Path $root "artifacts/kernel/$sha/resource-loader"
New-Item -ItemType Directory -Force -Path $out | Out-Null
# The archived Ghidra project records its original owner in project metadata.
# Override only Java's project-owner label for this read-only headless session.
$env:APPDATA=Join-Path $root 'artifacts/ghidra/appdata'
New-Item -ItemType Directory -Force -Path $env:APPDATA | Out-Null
$env:JAVA_TOOL_OPTIONS="-Duser.name=$ProjectOwner"
$env:JAVA_HOME=$JdkHome
$env:PATH="$JdkHome/bin;$env:PATH"
$log=Join-Path $out 'analysis.log'
& "$GhidraHome/support/analyzeHeadless.bat" "$root/artifacts/ghidra" $projectName -process th123.exe -readOnly -noanalysis -scriptPath "$PSScriptRoot/ghidra" -postScript ExportKernel.java $out $sha resources -log $log
$scriptError=Select-String -LiteralPath $log -Pattern 'ERROR REPORT SCRIPT ERROR' -Quiet -ErrorAction SilentlyContinue
if($LASTEXITCODE -ne 0 -or $scriptError -or !(Test-Path (Join-Path $out 'manifest.tsv')) -or !(Test-Path (Join-Path $out 'resource-strings.tsv'))){throw 'Resource loader export failed'}
