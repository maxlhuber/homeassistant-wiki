# Projektanweisungen

## Zentrale Geheimnisse

Die projektweiten Zugangsdaten liegen ausschließlich lokal und mit Windows DPAPI
für den aktuellen Windows-Benutzer verschlüsselt in:

`/.project-secrets/project-secrets.json`

Verfügbare Namen:

- `NasUsername`
- `NasPassword`
- `BackupEncryptionCode`

Zum Verwenden zuerst `scripts/ProjectSecrets.psm1` importieren und dann
`Get-HomeWikiProjectSecret -Name <Name>` aufrufen. Den Rückgabewert nur direkt
an den benötigten Prozess übergeben.

Geheimnisse niemals in Ausgaben, Logs, Git, Dokumentation, Prompts oder
Fehlermeldungen schreiben. Die verschlüsselte Datei darf ebenfalls nicht
committet oder auf GitHub hochgeladen werden.

Der Raspberry Pi besitzt unter `/etc/homeassistant-wiki/` eigene, nur für root
lesbare Betriebskopien. Diese dürfen nicht in das Repository kopiert werden.
