<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wallbox Benachrichtigung 2
## Kurz erklärt
Informiert Max über den aktuellen Strompreis, wenn das Auto zuhause, aber noch nicht angesteckt und nicht voll geladen ist.
## Auslöser
1. Status von Force state (`select.go_echarger_252938_frc`) ändert sich auf `Charge`

## Bedingungen
- logische Bedingungsgruppe `and` ist erfüllt

## Ablauf
1. Push-Nachricht an Max' iPhone senden

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1763020590547` |
| Modus | `single` |
| Kategorie | Energie & Auto |
| Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Max (`person.max`), Meike (`person.meike`), Force state (`select.go_echarger_252938_frc`), Ladezustand (`sensor.born_ladezustand_4`), Strompreis aktuell (`sensor.electricity_price_am_anger_3`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
