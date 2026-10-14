param([string]$Repository='Botarguirix/Touhou123Vita')
$ErrorActionPreference='Stop'
$credential="protocol=https`nhost=github.com`n`n" | git credential fill
$token=($credential | Where-Object { $_.StartsWith('password=') }) -replace '^password=',''
if(!$token){throw 'GitHub credentials unavailable'}
$headers=@{Authorization="Bearer $token";Accept='application/vnd.github+json'}
$runs=Invoke-RestMethod "https://api.github.com/repos/$Repository/actions/runs?per_page=5" -Headers $headers
$token=$null;$headers=$null;$credential=$null
$runs.workflow_runs | Select-Object id,head_sha,status,conclusion,html_url
