param(
    [switch]$Apply,
    [switch]$IncludeExperimentalVpk,
    [string]$ArtifactsDirectory
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
if (!$ArtifactsDirectory) { $ArtifactsDirectory = Join-Path $repo 'artifacts' }
$artifacts = [IO.Path]::GetFullPath($ArtifactsDirectory)
$allowed = [IO.Path]::GetFullPath((Join-Path $repo 'artifacts'))
if ($artifacts -ne $allowed) { throw "Cleanup is restricted to repository artifacts/: $artifacts" }

# These are always reproducible snapshots. Preserve only the newest report of
# each type; a timestamped .previous remains available as the recovery source.
$stale = [Collections.Generic.List[IO.FileInfo]]::new()
foreach ($pattern in @('touhou123vita-*.bmp.*.previous', 'touhou123vita-smoke.json.*.previous', 'touhou123vita-bc-natural.tsv.*.previous')) {
    Get-ChildItem -LiteralPath (Join-Path $artifacts 'vitafs/ux0/data') -File -Filter $pattern -ErrorAction SilentlyContinue | ForEach-Object { $stale.Add($_) }
}

# Optional cleanup of clearly superseded VPK iterations. Never touch current
# builds, diagnostic probes, or experiments with a distinct named behavior.
if ($IncludeExperimentalVpk) {
    $keep = @('Touhou123Vita-current.vpk', 'Touhou123Vita-current-auto.vpk')
    $explicitKeep = @('Touhou123Vita-bc-natural-final.vpk', 'Touhou123Vita-bg36-cloud-scroll.vpk', 'Touhou123Vita-para-probar.vpk')
    $protectedPattern = '(?i)(diagnostic|probe|audit|review|para-probar|bc-natural-final|bg36-cloud-scroll|current|latest|TH75)'
    $candidates = Get-ChildItem -LiteralPath $artifacts -File -Filter '*.vpk' | Where-Object {
        $_.Name -notin $keep -and $_.Name -notin $explicitKeep -and $_.Name -notmatch $protectedPattern
    }
    foreach ($file in $candidates) { $stale.Add($file) }
}

if ($stale.Count -eq 0) { Write-Output 'No stale artifacts matched the selected policy.'; exit 0 }
$stale | Sort-Object FullName -Unique | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize
if (!$Apply) { Write-Output 'Preview only. Add -Apply to move these files into artifacts/_quarantine/.'; exit 0 }

$quarantine = Join-Path $artifacts '_quarantine'
New-Item -ItemType Directory -Force -Path $quarantine | Out-Null
foreach ($file in ($stale | Sort-Object FullName -Unique)) {
    if (!$file.FullName.StartsWith($artifacts + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside artifacts/: $($file.FullName)"
    }
    $relative = $file.FullName.Substring($artifacts.Length).TrimStart([IO.Path]::DirectorySeparatorChar)
    $destination = Join-Path $quarantine $relative
    New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
    Move-Item -LiteralPath $file.FullName -Destination $destination
}
Write-Output "Moved $($stale.Count) files to $quarantine. Nothing was permanently deleted."
