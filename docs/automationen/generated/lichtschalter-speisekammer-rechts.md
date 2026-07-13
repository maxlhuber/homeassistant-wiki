<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Speisekammer rechts
## Kurz erklärt
Schaltet den Küchenflur bei rechtem Tastendruck des Z2M-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Speisekammer

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn `light.kuchenflur` hat den status `on`, dann `light.kuchenflur` ausschalten; andernfalls `light.kuchenflur` einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1777721039128` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | `light.kuchenflur` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
