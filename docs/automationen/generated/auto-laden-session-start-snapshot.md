---
search:
  exclude: true
---

<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Auto-Laden Session Start (Snapshot)

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Garage · Außenbereich

## Das bemerkst du im Alltag

Merkt sich beim Anstecken die Zählerstände, damit Home Assistant später Energieanteile und Kosten dieser Ladesitzung berechnen kann. Der Ladevorgang wird dadurch nicht gestartet.

## Sie startet, wenn …

1. Car connected wechselt von „ausgeschaltet“ auf „eingeschaltet“ und bleibt dort 00:00:05

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Einen internen Startwert speichern
2. Einen internen Startwert speichern
3. Einen internen Startwert speichern
4. Auto-Laden Session abgerechnet ausschalten

## So kannst du reagieren

Keine Bedienung im Alltag. Bei einer falschen Ladezusammenfassung den tatsächlichen Zähler- und Fahrzeugstand notieren und Max informieren.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Auto-Laden Session Start (Snapshot) |
    | Home-Assistant-ID | `auto_laden_session_start` |
    | Modus | `single` |
    | Kategorie | Energie & Auto |
    | Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Auto-Laden Session abgerechnet (`input_boolean.auto_laden_abgerechnet`), Auto Netz Energie Start (`input_number.auto_netz_energie_start`), Auto Netz Kosten Start (`input_number.auto_netz_kosten_start`), Auto Solar Energie Start (`input_number.auto_solar_energie_start`), Auto Netz Energie (`sensor.auto_netz_energie`), Auto Netz Kosten (`sensor.auto_netz_kosten`), Auto Solar Energie (`sensor.auto_solar_energie`) |

</div>

<p class="page-status">Definition aus Backup vom 12. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
