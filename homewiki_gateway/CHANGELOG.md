# 4.0.0

- Neu gestaltet: Haus-Handbuch für die Familie im Stil von Hausbeschilderung; Farben mit fester Bedeutung (Rot Notfall, Gelb Wartung, Blau Anleitung, Grün Orientierung), DIN-Überschriften, helles und dunkles Design.
- Neue Startseite mit Notfall-Zugang und Alltagsbereichen; neue Navigation: Start, Notfall, Zuhause, Haushalt & Energie, Wartung, Hilfe, Technik.
- Neue Seite **Notfall & Ausfälle**: was bei Ausfall von Home Assistant, Internet oder Strom weiterläuft und was zu tun ist, gerätebezogene Hinweise (Schloss, Wasserventil, Rauchmelder, Wallbox) und Verknüpfung mit einer eigenen Seite `notfall`.
- Neue Seite **Wartung & Pflege** mit Batterietyp je Gerät (Herstellerangabe, typisch oder selbst eingetragen), Batterievorrat für einen Komplettwechsel, Pflegeaufgaben, offenen Einrichtungspunkten und Firmwareständen.
- Neue Seite **Haushalt & Energie**: Energiequellen und erfasste Verbraucher, Auto und Wallbox, Haushaltsgeräte, Heizen und Kühlen, Garten und Wasser mit den zugehörigen Abläufen.
- Neuer Bereich **Technik**: Integrationen mit Internetbedarf, Apps mit Versionen, Zigbee-Netz mit Stromversorgung und unbenannten Geräten, Netzwerk mit Router und WLAN-/LAN-Geräten, Skripte und Helfer.
- Neuer App-Bereich **Live**: Batteriestände mit Batterieanzeige, nicht antwortende Geräte, verfügbare Updates und Alter des letzten Backups; Batterietypen lassen sich direkt eintragen.
- Backup-Auswertung um Skripte, Energie-Konfiguration, HA-Version und App-Liste erweitert; Konfigurationseinträge und Zugangsdaten werden weiterhin nicht gelesen.
- Änderungserkennung berücksichtigt Skripte, Energie, Apps, Firmware und Geräteklassen; ältere Snapshots lösen einen vollständigen Neuaufbau aus.

# 3.2.1

- Kompakter Einstieg und mehr Platz zum Lesen; Überblick heißt jetzt Status.
- Eigene Anleitungen, Protokolle und Wiederherstellung sind aufklappbar.
- Vereinfachte Wiki-Startseite und passende Hinweise für API-Verbindungen.

# 3.2.0

- Provider-Auswahl verständlich benannt: OpenAI Abo, OpenAI API, Claude Abo,
  Claude API und Ohne KI.
- Veraltete ChatGPT-Auswahl entfernt; bestehende Werte werden weiterhin migriert.
- Claude-Abo- und Claude-API-Anmeldung getrennt und die Oberfläche providerabhängig angepasst.

# 3.1.1

- Kurze Erläuterungen für alle Add-on-Konfigurationsoptionen ergänzt.

# 3.1.0

- Claude Code ist als gleichwertige Alternative zum Codex-CLI auswählbar.
- Nicht-interaktive Claude-Aufrufe laufen mit strikt begrenzten Berechtigungen,
  strukturiertem JSON und derselben Validierung wie Codex.
- Providerabhängige Anmeldung, Statusanzeige und Schaltflächen in der Ingress-Oberfläche.
- Optionaler `ANTHROPIC_API_KEY` aus der geschützten Add-on-Konfiguration; OAuth-
  Anmeldung über Claude Code bleibt für Pro/Max-Abos möglich.

# 3.0.2

- Die neueste automatische NAS-Datei wird nach dem Dateinamen ausgewählt; die vollständige Backup-Prüfung bleibt im Generator und verhindert weiterhin unsichere Ersatzstände.

# 3.0.1

- Automatische NAS-Backups werden auch in Unterordnern gefunden; ältere Supervisor-Metadaten ohne `type` bleiben kompatibel.
- Fehlerprotokolle enthalten eine begrenzte, bereinigte Diagnose.

# 3.0.0

- Neue responsive Oberfläche mit Leser-Einstieg und eigener Verwaltung.
- Verständliche Navigation, Hilfe und technische Vertiefung aus dem Backup.
- Rückmeldungen für Aktionen statt wechselnd gesperrter Buttons.
- Strukturierte ChatGPT-Anmeldung mit Ablaufstatus und Abbruch.
- Betriebsprotokoll mit Phasen, Laufbezug und begrenzter Aufbewahrung.
- Korrigierte Ingress-Benutzererkennung und optionales Verwaltungspasswort.
- Bestehende Daten und eigene Seiten bleiben bei der Migration erhalten.
