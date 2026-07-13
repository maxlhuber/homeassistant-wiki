<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Türkontakt Speisekammer aus
## Kurz erklärt
Schaltet das Speisekammerlicht aus, wenn die Tür geschlossen wird.
## Auslöser
1. Status von Tür (`binary_sensor.turkontakt_speisekammer_contact`) ändert sich auf `off`

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. `light.speisekammer` ausschalten

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768303490874` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | Tür (`binary_sensor.turkontakt_speisekammer_contact`), `light.speisekammer` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
