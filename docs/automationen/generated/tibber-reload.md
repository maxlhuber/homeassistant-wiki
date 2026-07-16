---
search:
  exclude: true
---

<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Tibber Reload

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Sicherungskasten · Keller

## Das bemerkst du im Alltag

Lädt den Tibber\-Config\-Eintrag neu, wenn der Spannungssensor länger als 1 Minute unavailable ist.

## Sie startet, wenn …

1. Spannung L1 wechselt auf „nicht erreichbar“ und bleibt dort 1 Min.

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Das betroffene Gerät die hinterlegte Funktion ausführen

## So kannst du reagieren

Ladezustand und Freigabe zusätzlich am Fahrzeug beziehungsweise an der Wallbox kontrollieren.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Tibber Reload |
    | Home-Assistant-ID | 1750446203882 |
    | Modus | single |
    | Kategorie | Energie & Auto |
    | Verwendete Entities | Spannung L1 (`sensor.voltage_phase1_am_anger_3`) |

</div>

<p class="page-status">Definition aus Backup vom 16. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
