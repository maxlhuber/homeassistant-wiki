<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# System - Recorder Diagnosewerte täglich bereinigen
## Kurz erklärt
Entfernt kurzfristige History für hochfrequente Diagnose- und Rohwert-Entities. Energy-Dashboard-Quellen sind bewusst nicht enthalten.
## Auslöser
1. Zeitpunkt `03:20:00` ist erreicht

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. festgelegtes Ziel Dienst `recorder.purge_entities` ausführen

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1778143674031` |
| Modus | `single` |
| Kategorie | System |
| Verwendete Entities | Stromstärke L1 (`sensor.current_l1_am_anger_3`), Stromstärke L2 (`sensor.current_l2_am_anger_3`), Stromstärke L3 (`sensor.current_l3_am_anger_3`), Voltage L1 (`sensor.go_echarger_252938_nrg`), Voltage L2 (`sensor.go_echarger_252938_nrg_2`), Voltage L3 (`sensor.go_echarger_252938_nrg_3`), Temperature sensor 1 (`sensor.go_echarger_252938_tma`), Temperature sensor 2 (`sensor.go_echarger_252938_tma_2`), Durchschnittliche Umlaufzeit (`sensor.google_dns_ping_durchschnittliche_umlaufzeit`), Netzfrequenz (`sensor.ltibber_01000e0700ff`), Wirkleistung aktuell (`sensor.ltibber_0100100700ff`), Strom L1 (`sensor.ltibber_01001f0700ff`), Spannung L1 (`sensor.ltibber_0100200700ff`), Strom L2 (`sensor.ltibber_0100330700ff`), Spannung L2 (`sensor.ltibber_0100340700ff`), Strom L3 (`sensor.ltibber_0100470700ff`), Spannung L3 (`sensor.ltibber_0100480700ff`), Phasenabweichung Spannungen L1/L2 (`sensor.ltibber_0100510701ff`), Phasenabweichung Spannungen L1/L3 (`sensor.ltibber_0100510702ff`), Phasenabweichung Strom/Spannung L2 (`sensor.ltibber_010051070fff`), Phasenabweichung Strom/Spannung L3 (`sensor.ltibber_010051071aff`), Arbeitsspeicherauslastung (`sensor.memory_use_percent`), Nuki Nuki RSSI (`sensor.nuki_nuki_rssi`), Nuki Öffner RSSI (`sensor.nuki_offner_rssi`), Beleuchtungsstärke (`sensor.prasenzmelder_buro_illuminance`), Target distance (`sensor.prasenzmelder_buro_target_distance`), Beleuchtungsstärke (`sensor.prasenzmelder_kuche_illuminance`), Target distance (`sensor.prasenzmelder_kuche_target_distance`), Prozessortemperatur (`sensor.processor_temperature`), Prozessornutzung (`sensor.processor_use`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
