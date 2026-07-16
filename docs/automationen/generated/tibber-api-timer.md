---
search:
  exclude: true
---

<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Tibber API Timer

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Sicherungskasten · Keller

## Das bemerkst du im Alltag

Aktualisiert den aktuellen Strompreis beim Home\-Assistant\-Start und anschließend alle 15 Minuten.

## Sie startet, wenn …

1. Das festgelegte Zeitintervall ist erreicht
2. Das betroffene Gerät meldet das passende Ereignis

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Die zugehörigen Daten aktualisieren

## So kannst du reagieren

Ladezustand und Freigabe zusätzlich am Fahrzeug beziehungsweise an der Wallbox kontrollieren.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Tibber API Timer |
    | Home-Assistant-ID | 1742480921483 |
    | Modus | single |
    | Kategorie | Energie & Auto |
    | Verwendete Entities | Strompreis aktuell (`sensor.electricity_price_am_anger_3`) |

</div>

<p class="page-status">Definition aus Backup vom 16. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
