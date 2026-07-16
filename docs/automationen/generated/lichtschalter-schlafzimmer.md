<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Schlafzimmer

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Schlafzimmer · Erdgeschoss

## Das bemerkst du im Alltag

Reagiert auf den linken Tastendruck des Schlafzimmer\-Wandschalters. Beim Einschalten wird tagsüber 100 Prozent und nachts zwischen Sonnenuntergang und Sonnenaufgang 30 Prozent Helligkeit gesetzt.

## Sie startet, wenn …

1. Eine Taste am Wandschalter Schlafzimmer wird gedrückt

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Ist das Schlafzimmerlicht an, wird es ausgeschaltet.
2. Ist es aus, wird es nachts mit 30 Prozent und tagsüber mit 100 Prozent Helligkeit eingeschaltet.

## So kannst du reagieren

Das betroffene Licht in Home Assistant oder am vorhandenen Wandschalter direkt bedienen. Reagiert es unerwartet, nicht zurücksetzen, sondern Max informieren.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Lichtschalter Schlafzimmer |
    | Home-Assistant-ID | 1768302882039 |
    | Modus | single |
    | Kategorie | Licht & Präsenz |
    | Verwendete Entities | Schlafzimmer (`light.schlafzimmer`) |

</div>

<p class="page-status">Definition aus Backup vom 16. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
