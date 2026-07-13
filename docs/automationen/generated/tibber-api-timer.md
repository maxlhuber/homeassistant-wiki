<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Tibber API Timer
## Kurz erklärt
Aktualisiert den aktuellen Strompreis beim Home-Assistant-Start und anschließend alle 15 Minuten.
## Auslöser
1. regelmäßiges Zeitmuster ist erreicht
2. Auslöser `homeassistant` bei nicht näher angegeben

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. festgelegtes Ziel Dienst `homeassistant.update_entity` ausführen

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1742480921483` |
| Modus | `single` |
| Kategorie | Energie & Auto |
| Verwendete Entities | Strompreis aktuell (`sensor.electricity_price_am_anger_3`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
