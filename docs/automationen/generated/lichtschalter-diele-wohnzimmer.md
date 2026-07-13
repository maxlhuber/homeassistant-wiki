<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Diele Wohnzimmer
## Kurz erklärt
Schaltet das Flurlicht bei linkem Tastendruck des Diele-Wohnzimmer-Wandschalters. Beim Einschalten wird tagsüber 100 Prozent und nachts zwischen Sonnenuntergang und Sonnenaufgang 30 Prozent Helligkeit gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Diele Wohnzimmer

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn `light.flur` hat den status `on`, dann `light.flur` ausschalten; andernfalls wenn logische bedingungsgruppe `or` ist erfüllt, dann `light.flur` einschalten mit 30 % helligkeit; andernfalls `light.flur` einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768303993349` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | `light.flur` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
