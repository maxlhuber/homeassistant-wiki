<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Präsenzmelder Licht Büro an
## Kurz erklärt
Schaltet das Bürolicht ein, wenn der Präsenzmelder Belegung erkennt. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.
## Auslöser
1. Status von Belegung (`binary_sensor.prasenzmelder_buro_presence`) ändert sich auf `on`

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. Büro (`light.buro_2`) einschalten mit 100 % Helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768311911626` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | Belegung (`binary_sensor.prasenzmelder_buro_presence`), Büro (`light.buro_2`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
