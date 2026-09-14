# Haus-Wiki 3.0

Das Wiki erklärt das Zuhause aus dem zuletzt verarbeiteten Home-Assistant-Backup. Es zeigt keine Live-Zustände und schaltet keine Geräte. Bewohner finden Räume, Geräte, Abläufe und Hilfe; die Verwaltung enthält Aktualisierung, Anmeldung, Verlauf, Betriebsprotokoll und eigene Seiten.

## Einrichtung und Zugriff

1. NAS unter Home Assistant → Einstellungen → System → Speicher als **Share** einbinden. Backup-Netzwerkspeicher sind nicht automatisch unter /share im Wiki verfügbar.
2. `export_path` auf einen eigenen Unterordner setzen, etwa `/share/NASWiki/HausWiki`. Das Wiki verwaltet diesen Unterordner vollständig. Nicht das Stammverzeichnis mit den HA-Backups als Exportziel verwenden.
3. `backup_password` mit dem Verschlüsselungscode aus dem Home-Assistant-Notfallpaket befüllen.
4. Über die HA-Seitenleiste öffnen. Ohne `admin_password` erhalten die in `admin_users` eingetragenen HA-Benutzernamen, Anzeigenamen oder Benutzer-IDs Verwaltungsrechte. Die Prüfung berücksichtigt den Anzeigenamen „Max“ unabhängig vom technischen Benutzernamen.
5. Alternativ `admin_password` konfigurieren. Dann werden Verwaltungsaktionen nach Eingabe dieses Passworts im Wiki freigeschaltet. Die Freischaltung gilt eine Stunde, ist an den HA-Benutzer gebunden und endet bei App-Neustart oder Passwortwechsel. Das Passwort wird nicht im Browser gespeichert.

Lesende Zugriffe funktionieren über Home Assistant Ingress. Direkte Zugriffe aus anderen Containern sind gesperrt; der reduzierte Health-Endpunkt bleibt für Betriebsprüfungen erreichbar.

## Aktualisierung

Standard: Mittwoch und Sonntag um 02:00 Uhr in der Home-Assistant-Zeitzone. `schedule_days`, `schedule_time` und `catch_up` steuern den Rhythmus. Ein manueller Klick meldet, ob der Lauf gestartet wurde oder bereits läuft.

Die App wartet auf laufende Supervisor-Backup-Jobs. Automatische NAS-Archive werden auf eingebundenen Share-Freigaben erkannt; andernfalls wird der Supervisor-Katalog verwendet. Nur ein lesbares und validiertes HA-Archiv kann veröffentlicht werden. Das verwendete Backup wird im Status ausgewiesen. Bei unverändertem Inhalt wird Home Assistant benachrichtigt.

Die Website wird lokal bereitgestellt und nach `export_path` exportiert. `release_retention` bestimmt die Anzahl früherer Wiki-Stände (Standard: 3). Eine Wiederherstellung ersetzt ausschließlich das Wiki. Während einer Aktualisierung ist sie gesperrt.

## Codex, Claude und LLM

`llm_provider` wählt `codex`, `claude`, `api` oder `disabled` (`chatgpt` bleibt als alter Migrationswert kompatibel). Bei `codex` startet „Codex anmelden“ die Device-Anmeldung des mitgelieferten Codex-CLI. Bei `claude` startet „Claude anmelden“ den offiziellen Claude-Code-Login; bei Claude Pro/Max erfolgt die OAuth-Bestätigung im Browser. Alternativ kann `anthropic_api_key` als geschütztes Add-on-Geheimnis gesetzt werden. Die Oberfläche passt Link, Status und Schaltflächen automatisch an.

Abgelaufene Codes werden während einer aktiven Anmeldung erneuert. Wiederholte technische Fehler führen zu einem sichtbaren Fehler statt einer endlosen Anmeldeschleife. Die Anmeldung kann abgebrochen werden.

Ein fertig erzeugtes Wiki bedeutet nicht automatisch einen erfolgreichen LLM-Aufruf; fehlende Ergänzungen bleiben sichtbar. Geheimnisse werden vor LLM-Anfragen entfernt. Bei erschöpftem Kontingent wird mit `quota_retry_minutes` erneut versucht; es gibt keinen automatischen kostenpflichtigen Anbieter-Fallback. `model` ist optional (`sonnet` ist der Claude-Standard); `openai_api_key` und `anthropic_api_key` werden nur für den jeweils ausdrücklich gewählten API-Modus benötigt.

Codex-Zugangsdaten liegen unter `/data/codex-home`, Claude-Zugangsdaten unter `/data/claude-home`; beide Verzeichnisse sind von HA-App-Backups ausgeschlossen. Nach Wiederherstellung kann eine erneute Anmeldung nötig sein.

## Eigene Seiten

Eigene Anleitungen liegen getrennt unter /data/manual und werden weder vom Generator noch vom LLM überschrieben. Der Editor speichert Markdown; die Veröffentlichung erfolgt mit einem erfolgreichen Backup-basierten Lauf. Keine Passwörter oder Zugangscodes in Wiki-Seiten eintragen.

## Betriebsprotokoll

Die Verwaltung zeigt Ereignisse mit Zeitpunkt, Schweregrad, Laufbezug und Verarbeitungsschritt. Dieselben Ereignisse erscheinen in den Container-Logs. Die lokalen rotierenden Dateien unter /data/logs belegen höchstens etwa 1 MB. Zugangsdaten, Device-Codes und rohe LLM-Antworten werden nicht protokolliert. Alte Läufe aus Version 2 bleiben im Verlauf erhalten; detaillierte Ereignisse werden ab Version 3 aufgezeichnet.

## Updates und interne API

Updates werden über das öffentliche GitHub-Repository und GHCR angeboten. Private Wiki-Inhalte werden nicht nach GitHub übertragen. Bestehende Optionen, eigene Seiten, Zugangsdaten und Wiki-Stände bleiben unter /data erhalten.

Die interne Oberfläche verwendet api/status, api/history, api/logs, api/manual, api/auth/device/status. Schreibzugriffe benötigen Ingress, Verwaltungsrechte und den Header `X-Haus-Wiki: 1`. Dies ist keine öffentlich freizugebende API.
