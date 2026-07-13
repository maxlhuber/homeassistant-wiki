---
search:
  exclude: true
---

# Bestandsaufnahme

Diese Seite beschreibt, welche Informationen für den Aufbau des Wikis benötigt werden und wie dabei sensible Daten geschützt werden.

## Benötigte Informationen

- Etagen und Räume beziehungsweise Bereiche
- Geräte und ihre Standorte
- Automationen, Skripte und Szenen
- Helfer, Zeitpläne und wichtige Gruppen
- Integrationen und Funkstandards
- wichtige Dashboards und manuelle Bedienelemente
- Sicherungs- und Neustartverfahren

## Bevorzugter Importweg

1. In Home Assistant unter **Einstellungen → System → Sicherungen** eine manuelle Sicherung erstellen.
2. Medien- und Freigabeordner können für diese Bestandsaufnahme abgewählt werden.
3. Die Sicherung über die Home-Assistant-Oberfläche herunterladen.
4. Die heruntergeladene Datei ausschließlich im lokalen Projektordner `eingang` ablegen.
5. Die Sicherung nicht per E-Mail oder Messenger verschicken und nicht in Git aufnehmen.

Der Ordner `eingang` wird vom Projekt ausdrücklich ignoriert. Inhalte daraus dienen nur zur lokalen Auswertung und erscheinen nicht in der fertigen Website.

!!! danger "Sensible Inhalte"
    Eine Home-Assistant-Sicherung kann Zugangsdaten, Geräteschlüssel, Standorte und Nutzungsverläufe enthalten. Sie wird wie ein Passwort behandelt. `secrets.yaml`, Tokens und Schlüssel werden niemals in das Wiki übernommen.

## Zusätzliche Fragen

Für verständliche Alltagstexte werden später noch kurze persönliche Angaben benötigt:

- Welche Automationen sind besonders wichtig?
- Was soll deine Frau im Fehlerfall selbst ausprobieren dürfen?
- Welche Geräte dürfen keinesfalls ausgeschaltet oder zurückgesetzt werden?
- Welche Begriffe verwendet ihr im Alltag für Räume, Modi und Geräte?

<p class="page-status">Zuletzt geprüft: 12. Juli 2026 · Status: Bereit zur Bestandsaufnahme</p>
