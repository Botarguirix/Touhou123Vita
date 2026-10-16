param([Parameter(Mandatory)][string]$Destination)
$ErrorActionPreference='Stop'
$source=Split-Path $PSScriptRoot -Parent
$dest=(Resolve-Path -LiteralPath $Destination).Path
$remote=git -c "safe.directory=$($dest.Replace('\','/'))" -C $dest remote get-url origin
if($remote -ne 'https://github.com/Botarguirix/Touhou123Vita.git'){throw 'Destination remote mismatch'}
$status=git -c "safe.directory=$($dest.Replace('\','/'))" -C $dest status --porcelain
if($status){throw 'Destination contains changes; refusing to overwrite'}
$files=git -c "safe.directory=$($source.Replace('\','/'))" -C $source ls-files --cached --others --exclude-standard
foreach($file in $files){
 if($file -notmatch '^(src/|include/|tests/|tools/|docs/|\.github/|README\.md$|CMakeLists\.txt$|\.gitignore$|\.gitattributes$)'){throw "Unapproved source path: $file"}
 if($file -match '\.(exe|dll|dat|vpk|rgba|png|zip|bmp)$'){throw "Binary excluded: $file"}
 $target=[System.IO.Path]::GetFullPath((Join-Path $dest $file))
 if(!$target.StartsWith($dest+[System.IO.Path]::DirectorySeparatorChar)){throw 'Destination path escapes clone'}
 New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
 Copy-Item -LiteralPath (Join-Path $source $file) -Destination $target -Force
}
Write-Output "Source synchronized to GitHub Desktop clone: $dest"
