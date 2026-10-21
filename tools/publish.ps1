param([string]$Owner='Botarguirix',[string]$Name='Touhou123Vita',[string]$CommitMessage='Update Vita prototype and validation')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='safe.directory'
$env:GIT_CONFIG_VALUE_0=$root.Replace('\','/')
# Use existing Git Credential Manager session. Never print credential values.
$request="protocol=https`nhost=github.com`n`n"
$credential=$request | git credential fill
if($LASTEXITCODE -ne 0){throw 'GitHub authentication unavailable'}
$password=($credential | Where-Object { $_.StartsWith('password=') }) -replace '^password=',''
if(!$password){throw 'GitHub credential missing'}
$headers=@{Authorization="Bearer $password";Accept='application/vnd.github+json';'X-GitHub-Api-Version'='2022-11-28'}
$user=Invoke-RestMethod 'https://api.github.com/user' -Headers $headers
if($user.login -ne $Owner){throw 'Authenticated GitHub owner mismatch'}
try {$repo=Invoke-RestMethod "https://api.github.com/repos/$Owner/$Name" -Headers $headers}
catch {
    if([int]$_.Exception.Response.StatusCode -ne 404){throw}
    $body=@{name=$Name;description='Experimental native PS Vita port research and practice prototype for Touhou 12.3';private=$true;auto_init=$false}|ConvertTo-Json
    $repo=Invoke-RestMethod 'https://api.github.com/user/repos' -Method Post -Headers $headers -ContentType 'application/json' -Body $body
}
$password=$null; $credential=$null; $headers=$null
if(!(Test-Path "$root/.git")){git -C $root init -b main}
if($LASTEXITCODE -ne 0){throw 'git init failed'}
if(!(git -C $root remote)){git -C $root remote add origin $repo.clone_url}
$paths=@('.gitignore','.gitattributes','CMakeLists.txt','README.md','docs','legacy','recomp','tests','tools','.github')
foreach($path in $paths){if(Test-Path (Join-Path $root $path)){git -C $root add -- $path}}
if($LASTEXITCODE -ne 0){throw 'Staging failed'}
$staged=@(git -C $root diff --cached --name-only)
foreach($path in $staged){
 if($path -match '^(assets|original|local|artifacts|build[^/]*)/' -or $path -match '\.(exe|dll|dat|vpk|self|rgba|png|zip|rep|pf)$'){throw "Disallowed publication file: $path"}
}
Write-Output 'Verified staged source paths:'
$staged | Write-Output
git -C $root diff --cached --quiet
if($LASTEXITCODE -eq 1){git -C $root commit -m $CommitMessage}
git -C $root push -u origin main
if($LASTEXITCODE -ne 0){throw 'git push failed'}
Write-Output $repo.html_url
