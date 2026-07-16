---
search:
  exclude: true
---

<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# System \- Recorder Diagnosewerte täglich bereinigen

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Büro · Erdgeschoss, Flur · Erdgeschoss, Garage · Außenbereich, Küche · Erdgeschoss, Sicherungskasten · Keller

## Das bemerkst du im Alltag

Entfernt kurzfristige History für hochfrequente Diagnose\- und Rohwert\-Entities. Energy\-Dashboard\-Quellen sind bewusst nicht enthalten.

## Sie startet, wenn …

1. Es ist 03:20:00 Uhr

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Das betroffene Gerät die hinterlegte Funktion ausführen

## So kannst du reagieren

Keine Bedienung im Alltag. Diese Funktion ist ausschließlich für die technische Wartung durch Max gedacht.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | System \- Recorder Diagnosewerte täglich bereinigen |
    | Home-Assistant-ID | 1778143674031 |
    | Modus | single |
    | Kategorie | System |
    | Verwendete Entities | Stromstärke L1 (`sensor.current_l1_am_anger_3`), Stromstärke L2 (`sensor.current_l2_am_anger_3`), Stromstärke L3 (`sensor.current_l3_am_anger_3`), Voltage L1 (`sensor.go_echarger_252938_nrg`), Voltage L2 (`sensor.go_echarger_252938_nrg_2`), Voltage L3 (`sensor.go_echarger_252938_nrg_3`), Temperature sensor 1 (`sensor.go_echarger_252938_tma`), Temperature sensor 2 (`sensor.go_echarger_252938_tma_2`), Durchschnittliche Umlaufzeit (`sensor.google_dns_ping_durchschnittliche_umlaufzeit`), Netzfrequenz (`sensor.ltibber_01000e0700ff`), Wirkleistung aktuell (`sensor.ltibber_0100100700ff`), Strom L1 (`sensor.ltibber_01001f0700ff`), Spannung L1 (`sensor.ltibber_0100200700ff`), Strom L2 (`sensor.ltibber_0100330700ff`), Spannung L2 (`sensor.ltibber_0100340700ff`), Strom L3 (`sensor.ltibber_0100470700ff`), Spannung L3 (`sensor.ltibber_0100480700ff`), Phasenabweichung Spannungen L1/L2 (`sensor.ltibber_0100510701ff`), Phasenabweichung Spannungen L1/L3 (`sensor.ltibber_0100510702ff`), Phasenabweichung Strom/Spannung L2 (`sensor.ltibber_010051070fff`), Phasenabweichung Strom/Spannung L3 (`sensor.ltibber_010051071aff`), Arbeitsspeicherauslastung (`sensor.memory_use_percent`), Nuki Nuki RSSI (`sensor.nuki_nuki_rssi`), Nuki Öffner RSSI (`sensor.nuki_offner_rssi`), Beleuchtungsstärke (`sensor.prasenzmelder_buro_illuminance`), Target distance (`sensor.prasenzmelder_buro_target_distance`), Beleuchtungsstärke (`sensor.prasenzmelder_kuche_illuminance`), Target distance (`sensor.prasenzmelder_kuche_target_distance`), Prozessortemperatur (`sensor.processor_temperature`), Prozessornutzung (`sensor.processor_use`) |

</div>

<p class="page-status">Definition aus Backup vom 16. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
