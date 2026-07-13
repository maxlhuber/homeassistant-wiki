<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Präsenzmelder Küche Licht an
## Kurz erklärt
Schaltet das Küchenlicht mit voller Helligkeit ein, wenn der Präsenzmelder in der Küche Belegung erkennt.
## Auslöser
1. Status von Belegung (`binary_sensor.prasenzmelder_kuche_presence`) ändert sich auf `on`

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. Küche (`light.kuche_2`) einschalten mit 100 % Helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768753491689` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | Belegung (`binary_sensor.prasenzmelder_kuche_presence`), Küche (`light.kuche_2`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
