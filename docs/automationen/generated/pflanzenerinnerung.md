<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Pflanzenerinnerung
## Kurz erklärt
Erinnert am 1. und 14. jedes Monats um 13:00 Uhr ans Gießen und wiederholt die Erinnerung alle 3 Stunden, bis der Gießkannen-Helfer zurückgesetzt wird.
## Auslöser
1. Zeitpunkt `13:00:00` ist erreicht

## Bedingungen
- logische Bedingungsgruppe `or` ist erfüllt

## Ablauf
1. Gießkanne (`input_boolean.giesskanne`) einschalten
2. eine festgelegte Schrittfolge wiederholen

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1680323841770` |
| Modus | `single` |
| Kategorie | Garten & Wasser |
| Verwendete Entities | Gießkanne (`input_boolean.giesskanne`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
