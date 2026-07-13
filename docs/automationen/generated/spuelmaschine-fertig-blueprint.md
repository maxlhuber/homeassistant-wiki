<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Spülmaschine fertig Blueprint
## Kurz erklärt
Benachrichtigt Max und Meike, wenn die Spülmaschine laut Leistungsaufnahme fertig ist.
## Auslöser
1. Die Auslöser werden durch einen Blueprint festgelegt.

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. Der Ablauf wird durch einen Blueprint festgelegt.
2. Nach Programmende erhalten Max und Meike jeweils eine Push-Nachricht. Fällt ein Versandweg aus, wird der andere trotzdem ausgeführt.

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Blueprint
Technische Vorlage: `sbyx/notify-or-do-something-when-an-appliance-like-a-dishwasher-or-washing-machine-finishes.yaml`

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1767206525153` |
| Modus | `single` |
| Kategorie | Haushalt |
| Verwendete Entities | Leistung (`sensor.steckdose_spulmaschine_power`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Empfänger am 13. Juli 2026 live aktualisiert</p>
