<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Wohnzimmer oben
## Kurz erklärt
Schaltet das Licht am Esstisch bei linkem Tastendruck des Wohnzimmer-Wandschalters. Beim Einschalten werden 100 Prozent Helligkeit und die definierte Farbtemperatur gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Wohnzimmer

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn `light.esstisch` hat den status `on`, dann `light.esstisch` ausschalten; andernfalls `light.esstisch` einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768303690130` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | `light.esstisch` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
