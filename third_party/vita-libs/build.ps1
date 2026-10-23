param(
    [string]$VitaSDK = $env:VITASDK,
    [string]$OutputDirectory,
    [string]$Executable,
    [switch]$Offline,
    [switch]$HostSmoke,
    [string]$HostCompiler = 'C:\msys64\ucrt64\bin\gcc.exe'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if (!$OutputDirectory) { $OutputDirectory = Join-Path $root 'artifacts/vita-libs' }
$out = [IO.Path]::GetFullPath($OutputDirectory)
if (!$VitaSDK) { $VitaSDK = 'C:\vitasdk' }
$cc = Join-Path $VitaSDK 'bin/arm-vita-eabi-gcc.exe'
$ar = Join-Path $VitaSDK 'bin/arm-vita-eabi-ar.exe'
$elfCreate = Join-Path $VitaSDK 'bin/vita-elf-create.exe'
$makeSelf = Join-Path $VitaSDK 'bin/vita-make-fself.exe'
foreach ($tool in @($cc, $ar, $elfCreate, $makeSelf)) {
    if (!(Test-Path -LiteralPath $tool -PathType Leaf)) { throw "Falta herramienta: $tool" }
}
foreach ($dir in @($out, "$out/downloads", "$out/src", "$out/include", "$out/lib", "$out/obj", "$out/licenses")) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# No se leen bytes del PE antes de verificar la identidad del ejecutable.
$pePath = if ($Executable) { [IO.Path]::GetFullPath($Executable) } else { Join-Path $root 'original/th123.exe' }
$peSha = 'f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e'
if ((Get-FileHash -LiteralPath $pePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $peSha) {
    throw 'SHA-256 del PE incorrecto; no se permite analizar otra version.'
}
$peBytes = [IO.File]::ReadAllBytes($pePath)
$peAscii = [Text.Encoding]::ASCII.GetString($peBytes)
$peOffset = [BitConverter]::ToInt32($peBytes, 0x3c)
$sectionStart = $peOffset + 24 + [BitConverter]::ToUInt16($peBytes, $peOffset + 20)
$sections = for ($i = 0; $i -lt [BitConverter]::ToUInt16($peBytes, $peOffset + 6); $i++) {
    $s = $sectionStart + $i * 40
    [pscustomobject]@{
        va = 0x400000 + [BitConverter]::ToUInt32($peBytes, $s + 12)
        size = [BitConverter]::ToUInt32($peBytes, $s + 16)
        raw = [BitConverter]::ToUInt32($peBytes, $s + 20)
    }
}
function Find-PeString([string]$Value) {
    $offset = $peAscii.IndexOf($Value, [StringComparison]::Ordinal)
    if ($offset -lt 0) { return $null }
    $section = $sections | Where-Object { $offset -ge $_.raw -and $offset -lt ($_.raw + $_.size) } | Select-Object -First 1
    if (!$section) { throw "Cadena fuera de secciones: $Value" }
    [ordered]@{ text = $Value; file_offset = ('0x{0:x8}' -f $offset); va = ('0x{0:x8}' -f ($section.va + $offset - $section.raw)) }
}
$evidence = [ordered]@{
    pe_sha256 = $peSha
    zlib = Find-PeString 'deflate 1.2.3 Copyright 1995-2005 Jean-loup Gailly'
    inflate = Find-PeString 'inflate 1.2.3 Copyright 1995-2005 Mark Adler'
    libpng = Find-PeString '1.2.5'
    vorbis_marker = Find-PeString 'vorbis'
    xiph_ascii = Find-PeString 'Xiph.Org'
    libvorbis_ascii = Find-PeString 'libVorbis'
    xiph_utf16_present = [Text.Encoding]::Unicode.GetString($peBytes).Contains('Xiph.Org')
    audio_version_status = 'No identificada exactamente: libogg 1.1.3 y libvorbis 1.1.2 son una base provisional, no una version probada del PE.'
}
if (!$evidence.zlib -or !$evidence.inflate -or !$evidence.libpng -or !$evidence.vorbis_marker) { throw 'No se encontraron las cadenas esperadas.' }
$evidence | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$out/pe-evidence.json" -Encoding utf8NoBOM

# Tarballs oficiales. libpng: archivo del tag del repositorio oficial porque
# SourceForge devuelve HTML en este entorno. No son bytes del tarball de 2002.
$packages = @(
    [ordered]@{ name = 'zlib'; version = '1.2.3'; directory = 'zlib-1.2.3'; archive = 'zlib-1.2.3.tar.gz'; url = 'https://zlib.net/fossils/zlib-1.2.3.tar.gz'; sha256 = '1795c7d067a43174113fdf03447532f373e1c6c57c08d61d9e4e9be5e244b05e' },
    [ordered]@{ name = 'libpng'; version = '1.2.5'; directory = 'libpng-1.2.5'; archive = 'libpng-1.2.5.tar.gz'; url = 'https://codeload.github.com/pnggroup/libpng/tar.gz/refs/tags/v1.2.5'; sha256 = '58ec845f95ff351c8a25bfbfa667a8f3924bb0f1a1ec572cc7e09b8817204d1e' },
    [ordered]@{ name = 'libogg'; version = '1.1.3'; directory = 'libogg-1.1.3'; archive = 'libogg-1.1.3.tar.gz'; url = 'https://downloads.xiph.org/releases/ogg/libogg-1.1.3.tar.gz'; sha256 = 'bae29e79fbc50bbedf1235852094b71c8c910a1ef0cd42fe4163b7b545630b65' },
    [ordered]@{ name = 'libvorbis'; version = '1.1.2'; directory = 'libvorbis-1.1.2'; archive = 'libvorbis-1.1.2.tar.gz'; url = 'https://downloads.xiph.org/releases/vorbis/libvorbis-1.1.2.tar.gz'; sha256 = '3f7135ccbda589c251017912f5f5ec9da626c976d2376bcfda19ad6b9c4a6050' }
)
foreach ($package in $packages) {
    $archive = Join-Path "$out/downloads" $package.archive
    if (!(Test-Path -LiteralPath $archive -PathType Leaf)) {
        if ($Offline) { throw "Falta tarball en modo Offline: $archive" }
        Invoke-WebRequest -Uri $package.url -OutFile $archive
    }
    $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $package.sha256) { throw "SHA-256 incorrecto: $archive ($actual)" }
    & tar -xzf $archive -C "$out/src"
    if ($LASTEXITCODE -ne 0) { throw "Fallo al extraer $archive" }
    Write-Output "SHA-256 OK: $($package.archive)"
}
$z = "$out/src/zlib-1.2.3"
$png = "$out/src/libpng-1.2.5"
$ogg = "$out/src/libogg-1.1.3"
$vorbis = "$out/src/libvorbis-1.1.2"
# Las tablas identifican la familia, no una release: permanecen iguales entre
# varias versiones. Se guardan solo hash/tamano/direccion, nunca los datos.
function Get-TableEvidence([string]$SourcePath, [string]$Pattern, [string]$Kind, [string]$Name) {
    $match = [regex]::Match([IO.File]::ReadAllText($SourcePath), $Pattern, [Text.RegularExpressions.RegexOptions]::Singleline)
    if (!$match.Success) { throw "No se encontro tabla: $Name" }
    $table = [Collections.Generic.List[byte]]::new()
    foreach ($token in $match.Groups[1].Value.Split(',')) {
        $value = $token.Trim()
        if (!$value) { continue }
        if ($Kind -eq 'float') {
            $number = [single]::Parse($value.TrimEnd([char[]]'fF'), [Globalization.CultureInfo]::InvariantCulture)
            $table.AddRange([BitConverter]::GetBytes($number))
        } else {
            $number = [Convert]::ToUInt32($value.TrimEnd([char[]]'uUlL').Substring(2), 16)
            $table.AddRange([BitConverter]::GetBytes($number))
        }
    }
    $tableBytes = $table.ToArray()
    $offset = [Text.Encoding]::Latin1.GetString($peBytes).IndexOf([Text.Encoding]::Latin1.GetString($tableBytes), [StringComparison]::Ordinal)
    if ($tableBytes.Length -ne 1024 -or $offset -lt 0) { throw "Tabla no coincide con PE: $Name" }
    $section = $sections | Where-Object { $offset -ge $_.raw -and ($offset + $tableBytes.Length) -le ($_.raw + $_.size) } | Select-Object -First 1
    if (!$section) { throw "Tabla fuera de seccion: $Name" }
    [ordered]@{
        table = $Name
        bytes = $tableBytes.Length
        sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($tableBytes)).ToLowerInvariant()
        va = ('0x{0:x8}' -f ($section.va + $offset - $section.raw))
        identifies_exact_version = $false
    }
}
$evidence['baseline_tables'] = @(
    (Get-TableEvidence "$vorbis/lib/floor1.c" 'FLOOR1_fromdB_LOOKUP\s*\[256\]\s*=\s*\{(.*?)\}' 'float' 'FLOOR1_fromdB_LOOKUP'),
    (Get-TableEvidence "$ogg/src/framing.c" 'crc_lookup\s*\[256\]\s*=\s*\{(.*?)\}' 'integer' 'crc_lookup')
)
$evidence | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$out/pe-evidence.json" -Encoding utf8NoBOM
# Sustituye exclusivamente los tipos que normalmente genera configure.
$configTypes = @'
#ifndef VITA_LIBOGG_CONFIG_TYPES_H
#define VITA_LIBOGG_CONFIG_TYPES_H
#include <stdint.h>
typedef int16_t ogg_int16_t;
typedef uint16_t ogg_uint16_t;
typedef int32_t ogg_int32_t;
typedef uint32_t ogg_uint32_t;
typedef int64_t ogg_int64_t;
#endif
'@
Set-Content -LiteralPath "$ogg/include/ogg/config_types.h" -Value $configTypes -Encoding ascii
Copy-Item -LiteralPath "$z/zlib.h", "$z/zconf.h", "$png/png.h", "$png/pngconf.h" -Destination "$out/include" -Force
Copy-Item -LiteralPath "$ogg/include/ogg", "$vorbis/include/vorbis" -Destination "$out/include" -Recurse -Force
Copy-Item -LiteralPath "$z/README" -Destination "$out/licenses/zlib-README.txt" -Force
Copy-Item -LiteralPath "$png/LICENSE" -Destination "$out/licenses/libpng-LICENSE.txt" -Force
Copy-Item -LiteralPath "$ogg/COPYING" -Destination "$out/licenses/libogg-COPYING.txt" -Force
Copy-Item -LiteralPath "$vorbis/COPYING" -Destination "$out/licenses/libvorbis-COPYING.txt" -Force
$commonFlags = @('-std=gnu11', '-O2', '-fno-strict-aliasing', '-ffp-contract=off', '-ffunction-sections', '-fdata-sections', '-DHAVE_ALLOCA_H', '-DHAVE_UNISTD_H', '-DPNG_NO_ASSEMBLER_CODE', '-I', "$out/include")
function Build-Archive([string]$Compiler, [string]$Archiver, [string]$Destination, [string]$Name, [string]$SourceDirectory, [string[]]$Sources) {
    $objectDir = Join-Path $Destination "obj/$Name"
    New-Item -ItemType Directory -Force -Path $objectDir, "$Destination/lib" | Out-Null
    $objects = @(foreach ($source in $Sources) {
        $object = Join-Path $objectDir "$source.o"
        & $Compiler @commonFlags '-I' $SourceDirectory '-c' (Join-Path $SourceDirectory "$source.c") '-o' $object
        if ($LASTEXITCODE -ne 0) { throw "Compilacion fallida: $Name/$source" }
        $object
    })
    $library = Join-Path $Destination "lib/$Name.a"
    if (Test-Path -LiteralPath $library) { Remove-Item -LiteralPath $library }
    & $Archiver 'rcsD' $library @objects
    if ($LASTEXITCODE -ne 0) { throw "Archive fallido: $Name" }
}
function Build-Libraries([string]$Compiler, [string]$Archiver, [string]$Destination) {
    Build-Archive $Compiler $Archiver $Destination 'libz' $z @('adler32', 'compress', 'crc32', 'gzio', 'uncompr', 'deflate', 'trees', 'zutil', 'inflate', 'infback', 'inftrees', 'inffast')
    Build-Archive $Compiler $Archiver $Destination 'libpng' $png @('png', 'pngerror', 'pngget', 'pngmem', 'pngpread', 'pngread', 'pngrio', 'pngrtran', 'pngrutil', 'pngset', 'pngtrans', 'pngwio', 'pngwrite', 'pngwtran', 'pngwutil')
    Build-Archive $Compiler $Archiver $Destination 'libogg' "$ogg/src" @('framing', 'bitwise')
    Build-Archive $Compiler $Archiver $Destination 'libvorbis' "$vorbis/lib" @('mdct', 'smallft', 'block', 'envelope', 'window', 'lsp', 'lpc', 'analysis', 'synthesis', 'psy', 'info', 'floor1', 'floor0', 'res0', 'mapping0', 'registry', 'codebook', 'sharedbook', 'lookup', 'bitrate')
    Build-Archive $Compiler $Archiver $Destination 'libvorbisfile' "$vorbis/lib" @('vorbisfile')
    Build-Archive $Compiler $Archiver $Destination 'libvorbisenc' "$vorbis/lib" @('vorbisenc')
}
Build-Libraries $cc $ar $out
$smoke = Join-Path $PSScriptRoot 'smoke_test.c'
$linkLibraries = @('-lvorbisfile', '-lvorbisenc', '-lvorbis', '-logg', '-lpng', '-lz', '-lm')
& $cc @commonFlags '-Wall' '-Wextra' '-Werror' '-Wl,-q,--gc-sections' $smoke '-L' "$out/lib" @linkLibraries '-lSceIofilemgr_stub' '-lSceProcessmgr_stub' '-o' "$out/smoke.elf"
if ($LASTEXITCODE -ne 0) { throw 'Fallo al enlazar smoke.elf' }
& $elfCreate "$out/smoke.elf" "$out/smoke.velf"
if ($LASTEXITCODE -ne 0) { throw 'vita-elf-create fallo' }
& $makeSelf '-c' "$out/smoke.velf" "$out/smoke.self"
if ($LASTEXITCODE -ne 0) { throw 'vita-make-fself fallo' }
$hostResult = 'No ejecutado'
if ($HostSmoke) {
    if (!(Test-Path -LiteralPath $HostCompiler -PathType Leaf)) { throw "Falta compilador host: $HostCompiler" }
    $hostBin = Split-Path $HostCompiler -Parent
    $hostAr = Join-Path $hostBin 'ar.exe'
    if (!(Test-Path -LiteralPath $hostAr -PathType Leaf)) { throw "Falta archiver host: $hostAr" }
    $previousPath = $env:PATH
    $vitaFlags = $commonFlags
    try {
        $env:PATH = "$hostBin;$previousPath"
        # MinGW proporciona alloca desde malloc.h (rama _WIN32 de os.h).
        $commonFlags = @($commonFlags | Where-Object { $_ -ne '-DHAVE_ALLOCA_H' })
        Build-Libraries $HostCompiler $hostAr "$out/host"
        & $HostCompiler @commonFlags '-Wall' '-Wextra' '-Werror' $smoke '-L' "$out/host/lib" @linkLibraries '-o' "$out/host/smoke.exe"
        if ($LASTEXITCODE -ne 0) { throw 'Fallo al enlazar smoke.exe' }
        # Una excepcion de Windows puede dejar un proceso esperando un dialogo.
        # Solo se termina este proceso propio si no sale dentro del limite.
        $hostProcess = Start-Process -FilePath "$out/host/smoke.exe" -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput "$out/host/smoke-result.txt" -RedirectStandardError "$out/host/smoke-error.txt"
        if (!$hostProcess.WaitForExit(30000)) {
            $hostProcess.Kill()
            $hostProcess.WaitForExit()
            throw 'Prueba host excedio 30 segundos; se termino su proceso.'
        }
        Get-Content -LiteralPath "$out/host/smoke-result.txt", "$out/host/smoke-error.txt"
        if ($hostProcess.ExitCode -ne 0) { throw "Prueba host fallo: $($hostProcess.ExitCode)" }
        $hostResult = 'Paso: smoke.exe termino con codigo 0'
    } finally { $env:PATH = $previousPath; $commonFlags = $vitaFlags }
}
$libraries = foreach ($library in Get-ChildItem -LiteralPath "$out/lib" -Filter '*.a' | Sort-Object Name) {
    [ordered]@{ name = $library.Name; bytes = $library.Length; sha256 = (Get-FileHash -LiteralPath $library.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$manifest = [ordered]@{
    pe_sha256 = $peSha
    compiler = (& $cc '--version' | Select-Object -First 1)
    flags = $commonFlags
    packages = $packages
    libraries = @($libraries)
    smoke_self_bytes = (Get-Item -LiteralPath "$out/smoke.self").Length
    smoke_self_sha256 = (Get-FileHash -LiteralPath "$out/smoke.self" -Algorithm SHA256).Hash.ToLowerInvariant()
    smoke_vita_executed = $false
    smoke_host = $hostResult
}
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath "$out/build-manifest.json" -Encoding utf8NoBOM
$libraries | ForEach-Object { Write-Output "$($_.name): $($_.bytes) bytes $($_.sha256)" }
Write-Output "Compilacion Vita OK: $out/smoke.self (no ejecutada en Vita3K ni hardware)"
