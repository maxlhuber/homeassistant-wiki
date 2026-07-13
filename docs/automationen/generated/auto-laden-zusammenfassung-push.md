<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Auto-Laden Zusammenfassung (Push)

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Garage · Außenbereich

## Das bemerkst du im Alltag

Sendet Max nach dem Vollladen oder Abstecken eine Zusammenfassung zu geladener Energie, Solar- und Netzanteil sowie durchschnittlichem Preis.

## Sie startet, wenn …

1. Die Wallbox meldet „voll geladen“ oder das Auto ist seit fünf Sekunden abgesteckt.

## Sie läuft nur weiter, wenn …

- Diese Ladesitzung wurde noch nicht abgerechnet und die benötigten Zählerwerte sind vorhanden.

## Dann passiert …

1. Home Assistant markiert die Ladesitzung als abgerechnet.
2. Max erhält eine Zusammenfassung zu Energie, Solar-/Netzanteil und durchschnittlichem Preis.

## So kannst du reagieren

Die Nachricht ist nur eine Auswertung. Den wirklichen Ladezustand am Fahrzeug oder an der Wallbox prüfen.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Auto-Laden Zusammenfassung (Push) |
    | Home-Assistant-ID | `auto_laden_zusammenfassung` |
    | Modus | `single` |
    | Kategorie | Energie & Auto |
    | Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Auto-Laden Session abgerechnet (`input_boolean.auto_laden_abgerechnet`), Auto Netz Energie Start (`input_number.auto_netz_energie_start`), Auto Netz Kosten Start (`input_number.auto_netz_kosten_start`), Auto Solar Energie Start (`input_number.auto_solar_energie_start`), Auto Netz Energie (`sensor.auto_netz_energie`), Auto Netz Kosten (`sensor.auto_netz_kosten`), Auto Solar Energie (`sensor.auto_solar_energie`), Wallbox Zielstatus (`sensor.wallbox_zielstatus`) |

</div>

<p class="page-status">Definition aus Backup vom 12. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
