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

## Inventarseiten aktualisieren

Nach dem sicheren Extrahieren der ausgewählten Home-Assistant-Dateien nach
`eingang/work/data` werden die Raum-, Geräte- und Automationsseiten so neu erzeugt:

```powershell
.venv\Scripts\python scripts\generate_docs.py eingang\work\data docs
.venv\Scripts\python -m mkdocs build --clean
```

Der Generator liest keine Zugangsdaten, Cloud-Dateien, Verlaufsdatenbank,
Gerätekennungen oder `secrets.yaml`. Automatisch erzeugte Seiten sind am Hinweis
am Dateianfang erkennbar und werden bei der nächsten Aktualisierung ersetzt.

## Grundsätze

- Verständliche Alltagssprache steht vor technischen Details.
- Keine Passwörter, Tokens, Alarmcodes oder sonstigen Geheimnisse eintragen.
- Jede Seite erhält ein Datum „Zuletzt geprüft“.
- Technische Namen und Entity-IDs werden nur dort ergänzt, wo sie bei der Fehlersuche helfen.
