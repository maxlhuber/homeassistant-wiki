<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Schlafzimmer
## Kurz erklärt
Reagiert auf den linken Tastendruck des Schlafzimmer-Wandschalters. Beim Einschalten wird tagsüber 100 Prozent und nachts zwischen Sonnenuntergang und Sonnenaufgang 30 Prozent Helligkeit gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Schlafzimmer

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn `light.schlafzimmer` hat den status `on`, dann `light.schlafzimmer` ausschalten; andernfalls wenn logische bedingungsgruppe `or` ist erfüllt, dann `light.schlafzimmer` einschalten mit 30 % helligkeit; andernfalls `light.schlafzimmer` einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768302882039` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | `light.schlafzimmer` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
