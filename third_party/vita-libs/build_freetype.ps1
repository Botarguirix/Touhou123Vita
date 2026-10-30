# FreeType 2.13.3 para Vita (libfreetype.a en artifacts/vita-libs), para el
# GetGlyphOutlineA de recomp/host/glyph.c. Tarball oficial verificado por SHA-256.
param([string]$VitaSDK = $(if ($env:VITASDK) { $env:VITASDK } else { 'C:\vitasdk' }))
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$out = Join-Path $root 'artifacts/vita-libs'
$archive = Join-Path $out 'downloads/freetype-2.13.3.tar.xz'
$sha = '0550350666d427c74daeb85d5ac7bb353acba5f76956395995311a9c6f063289'
if (!(Test-Path $archive)) {
    Invoke-WebRequest -Uri 'https://download.savannah.gnu.org/releases/freetype/freetype-2.13.3.tar.xz' -OutFile $archive
}
if ((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha) { throw "SHA-256 incorrecto: $archive" }
$src = Join-Path $out 'src/freetype-2.13.3'
if (!(Test-Path $src)) {
    python -I -c "import sys,tarfile; tarfile.open(sys.argv[1]).extractall(sys.argv[2], filter='data')" $archive (Join-Path $out 'src')
}
$cc = Join-Path $VitaSDK 'bin/arm-vita-eabi-gcc.exe'
$ar = Join-Path $VitaSDK 'bin/arm-vita-eabi-ar.exe'
$obj = Join-Path $out 'obj/freetype'
New-Item -ItemType Directory -Force $obj | Out-Null
$files = 'autofit/autofit.c', 'base/ftbase.c', 'base/ftbbox.c', 'base/ftbdf.c', 'base/ftbitmap.c', 'base/ftcid.c',
    'base/ftfstype.c', 'base/ftgasp.c', 'base/ftglyph.c', 'base/ftgxval.c', 'base/ftinit.c', 'base/ftmm.c',
    'base/ftotval.c', 'base/ftpatent.c', 'base/ftpfr.c', 'base/ftstroke.c', 'base/ftsynth.c', 'base/fttype1.c',
    'base/ftwinfnt.c', 'base/ftsystem.c', 'base/ftdebug.c', 'bdf/bdf.c', 'cache/ftcache.c', 'cff/cff.c',
    'cid/type1cid.c', 'gzip/ftgzip.c', 'lzw/ftlzw.c', 'pcf/pcf.c', 'pfr/pfr.c', 'psaux/psaux.c',
    'pshinter/pshinter.c', 'psnames/psnames.c', 'raster/raster.c', 'sdf/sdf.c', 'sfnt/sfnt.c',
    'smooth/smooth.c', 'svg/svg.c', 'truetype/truetype.c', 'type1/type1.c', 'type42/type42.c', 'winfonts/winfnt.c'
$objects = foreach ($f in $files) {
    $o = Join-Path $obj (($f -replace '[/\\]', '_') -replace '\.c$', '.o')
    & $cc -O2 -DFT2_BUILD_LIBRARY "-I$src/include" -c "$src/src/$f" -o $o
    if ($LASTEXITCODE) { throw "fallo al compilar $f" }
    $o
}
$lib = Join-Path $out 'lib/libfreetype.a'
Remove-Item $lib -ErrorAction SilentlyContinue
& $ar rcs $lib @objects
if ($LASTEXITCODE) { throw 'fallo ar' }
Copy-Item -Recurse -Force "$src/include/*" (Join-Path $out 'include')
Copy-Item -Force "$src/LICENSE.TXT" (Join-Path $out 'licenses/freetype-LICENSE.TXT')
Write-Output "libfreetype.a: $((Get-Item $lib).Length) bytes"
