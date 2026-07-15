<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Müllabfuhr Benachrichtigung Zentral

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** kein fester Raum – betrifft das ganze Haus

## Das bemerkst du im Alltag

Sammelt alle Müllarten, die am nächsten Tag abgeholt werden, und verschickt um 18:00 eine Erinnerung zum Rausstellen der Tonnen.

## Sie startet, wenn …

1. Es ist 18:00:00 Uhr

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Home Assistant sammelt alle Müllarten, die am nächsten Tag abgeholt werden.
2. Wenn mindestens eine Abholung ansteht, erhalten Max und Meike um 18:00 Uhr eine gemeinsame Erinnerung.

## So kannst du reagieren

Bei einer fehlenden oder unklaren Meldung den Abfuhrtermin im Kalender beziehungsweise beim Entsorger prüfen.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Müllabfuhr Benachrichtigung Zentral |
    | Home-Assistant-ID | 1776706598749 |
    | Modus | single |
    | Kategorie | Haushalt |
    | Verwendete Entities | AbfallBio (`sensor.abfallbio`), AbfallPapier (`sensor.abfallpapier`), AbfallRecycling (`sensor.abfallrecycling`), AbfallRestmuell (`sensor.abfallrestmuell`) |

</div>

<p class="page-status">Definition aus Backup vom 15. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
