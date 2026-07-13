<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Türkontakt Speisekammer ein
## Kurz erklärt
Schaltet das Speisekammerlicht ein, wenn die Tür geöffnet wird. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.
## Auslöser
1. Status von Tür (`binary_sensor.turkontakt_speisekammer_contact`) ändert sich auf `on`

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. `light.speisekammer` einschalten mit 100 % Helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768303465614` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | Tür (`binary_sensor.turkontakt_speisekammer_contact`), `light.speisekammer` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
