param([Parameter(ValueFromRemainingArguments=$true)][string[]]$CliArgs)
$ErrorActionPreference='Stop'
$pythonCandidates=@(
    (Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'),
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$python=$pythonCandidates | Select-Object -First 1
if(-not $python){throw 'Python 3 is required; run tools/find_pe-callers.py with the project analysis dependencies.'}
& $python (Join-Path $PSScriptRoot 'find_pe_callers.py') @CliArgs
if($LASTEXITCODE -ne 0){throw 'x86 caller scan failed'}
