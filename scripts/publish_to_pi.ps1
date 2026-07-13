[CmdletBinding()]
param(
    [string]$HostName = 'homeassistant-wiki.local',
    [string]$UserName = 'wikiadmin',
    [string]$KeyFile = "$env:USERPROFILE\.ssh\homeassistant-wiki_ed25519"
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$archive = Join-Path $env:TEMP 'homeassistant-wiki-update.tar.gz'
$updateScript = Join-Path $projectRoot 'raspberry-pi\wiki-update.sh'
$nginxConfig = Join-Path $projectRoot 'raspberry-pi\nginx-homeassistant-wiki.conf'

if (-not (Test-Path -LiteralPath $KeyFile)) {
    throw "SSH-Schlüssel nicht gefunden: $KeyFile"
}
if (-not (Test-Path -LiteralPath $updateScript) -or -not (Test-Path -LiteralPath $nginxConfig)) {
    throw 'Die Raspberry-Pi-Aktualisierungsdateien fehlen.'
}

Push-Location $projectRoot
try {
    $localPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $localPython)) {
        throw "Lokale Python-Umgebung fehlt: $localPython"
    }
    & $localPython -m mkdocs build --clean --strict
    if ($LASTEXITCODE -ne 0) {
        throw 'Die lokale strikte Wiki-Prüfung ist fehlgeschlagen. Es wird nichts veröffentlicht.'
    }
    if (Test-Path -LiteralPath $archive) {
        Remove-Item -LiteralPath $archive -Force
    }
    & tar.exe -czf $archive mkdocs.yml requirements.txt docs
    if ($LASTEXITCODE -ne 0) {
        throw 'Das Wiki-Paket konnte nicht erstellt werden.'
    }
}
finally {
    Pop-Location
}

$sshTarget = "${UserName}@${HostName}"
$sshOptions = @('-i', $KeyFile, '-o', 'StrictHostKeyChecking=accept-new')

& scp.exe @sshOptions $archive $updateScript $nginxConfig "${sshTarget}:/tmp/"
if ($LASTEXITCODE -ne 0) {
    throw 'Das Wiki-Paket konnte nicht auf den Raspberry Pi kopiert werden.'
}

$remoteCommand = @'
set -e
rm -rf /tmp/homeassistant-wiki-source
mkdir -p /tmp/homeassistant-wiki-source
tar -xzf /tmp/homeassistant-wiki-update.tar.gz -C /tmp/homeassistant-wiki-source
rsync -a --delete /tmp/homeassistant-wiki-source/ /srv/homeassistant-wiki/source/
sudo install -m 0755 /tmp/wiki-update.sh /usr/local/sbin/wiki-update
sudo /usr/local/sbin/wiki-update
sudo install -m 0644 /tmp/nginx-homeassistant-wiki.conf /etc/nginx/sites-available/homeassistant-wiki
sudo nginx -t
sudo systemctl reload nginx.service
rm -rf /tmp/homeassistant-wiki-source /tmp/homeassistant-wiki-update.tar.gz /tmp/wiki-update.sh /tmp/nginx-homeassistant-wiki.conf
'@

& ssh.exe @sshOptions $sshTarget $remoteCommand
if ($LASTEXITCODE -ne 0) {
    throw 'Das Wiki konnte auf dem Raspberry Pi nicht aktualisiert werden.'
}

Write-Host "Fertig: http://$HostName/"
