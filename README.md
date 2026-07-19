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

Änderungen zuerst bewusst nach `main` in das private GitHub-Repository übertragen.
Danach kann der ohnehin auf dem Raspberry Pi installierte, sichere Wochenlauf auch
manuell gestartet werden:

```powershell
.\scripts\publish_to_pi.ps1
```

Das Windows-Skript kopiert und löscht keine Dateien. Es startet nur den Dienst auf dem
Raspberry Pi. Der Pi holt den freigegebenen GitHub-Stand, prüft das neueste Backup,
baut ein neues Release und schaltet erst nach erfolgreicher Prüfung den Nginx-Zeiger
atomar um. Ein fehlerhafter Build ersetzt daher nicht das zuletzt funktionierende Wiki.

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

1. Der Pi lädt zuerst ausschließlich einen geradlinig vorausliegenden, bereits
   freigegebenen Stand von `main`. Abweichende Git-Verläufe werden nicht automatisch
   zusammengeführt.
2. Das neueste **gültige Home-Assistant-Backup** wird im nur lesbar eingebundenen
   NAS-Ordner gesucht.
3. Ausschließlich Automationen, Szenen, Raum-, Geräte- und Entity-Register sowie
   das Dashboard-Verzeichnis und die fest benannten Dashboard-Dateien werden im
   Datenstrom entschlüsselt. Das vollständige Backup wird nicht entpackt.
4. Ein semantischer Vergleich übermittelt nur geänderte Automationen an das kleine,
   fest angeheftete OpenAI-Modell. Ohne Änderungen erfolgt nur eine minimale
   Guthabenprobe. Ein reiner Dashboard-Prüfstopp löst keine Guthabenprobe aus.
   Dashboard-Änderungen werden vollständig lokal erkannt. Die API speichert die
   Anfrage nicht (`store: false`).
5. Der Generator läuft zweimal. Stimmen beide Ergebnisse nicht exakt überein,
   fehlen Inhalte oder sieht ein Text wie ein Geheimnis aus, wird abgebrochen.
6. Eine geänderte Dashboard-Struktur verlangt eine bewusste Prüfung der bebilderten
   Seiten. So gelangen keine veralteten Dashboard-Bilder unbemerkt ins Wiki.
7. Erst nach strengem MkDocs-Build werden die erzeugten Seiten nach GitHub
   übertragen. Danach schaltet der Pi atomar auf das neue Release um und prüft die
   echte Startseite. Bei einem Fehler bleibt beziehungsweise wird die letzte
   funktionierende Version aktiv.
8. Home Assistant meldet Erfolg, Prüfbedarf, Backup-/GitHub-Fehler und insbesondere
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
sudo bash /srv/homeassistant-wiki/source/raspberry-pi/wiki-weekly-install.sh
```

Ein manueller Lauf kann zusätzlich über die Home-Assistant-Automation
„System: Wiki jetzt aktualisieren“ gestartet werden. Home Assistant veröffentlicht
dabei eine nicht gespeicherte MQTT-Nachricht mit einem zufälligen, nur lokal
hinterlegten Freigabewert. Der Pi ignoriert falsche Nachrichten, Doppelstarts und
weitere Startversuche innerhalb von 60 Sekunden. Abschluss oder Fehler werden über
die bestehende iPhone-Statusmeldung gemeldet.

## Wiki in der Home-Assistant-Seitenleiste

Die lokale App unter `home-assistant-apps/homewiki_gateway` stellt das Wiki über
Home Assistant Ingress bereit. Dadurch funktioniert der Seitenleisteneintrag über
die Home-Assistant-App auch von unterwegs mit Home Assistant Cloud, ohne VPN und
ohne öffentliche Portfreigabe für den Raspberry Pi. Die App ist nur ein
abgesicherter Proxy; Build, Veröffentlichung und Datenhaltung bleiben auf dem Pi.

## Grundsätze

- Verständliche Alltagssprache steht vor technischen Details.
- Keine Passwörter, Tokens, Alarmcodes oder sonstigen Geheimnisse eintragen.
- Jede Seite erhält ein Datum „Zuletzt geprüft“.
- Technische Namen und Entity-IDs werden nur auf bewusst geprüften Wartungsseiten ergänzt, wo sie bei der Fehlersuche helfen.
- Unklare Fakten werden als offen markiert und nicht erfunden.
