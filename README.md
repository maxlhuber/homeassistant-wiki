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

Beim Wochenlauf wird `metadata.inventory_source_date` aus dem geprüften Backup
übernommen. `metadata.live_checked_date` (Datum tatsächlich live geprüfter
Ergänzungen und Statuswerte) rückt dagegen nie automatisch weiter, damit ein Backup
nicht fälschlich als aktueller Live-Abgleich erscheint.

Die Familienansicht filtert deaktivierte Entitäten, Diagnose- und Konfigurationswerte,
interne Dienste, virtuelle Gruppen und erkennbare Duplikate. Ein abgeleiteter Standort
wird im Wiki ausdrücklich anders gekennzeichnet als ein in Home Assistant bestätigter Raum.

## Automatische Wochenaktualisierung auf dem Raspberry Pi

Der Raspberry Pi erledigt den vollständigen Lauf sonntags ab 06:00 Uhr selbstständig;
ein eingeschalteter PC ist nicht erforderlich. Der Ablauf ist absichtlich streng:

1. Das neueste **gültige Home-Assistant-Backup** wird im nur lesbar eingebundenen
   NAS-Ordner gesucht.
2. Ausschließlich Automationen, Szenen sowie Raum-, Geräte- und Entity-Register
   werden im Datenstrom entschlüsselt. Das vollständige Backup wird nicht entpackt.
3. Ein semantischer Vergleich übermittelt nur geänderte Automationen an das kleine,
   fest angeheftete OpenAI-Modell. Ohne Änderungen erfolgt nur eine minimale
   Guthabenprobe. Die API speichert die Anfrage nicht (`store: false`).
4. Der Generator läuft zweimal. Stimmen beide Ergebnisse nicht exakt überein,
   fehlen Inhalte oder sieht ein Text wie ein Geheimnis aus, wird abgebrochen.
5. Erst nach strengem MkDocs-Build werden die erzeugten Seiten nach GitHub
   übertragen. Danach schaltet der Pi atomar auf das neue Release um und prüft die
   echte Startseite. Bei einem Fehler bleibt beziehungsweise wird die letzte
   funktionierende Version aktiv.
6. Home Assistant meldet Erfolg, Prüfbedarf, Backup-/GitHub-Fehler und insbesondere
   aufgebrauchtes OpenAI-Guthaben an das iPhone. Ist Home Assistant kurzzeitig nicht
   erreichbar, bleibt die Meldung in einer lokalen Warteschlange.

Geheimnisse liegen ausschließlich als root-geschützte Dateien unter
`/etc/homeassistant-wiki`. Der NAS-Zugriff ist `ro,nosuid,nodev,noexec` eingebunden.
Ein neuer OpenAI-Schlüssel wird auf dem Pi interaktiv mit folgendem Befehl hinterlegt:

```bash
sudo homeassistant-wiki-set-openai-key
```

Wenn eine sicherheitsrelevante oder ungewöhnlich große Änderung bewusst geprüft
werden muss, bleibt das bisherige Wiki aktiv. Nach der Prüfung wird exakt dieser
Stand einmalig freigegeben mit:

```bash
sudo homeassistant-wiki-approve-review
```

Installation beziehungsweise Reparatur der Pi-Dienste:

```bash
sudo /srv/homeassistant-wiki/source/raspberry-pi/wiki-weekly-install.sh
```

## Grundsätze

- Verständliche Alltagssprache steht vor technischen Details.
- Keine Passwörter, Tokens, Alarmcodes oder sonstigen Geheimnisse eintragen.
- Jede Seite erhält ein Datum „Zuletzt geprüft“.
- Technische Namen und Entity-IDs werden nur dort ergänzt, wo sie bei der Fehlersuche helfen.
- Unklare Fakten werden als offen markiert und nicht erfunden.
