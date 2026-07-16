<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Lichtschalter Ikea Shortcut Haustüre

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Flur · Erdgeschoss

## Das bemerkst du im Alltag

Nutzt den IKEA\-Shortcut an der Haustüre als Alles\-aus\-Schalter für alle Lichter außer Büro oder als Einschalter für den Kronleuchter im Flur mit Standardhelligkeit.

## Sie startet, wenn …

1. Eine Taste am IKEA-Shortcut an der Haustür wird gedrückt.

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Wenn noch eines der zusammengefassten Lichter außer Büro an ist, schaltet Home Assistant diese Lichter aus.
2. Sind diese Lichter bereits aus, schaltet Home Assistant den Kronleuchter im Flur ein: nachts mit 30 Prozent, sonst mit 100 Prozent Helligkeit.

## So kannst du reagieren

Das betroffene Licht in Home Assistant oder am vorhandenen Wandschalter direkt bedienen. Reagiert es unerwartet, nicht zurücksetzen, sondern Max informieren.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Lichtschalter Ikea Shortcut Haustüre |
    | Home-Assistant-ID | 1768303055798 |
    | Modus | single |
    | Kategorie | Licht & Präsenz |
    | Verwendete Entities | Alle Lichter außer Büro (`light.alle_lichter_ausser_buro`), Kronleuchter flur (`light.kronleuchter_flur`) |

</div>

<p class="page-status">Definition aus Backup vom 16. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
