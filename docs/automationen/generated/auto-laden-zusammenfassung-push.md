<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Auto-Laden Zusammenfassung (Push)
## Kurz erklärt
Sendet die Zusammenfassung (kWh, Solar/Netz, Durchschnittspreis) an Max iPhone - beim Erreichen von "Voll geladen" oder beim Abstecken (je nachdem was zuerst kommt), aber pro Ladesession nur einmal.
## Auslöser
1. Status von Wallbox Zielstatus (`sensor.wallbox_zielstatus`) ändert sich auf `Voll geladen`
2. Status von Car connected (`binary_sensor.go_echarger_252938_car`) ändert sich von `on` auf `off` für 00:00:05

## Bedingungen
- Auto-Laden Session abgerechnet (`input_boolean.auto_laden_abgerechnet`) hat den Status `off`
- eine interne Vorlagenprüfung ist erfüllt

## Ablauf
1. Auto-Laden Session abgerechnet (`input_boolean.auto_laden_abgerechnet`) einschalten
2. wenn eine interne vorlagenprüfung ist erfüllt, dann push-nachricht an max' iphone senden; andernfalls push-nachricht an max' iphone senden

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `auto_laden_zusammenfassung` |
| Modus | `single` |
| Kategorie | Energie & Auto |
| Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Auto-Laden Session abgerechnet (`input_boolean.auto_laden_abgerechnet`), Auto Netz Energie Start (`input_number.auto_netz_energie_start`), Auto Netz Kosten Start (`input_number.auto_netz_kosten_start`), Auto Solar Energie Start (`input_number.auto_solar_energie_start`), Auto Netz Energie (`sensor.auto_netz_energie`), Auto Netz Kosten (`sensor.auto_netz_kosten`), Auto Solar Energie (`sensor.auto_solar_energie`), Wallbox Zielstatus (`sensor.wallbox_zielstatus`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
