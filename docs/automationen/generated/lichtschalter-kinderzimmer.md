<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Kinderzimmer
## Kurz erklärt
Schaltet aktuell das Licht im Spielzimmer bei linkem Tastendruck des Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Spielzimmer

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn spielzimmer (`light.spielzimmer`) hat den status `on`, dann spielzimmer (`light.spielzimmer`) ausschalten; andernfalls spielzimmer (`light.spielzimmer`) einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768302032548` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | Spielzimmer (`light.spielzimmer`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
