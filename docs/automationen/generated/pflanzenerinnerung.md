<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Pflanzenerinnerung

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** kein fester Raum – betrifft das ganze Haus

## Das bemerkst du im Alltag

Erinnert am 1. und 14. jedes Monats um 13:00 Uhr ans Gießen und wiederholt die Erinnerung alle 3 Stunden, bis der Gießkannen\-Helfer zurückgesetzt wird.

## Sie startet, wenn …

1. Es ist 13:00:00 Uhr

## Sie läuft nur weiter, wenn …

- Es ist der 1. oder 14. Tag des Monats.

## Dann passiert …

1. Home Assistant sendet eine Erinnerung zum Pflanzengießen.
2. Die Erinnerung wird alle drei Stunden wiederholt, bis sie in der Handy-Meldung als erledigt bestätigt wird.

## So kannst du reagieren

Die Erinnerung kann über die Aktion „gegossen“ in der Handy-Meldung beendet werden. Sie schaltet kein Wasserventil.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Pflanzenerinnerung |
    | Home-Assistant-ID | 1680323841770 |
    | Modus | single |
    | Kategorie | Garten & Wasser |
    | Verwendete Entities | Gießkanne (`input_boolean.giesskanne`) |

</div>

<p class="page-status">Definition aus Backup vom 15. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
