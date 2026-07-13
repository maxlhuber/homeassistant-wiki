<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Ikea Shortcut Haustüre
## Kurz erklärt
Nutzt den IKEA-Shortcut an der Haustüre als Alles-aus-Schalter für alle Lichter außer Büro oder als Einschalter für den Kronleuchter im Flur mit Standardhelligkeit.
## Auslöser
1. Geräteereignis „action“ von Ikea Shortcut Haustüre

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. wenn alle lichter außer büro (`light.alle_lichter_ausser_buro`) hat den status `['on']`, dann alle lichter außer büro (`light.alle_lichter_ausser_buro`) ausschalten; andernfalls wenn logische bedingungsgruppe `or` ist erfüllt, dann `light.kronleuchter_flur` einschalten mit 30 % helligkeit; andernfalls `light.kronleuchter_flur` einschalten mit 100 % helligkeit

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768303055798` |
| Modus | `single` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | Alle Lichter außer Büro (`light.alle_lichter_ausser_buro`), `light.kronleuchter_flur` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
