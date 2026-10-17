param(
    [string]$PoseDetail=(Join-Path (Split-Path $PSScriptRoot -Parent) 'artifacts/pat-detail.tsv'),
    [string[]]$Manifest=@(
        (Join-Path (Split-Path $PSScriptRoot -Parent) 'artifacts/th123-resource-manifest.tsv'),
        (Join-Path (Split-Path $PSScriptRoot -Parent) 'artifacts/th105-resource-manifest.tsv')
    ),
    [string]$OutputTsv=(Join-Path (Split-Path $PSScriptRoot -Parent) 'artifacts/pat-resource-coverage.tsv'),
    [string]$OutputMarkdown=(Join-Path (Split-Path $PSScriptRoot -Parent) 'docs/PAT_RESOURCE_COVERAGE.md')
)
$ErrorActionPreference='Stop'
$available=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach($manifestPath in $Manifest){
    foreach($entry in (Import-Csv -LiteralPath $manifestPath -Delimiter "`t")){
        [void]$available.Add($entry.path.Replace('\','/'))
    }
}
$variants=@{}
$poseCount=0
$damagingPoseCount=0
foreach($row in (Import-Csv -LiteralPath $PoseDetail -Delimiter "`t")){
    $poseCount++
    if([int]$row.damage -le 0 -or ($row.attack_boxes -eq '-' -and [Convert]::ToUInt32($row.attack_flags.Substring(2),16) -eq 0)){continue}
    $damagingPoseCount++
    $parts=$row.path.Split('/')
    if($parts.Length -lt 4){continue}
    $character=$parts[2]
    $image=$row.image_name
    $dot=$image.LastIndexOf('.')
    if($dot -ge 0){$image=$image.Substring(0,$dot)+'.cv2'}
    $imagePath="data/character/$character/$image"
    $key="$character`t$($row.action)`t$($row.index)"
    if(!$variants.ContainsKey($key)){$variants[$key]=[pscustomobject]@{character=$character;action=[int]$row.action;index=[int]$row.index;damaging_poses=0;max_damage=0;attack_boxes=0;missing_images=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);image_examples=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)}}
    $v=$variants[$key]
    $v.damaging_poses++
    $damage=[int]$row.damage;if($damage -gt $v.max_damage){$v.max_damage=$damage}
    if($row.attack_boxes -ne '-'){$v.attack_boxes+=($row.attack_boxes.Split(';').Length)}
    [void]$v.image_examples.Add($imagePath)
    if(!$available.Contains($imagePath)){[void]$v.missing_images.Add($imagePath)}
}
$rows=@($variants.Values | Sort-Object character,action,index | ForEach-Object {
    [pscustomobject]@{character=$_.character;action=$_.action;index=$_.index;damaging_poses=$_.damaging_poses;max_damage=$_.max_damage;attack_boxes=$_.attack_boxes;distinct_images=$_.image_examples.Count;missing_images=$_.missing_images.Count;missing_image_examples=(@($_.missing_images | Sort-Object | Select-Object -First 3) -join ';')}
})
$parent=Split-Path $OutputTsv -Parent;New-Item -ItemType Directory -Force $parent | Out-Null
$rows | Export-Csv -LiteralPath $OutputTsv -Delimiter "`t" -NoTypeInformation -Encoding utf8
$playable=$rows | Where-Object character -NotIn @('common','namazu')
$characters=@($playable.character | Sort-Object -Unique)
$actionSummary=@($playable | Group-Object action | Sort-Object {[int]$_.Name} | ForEach-Object {
    $group=$_.Group
    $resolvable=@($group | Where-Object missing_images -eq 0).Count
    $missing=@($group | Where-Object missing_images -gt 0).Count
    "| $($_.Name) | $($group.Count) | $resolvable | $missing |"
})
$perCharacter=@($characters | ForEach-Object {
    $name=$_;$group=@($playable | Where-Object character -eq $name)
    $variantCount=$group.Count
    $completeCount=@($group | Where-Object {[int]$_.missing_images -eq 0}).Count
    $missingCount=@($group | Where-Object {[int]$_.missing_images -gt 0}).Count
    "| $name | $variantCount | $completeCount | $missingCount |"
})
$lines=@(
    '# Cobertura de poses de ataque y recursos de imagen',
    '',
    'Cruce reproducible de artifacts/pat-detail.tsv con los manifiestos descifrados de los tres DAT 12.3 y los DAT th105a.dat/th105b.dat. Las variantes con dano requieren dano y caja o flag de ataque; missing_images cuenta imagenes referenciadas por poses daninas que no estan indexadas en ninguno de esos cinco DAT.',
    '',
    "- Poses PAT examinadas: **$poseCount**.",
    "- Poses con dano y caja/flag ofensivo: **$damagingPoseCount**.",
    "- Variantes personaje/accion/indice con dano: **$($playable.Count)** en **$($characters.Count)** personajes jugables candidatos.",
    '- Manifiesto detallado: artifacts/pat-resource-coverage.tsv.',
    '',
    '## Por personaje',
    '',
    '| Personaje | Variantes con dano | Todas las imagenes disponibles | Variantes con referencias faltantes |',
    '|---|---:|---:|---:|'
)
$lines += $perCharacter
$lines += @(
    '',
    '## Por ID de accion',
    '',
    '| Accion | Variantes con dano | Imagenes completas | Con imagenes faltantes |',
    '|---:|---:|---:|---:|'
)
$lines += $actionSummary
$lines += @(
    '',
    'Esta auditoria prueba disponibilidad por indice de DAT, no la seleccion de variante, el orden de animacion, el input ni la generacion de objetos. Una variante sin imagen faltante aun puede usar datos PAT que el renderer no soporte; una variante con archivos encontrados todavia requiere decodificacion/renderizado en Vita3K.'
)
Set-Content -LiteralPath $OutputMarkdown -Value ($lines -join "`n") -Encoding utf8
Write-Output "poses=$poseCount damaging=$damagingPoseCount variants=$($playable.Count) characters=$($characters.Count)"
Write-Output "TSV: $OutputTsv"
Write-Output "Markdown: $OutputMarkdown"
