<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Büro
## Kurz erklärt
Schaltet das Bürolicht bei linkem Tastendruck des Z2M-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Büro

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn büro (`light.buro_2`) hat den status `on`, dann büro (`light.buro_2`) ausschalten; andernfalls büro (`light.buro_2`) einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768301816686` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | Büro (`light.buro_2`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
