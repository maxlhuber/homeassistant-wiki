<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Spülmaschine ist fertig

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Küche · Erdgeschoss

## Das bemerkst du im Alltag

Benachrichtigt Max und Meike, wenn die Spülmaschine laut gemessener Leistungsaufnahme fertig ist.

## Sie startet, wenn …

1. Home Assistant erkennt anhand des Stromverbrauchs oder Gerätezustands, dass der Ablauf beendet ist

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Die im Namen und in der Kurzbeschreibung genannte Meldung oder Aktion ausführen
2. Max und Meike erhalten jeweils eine Push-Nachricht.
3. Fällt ein Versandweg aus, wird der andere trotzdem versucht.

## So kannst du reagieren

Die Spülmaschine funktioniert unabhängig von dieser Meldung. Bleibt die Nachricht aus, Programmende direkt am Gerät prüfen.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Spülmaschine fertig Blueprint |
    | Home-Assistant-ID | 1767206525153 |
    | Modus | single |
    | Kategorie | Haushalt |
    | Verwendete Entities | Leistung (`sensor.steckdose_spulmaschine_power`) |
    | Blueprint | sbyx/notify\-or\-do\-something\-when\-an\-appliance\-like\-a\-dishwasher\-or\-washing\-machine\-finishes.yaml |

</div>

<p class="page-status">Definition aus Backup vom 15. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
