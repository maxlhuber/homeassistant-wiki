<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Garten oben
## Kurz erklärt
Schaltet die Terrassenbeleuchtung bei linkem Tastendruck des Garten-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Garten

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn `light.terasse` hat den status `on`, dann `light.terasse` ausschalten; andernfalls `light.terasse` einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768303832798` |
| Modus | `single` |
| Kategorie | Garten & Wasser |
| Verwendete Entities | `light.terasse` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
