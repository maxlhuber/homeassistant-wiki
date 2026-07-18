[CmdletBinding()]
param(
    [string]$HostName = 'homeassistant-wiki.local',
    [string]$UserName = 'wikiadmin',
    [string]$KeyFile = "$env:USERPROFILE\.ssh\homeassistant-wiki_ed25519"
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $KeyFile -PathType Leaf)) {
    throw "SSH-Schlüssel nicht gefunden: $KeyFile"
}

$sshTarget = "${UserName}@${HostName}"
$sshOptions = @(
    '-i', $KeyFile,
    '-o', 'IdentitiesOnly=yes',
    '-o', 'StrictHostKeyChecking=accept-new'
)

Write-Host 'Der sichere Wiki-Wochenlauf wird auf dem Raspberry Pi gestartet.'
& ssh.exe @sshOptions $sshTarget 'sudo systemctl start --no-block wiki-weekly.service'
if ($LASTEXITCODE -ne 0) {
    throw 'Der Wiki-Dienst konnte auf dem Raspberry Pi nicht gestartet werden.'
}

Write-Host "Gestartet. Der Abschluss wird per iPhone gemeldet: http://$HostName/"
