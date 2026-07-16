<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Laden bei Anwesenheit anbieten

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Garage · Außenbereich

## Das bemerkst du im Alltag

Informiert Max über den aktuellen Strompreis, wenn das Auto zuhause, aber noch nicht angesteckt und nicht voll geladen ist.

## Sie startet, wenn …

1. Home Assistant erhält das Signal, eine mögliche Ladung zu prüfen.

## Sie läuft nur weiter, wenn …

- Das Auto ist zu Hause, noch nicht angeschlossen und noch nicht voll geladen.

## Dann passiert …

1. Max erhält eine Push-Nachricht mit dem aktuellen Strompreis und dem Ladeangebot.

## So kannst du reagieren

Den tatsächlichen Ladezustand im Fahrzeug oder an der Wallbox prüfen. Bei Unklarheit keine Ladefreigabe nur aufgrund einer Push-Nachricht erteilen.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Wallbox Benachrichtigung 2 |
    | Home-Assistant-ID | 1763020590547 |
    | Modus | single |
    | Kategorie | Energie & Auto |
    | Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Max (`person.max`), Meike (`person.meike`), Force state (`select.go_echarger_252938_frc`), Ladezustand (`sensor.born_ladezustand_4`), Strompreis aktuell (`sensor.electricity_price_am_anger_3`) |

</div>

<p class="page-status">Definition aus Backup vom 16. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
