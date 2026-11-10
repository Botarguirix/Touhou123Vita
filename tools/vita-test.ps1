# Ciclo de prueba por red con vitacompanion (FTP 1337, comandos 1338).
# Uso:  .\tools\vita-test.ps1 -Ip 192.168.3.50 [-Action launch|quit|pull|push|reboot|cmd] [-Vpk ruta] [-Cmd "texto"]
param(
    [Parameter(Mandatory)][string]$Ip,
    [ValidateSet('launch','quit','pull','push','reboot','cmd','version')][string]$Action = 'pull',
    [string]$TitleId = 'THSV12302',
    [string]$Vpk,
    [string]$Cmd,
    [string]$Out = "$PSScriptRoot\..\artifacts\vita-traces"
)
$ErrorActionPreference = 'Stop'
$data = "ux0:/data/touhou123vita"

function Send-Cmd([string]$text) {
    $c = [Net.Sockets.TcpClient]::new($Ip, 1338)
    $s = $c.GetStream()
    $b = [Text.Encoding]::ASCII.GetBytes("$text`n")
    $s.Write($b, 0, $b.Length)
    Start-Sleep -Milliseconds 400
    $buf = New-Object byte[] 4096
    $r = ''
    while ($s.DataAvailable) { $n = $s.Read($buf, 0, $buf.Length); $r += [Text.Encoding]::ASCII.GetString($buf, 0, $n) }
    $c.Close()
    $r
}
function Ftp-Get([string]$remote, [string]$local) {
    & curl.exe -s --fail -o $local "ftp://${Ip}:1337/$remote"
}
function Ftp-Put([string]$local, [string]$remote) {
    & curl.exe -s --fail -T $local "ftp://${Ip}:1337/$remote"
}

switch ($Action) {
    'version' { Send-Cmd 'version' }
    'launch'  { Send-Cmd "launch $TitleId" }
    'quit'    { Send-Cmd "quit $TitleId" }
    'reboot'  { Send-Cmd 'reboot' }
    'cmd'     { Send-Cmd $Cmd }
    'pull' {
        New-Item $Out -ItemType Directory -Force | Out-Null
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        foreach ($f in 'recomp-trace.log','recomp-result.txt') {
            $dst = Join-Path $Out "$stamp-$f"
            Ftp-Get "$data/$f" $dst
            if (Test-Path $dst) { "$dst  ($((Get-Item $dst).Length) bytes)" }
        }
    }
    'push' {
        # sube un archivo de configuracion o dato al directorio del juego, p. ej. -Vpk ...\vsync-off.txt
        if (-not $Vpk) { throw 'indica el archivo con -Vpk' }
        Ftp-Put $Vpk "$data/$(Split-Path $Vpk -Leaf)"
        "subido a $data"
    }
}
