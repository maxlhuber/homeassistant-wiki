<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Auto-Laden Session Start (Snapshot)
## Kurz erklärt
Speichert beim Anstecken die aktuellen Integral-Zaehlerstaende als Startwerte der Ladesession.
## Auslöser
1. Status von Car connected (`binary_sensor.go_echarger_252938_car`) ändert sich von `off` auf `on` für 00:00:05

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. Auto Netz Energie Start (`input_number.auto_netz_energie_start`) Dienst `input_number.set_value` ausführen
2. Auto Solar Energie Start (`input_number.auto_solar_energie_start`) Dienst `input_number.set_value` ausführen
3. Auto Netz Kosten Start (`input_number.auto_netz_kosten_start`) Dienst `input_number.set_value` ausführen
4. Auto-Laden Session abgerechnet (`input_boolean.auto_laden_abgerechnet`) ausschalten

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `auto_laden_session_start` |
| Modus | `single` |
| Kategorie | Energie & Auto |
| Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Auto-Laden Session abgerechnet (`input_boolean.auto_laden_abgerechnet`), Auto Netz Energie Start (`input_number.auto_netz_energie_start`), Auto Netz Kosten Start (`input_number.auto_netz_kosten_start`), Auto Solar Energie Start (`input_number.auto_solar_energie_start`), Auto Netz Energie (`sensor.auto_netz_energie`), Auto Netz Kosten (`sensor.auto_netz_kosten`), Auto Solar Energie (`sensor.auto_solar_energie`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
