<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Küche oben
## Kurz erklärt
Schaltet das Küchenlicht bei linkem Tastendruck des Z2M-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.
## Auslöser
1. Geräteereignis „action“ von Wandschalter Küche

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn küche (`light.kuche_2`) hat den status `on`, dann küche (`light.kuche_2`) ausschalten; andernfalls küche (`light.kuche_2`) einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768302399176` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | Küche (`light.kuche_2`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
