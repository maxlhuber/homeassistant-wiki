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
