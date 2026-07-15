<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Präsenzmelder Licht Büro an

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Büro · Erdgeschoss

## Das bemerkst du im Alltag

Schaltet das Bürolicht ein, wenn der Präsenzmelder Belegung erkennt. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.

## Sie startet, wenn …

1. Belegung wechselt auf „eingeschaltet“

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Büro einschalten mit 100 % Helligkeit

## So kannst du reagieren

Das betroffene Licht in Home Assistant oder am vorhandenen Wandschalter direkt bedienen. Reagiert es unerwartet, nicht zurücksetzen, sondern Max informieren.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Präsenzmelder Licht Büro an |
    | Home-Assistant-ID | 1768311911626 |
    | Modus | single |
    | Kategorie | Licht & Präsenz |
    | Verwendete Entities | Belegung (`binary_sensor.prasenzmelder_buro_presence`), Büro (`light.buro_2`) |

</div>

<p class="page-status">Definition aus Backup vom 15. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
