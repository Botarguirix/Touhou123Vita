param(
 [Parameter(Mandatory)][string]$GhidraHome,
 [Parameter(Mandatory)][string]$JdkHome,
 [string]$ProjectOwner='ikari'
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$sha=(Get-FileHash -LiteralPath (Join-Path $root 'original/th123.exe') -Algorithm SHA256).Hash.ToLowerInvariant()
$projectName="T123-$($sha.Substring(0,12))"
$out=Join-Path $root "artifacts/pe-inventory/$sha"
New-Item -ItemType Directory -Force -Path $out | Out-Null
foreach($generated in @('functions.tsv','functions-summary.txt')){
 $old=Join-Path $out $generated
 if(Test-Path -LiteralPath $old){Remove-Item -LiteralPath $old -Force}
}
$env:APPDATA=Join-Path $root 'artifacts/ghidra/appdata'
New-Item -ItemType Directory -Force -Path $env:APPDATA | Out-Null
$env:JAVA_TOOL_OPTIONS="-Duser.name=$ProjectOwner"
$env:JAVA_HOME=$JdkHome
$env:PATH="$JdkHome/bin;$env:PATH"
$log=Join-Path $out 'ghidra-functions.log'
& "$GhidraHome/support/analyzeHeadless.bat" (Join-Path $root 'artifacts/ghidra') $projectName -process th123.exe -readOnly -noanalysis -scriptPath (Join-Path $PSScriptRoot 'ghidra') -postScript ExportFunctions.java $out $sha -log $log
$scriptError=Select-String -LiteralPath $log -Pattern 'ERROR REPORT SCRIPT ERROR' -Quiet -ErrorAction SilentlyContinue
if($LASTEXITCODE -ne 0 -or $scriptError -or !(Test-Path (Join-Path $out 'functions.tsv'))){throw 'Function export failed'}
Get-Content (Join-Path $out 'functions-summary.txt')
