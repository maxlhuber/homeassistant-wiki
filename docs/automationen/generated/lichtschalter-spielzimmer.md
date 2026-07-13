<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Spielzimmer
## Kurz erklärt
Schaltet aktuell das Licht im Kinderzimmer bei linkem Tastendruck des Wandschalters im Spielzimmer. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Kinderzimmer

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn `light.kinderzimmer` hat den status `on`, dann `light.kinderzimmer` ausschalten; andernfalls `light.kinderzimmer` einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768302068809` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | `light.kinderzimmer` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
