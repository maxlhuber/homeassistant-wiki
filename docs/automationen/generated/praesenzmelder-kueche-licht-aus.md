<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Präsenzmelder Küche Licht aus
## Kurz erklärt
Schaltet das Küchenlicht aus, wenn der Präsenzmelder in der Küche keine Belegung mehr erkennt.
## Auslöser
1. Status von Belegung (`binary_sensor.prasenzmelder_kuche_presence`) ändert sich auf `off`

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. Küche (`light.kuche_2`) ausschalten

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768753412175` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | Belegung (`binary_sensor.prasenzmelder_kuche_presence`), Küche (`light.kuche_2`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
