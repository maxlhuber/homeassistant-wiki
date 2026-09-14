# Haus-Wiki für Home Assistant

Haus-Wiki ist eine Home-Assistant-App für HAOS. Sie erzeugt aus dem neuesten
vollständigen Home-Assistant-Backup eine verständliche, statische Dokumentation
und stellt sie über Home Assistant Ingress in der Seitenleiste bereit.

Wiki-Inhalte und Anmeldedaten werden nicht in dieses Repository geschrieben. Das
Repository enthält nur Quellcode und eine neutrale Startseite. Der erzeugte Stand
liegt im App-Datenspeicher und wird zusätzlich nach `/share/HausWiki` exportiert.

## Eigenschaften

- Vollautomatischer Lauf am Mittwoch und Sonntag um 02:00 Uhr (konfigurierbar)
- Kein Lauf ohne lesbares Vollbackup; laufende Backups werden abgewartet
- Lokaler semantischer Abgleich, sodass unveränderte Backups keinen Neuaufbau auslösen
- Anmeldung über den offiziellen Codex-CLI oder Claude Code (Claude Pro/Max OAuth), alternativ OpenAI API
- Providerabhängige Anmeldung und Schaltflächen; optionaler Anthropic-API-Key
- Keine manuellen LLM-Freigaben oder Prüfstopps
- Bereinigte, auf geänderte Automationen begrenzte LLM-Eingaben
- Home-Assistant-Benachrichtigungen, Versionsaufbewahrung und Rollback
- Geschützte manuelle Seiten, die Generator und LLM nicht verändern
- Multi-Architektur-Image für `amd64` und `aarch64`

## Installation

Die Repository-URL im Home-Assistant-App-Store hinzufügen:

```text
https://github.com/maxlhuber/homeassistant-wiki
```

Danach **Haus-Wiki** installieren, die Optionen setzen, starten und in der
Seitenleiste öffnen. Die vollständige Einrichtung ist in
[`homewiki_gateway/DOCS.md`](homewiki_gateway/DOCS.md)
beschrieben.

## Entwicklung und Prüfung

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m mkdocs build --clean --strict
```

Ein Push nach `main`, der die App ändert, testet den Stand und veröffentlicht das
Container-Image in der GitHub Container Registry. Die `version` in `config.yaml`
ist zugleich der Image-Tag, den Home Assistant als App-Update erkennt.

## Datenschutz und Sicherheit

Aus Backups werden ausschließlich die für Inventar, Automationen, Szenen und
Dashboards benötigten Dateien in einem temporären Arbeitsbereich gelesen.
Geheimnisähnliche Inhalte blockieren die Veröffentlichung. Das LLM erhält weder
Backup-Dateien noch echte Automationsnamen, Zugangsdaten oder personenbezogene
Freitexte. Die aktive Wiki-Version wird erst nach reproduzierbarer Generierung und
strengem MkDocs-Build atomar ersetzt.
