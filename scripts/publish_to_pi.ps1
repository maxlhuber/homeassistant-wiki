[CmdletBinding()]
param(
    [string]$HostName = 'homeassistant-wiki.local',
    [string]$UserName = 'wikiadmin',
    [string]$KeyFile = "$env:USERPROFILE\.ssh\homeassistant-wiki_ed25519"
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$archive = Join-Path $env:TEMP 'homeassistant-wiki-update.tar.gz'

if (-not (Test-Path -LiteralPath $KeyFile)) {
    throw "SSH-Schlüssel nicht gefunden: $KeyFile"
}

Push-Location $projectRoot
try {
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

& scp.exe @sshOptions $archive "${sshTarget}:/tmp/homeassistant-wiki-update.tar.gz"
if ($LASTEXITCODE -ne 0) {
    throw 'Das Wiki-Paket konnte nicht auf den Raspberry Pi kopiert werden.'
}

$remoteCommand = @'
set -e
rm -rf /tmp/homeassistant-wiki-source
mkdir -p /tmp/homeassistant-wiki-source
tar -xzf /tmp/homeassistant-wiki-update.tar.gz -C /tmp/homeassistant-wiki-source
rsync -a --delete /tmp/homeassistant-wiki-source/ /srv/homeassistant-wiki/source/
sudo /usr/local/sbin/wiki-update
rm -rf /tmp/homeassistant-wiki-source /tmp/homeassistant-wiki-update.tar.gz
'@

& ssh.exe @sshOptions $sshTarget $remoteCommand
if ($LASTEXITCODE -ne 0) {
    throw 'Das Wiki konnte auf dem Raspberry Pi nicht aktualisiert werden.'
}

Write-Host "Fertig: http://$HostName/"
