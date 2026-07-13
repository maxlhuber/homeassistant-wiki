# Home-Assistant-Wiki

Dieses Projekt enthält die verständliche Dokumentation unseres Smart Homes.

## Lokale Vorschau

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m mkdocs serve
```

Danach ist das Wiki normalerweise unter <http://127.0.0.1:8000> erreichbar.

## Website erzeugen

```powershell
.venv\Scripts\python -m mkdocs build --clean
```

Die fertige Website liegt anschließend im Ordner `site`.

## Auf dem Raspberry Pi veröffentlichen

```powershell
.\scripts\publish_to_pi.ps1
```

Das Skript führt zuerst einen lokalen Strict-Build aus. Auf dem Raspberry Pi wird
anschließend in ein neues Release-Verzeichnis gebaut; erst nach erfolgreichem Build
wird der Nginx-Zeiger atomar umgeschaltet. Ein fehlerhafter Build ersetzt daher nicht
das zuletzt funktionierende Wiki.

## Inventarseiten aktualisieren

Nach dem sicheren Extrahieren der ausgewählten Home-Assistant-Dateien nach
`eingang/work/data` werden die Raum-, Geräte- und Automationsseiten so neu erzeugt:

```powershell
.venv\Scripts\python scripts\generate_docs.py eingang\work\data docs
.venv\Scripts\python -m mkdocs build --clean
```

Der Generator liest keine Zugangsdaten, Cloud-Dateien, Verlaufsdatenbank oder
`secrets.yaml`. Die Geräte- und Entity-Registries werden benötigt, um Beziehungen
zwischen Geräten, Räumen und Automationen aufzulösen. Gerätekennungen, Verbindungen
und eindeutige IDs daraus werden **nicht veröffentlicht**. Automatisch erzeugte
Seiten sind am Hinweis am Dateianfang erkennbar und werden bei der nächsten
Aktualisierung ersetzt.

Dauerhafte Korrekturen und vorsichtige Standortzuordnungen stehen in
`scripts/wiki_overrides.yaml`. Diese Datei enthält ausschließlich Dokumentationsdaten
und keine Geheimnisse. Änderungen an generierten Seiten gehören in diese Datei oder
in den Generator, weil direkte Änderungen beim nächsten Lauf überschrieben werden.

Bei jedem neuen Backup müssen dort außerdem
`metadata.inventory_source_date` (Stichtag des importierten Backups) und
`metadata.live_checked_date` (Datum der tatsächlich live geprüften Ergänzungen und
Statuswerte) bewusst aktualisiert werden. Der Generator rückt diese Daten nicht
automatisch weiter, damit ein altes Backup nie als aktueller Live-Abgleich erscheint.

Die Familienansicht filtert deaktivierte Entitäten, Diagnose- und Konfigurationswerte,
interne Dienste, virtuelle Gruppen und erkennbare Duplikate. Ein abgeleiteter Standort
wird im Wiki ausdrücklich anders gekennzeichnet als ein in Home Assistant bestätigter Raum.

## Grundsätze

- Verständliche Alltagssprache steht vor technischen Details.
- Keine Passwörter, Tokens, Alarmcodes oder sonstigen Geheimnisse eintragen.
- Jede Seite erhält ein Datum „Zuletzt geprüft“.
- Technische Namen und Entity-IDs werden nur dort ergänzt, wo sie bei der Fehlersuche helfen.
- Unklare Fakten werden als offen markiert und nicht erfunden.
