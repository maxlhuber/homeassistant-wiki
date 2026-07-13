<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Wohnzimmer unten
## Kurz erklärt
Schaltet das Wohnzimmerlicht bei rechtem Tastendruck des Wohnzimmer-Wandschalters. Beim Einschalten werden 100 Prozent Helligkeit und die definierte Farbtemperatur gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Wohnzimmer

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn `light.wohnzimmer` hat den status `on`, dann `light.wohnzimmer` ausschalten; andernfalls `light.wohnzimmer` einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768303742730` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | `light.wohnzimmer` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
