<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Bad
## Kurz erklärt
Reagiert auf den linken Tastendruck des Bad-Wandschalters. Beim Einschalten wird tagsüber 100 Prozent und nachts zwischen Sonnenuntergang und Sonnenaufgang 30 Prozent Helligkeit gesetzt.
## Auslöser
1. MQTT-Nachricht am Thema `zigbee2mqtt/Wandschalter Bad`

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn `light.bad` hat den status `on`, dann `light.bad` ausschalten; andernfalls wenn logische bedingungsgruppe `or` ist erfüllt, dann `light.bad` einschalten mit 30 % helligkeit; andernfalls `light.bad` einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768302744548` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | `light.bad` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
