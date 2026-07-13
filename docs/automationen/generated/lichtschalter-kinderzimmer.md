<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Kinderzimmer

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

!!! warning "Wichtig"
    Raum- und Gerätenamen widersprechen sich: Der „Kinderzimmer“-Schalter steuert laut Home Assistant derzeit das Spielzimmer. Die Zuordnung muss vor Ort bestätigt werden.

**Ort:** Kinderzimmer · Erdgeschoss

## Das bemerkst du im Alltag

Schaltet aktuell das Licht im Spielzimmer bei linkem Tastendruck des Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt.

## Sie startet, wenn …

1. Eine Taste am Wandschalter Spielzimmer wird gedrückt

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Wenn spielzimmer ist „eingeschaltet“, dann spielzimmer ausschalten; andernfalls spielzimmer einschalten mit 100 % helligkeit

## So kannst du reagieren

Das betroffene Licht in Home Assistant oder am vorhandenen Wandschalter direkt bedienen. Reagiert es unerwartet, nicht zurücksetzen, sondern Max informieren.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Lichtschalter Kinderzimmer |
    | Home-Assistant-ID | `1768302032548` |
    | Modus | `single` |
    | Kategorie | Licht & Präsenz |
    | Verwendete Entities | Spielzimmer (`light.spielzimmer`) |

</div>

<p class="page-status">Definition aus Backup vom 12. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
