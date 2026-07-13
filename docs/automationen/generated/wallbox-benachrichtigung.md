<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wallbox Benachrichtigung
## Kurz erklärt
Informiert Max, wenn die Wallbox aktiv lädt, das Auto angeschlossen ist und noch nicht voll geladen wurde.
## Auslöser
1. Status von Force state (`select.go_echarger_252938_frc`) ändert sich auf `Charge`

## Bedingungen
- logische Bedingungsgruppe `and` ist erfüllt

## Ablauf
1. Push-Nachricht an Max' iPhone senden. Der aktuelle Strompreis wird korrekt in `ct/kWh` angegeben.

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1763020246492` |
| Modus | `single` |
| Kategorie | Energie & Auto |
| Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Force state (`select.go_echarger_252938_frc`), Aktueller Strompreis (`sensor.am_anger_3_aktueller_strompreis`), Ladezustand (`sensor.born_ladezustand_4`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Preiseinheit am 13. Juli 2026 live korrigiert</p>
