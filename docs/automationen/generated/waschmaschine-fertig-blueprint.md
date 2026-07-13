<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Waschmaschine ist fertig

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Waschküche · Keller

## Das bemerkst du im Alltag

Benachrichtigt Max und Meike, wenn die Waschmaschine laut Leistungsaufnahme fertig ist.

## Sie startet, wenn …

1. Home Assistant erkennt anhand des Stromverbrauchs oder Gerätezustands, dass der Ablauf beendet ist

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Die im Namen und in der Kurzbeschreibung genannte Meldung oder Aktion ausführen

## So kannst du reagieren

Die Waschmaschine funktioniert unabhängig von dieser Meldung. Bleibt die Nachricht aus, Programmende direkt am Gerät prüfen.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Waschmaschine fertig Blueprint |
    | Home-Assistant-ID | `1767206458674` |
    | Modus | `single` |
    | Kategorie | Haushalt |
    | Verwendete Entities | Leistung (`sensor.steckdose_waschmaschine_power`) |
    | Blueprint | `sbyx/notify-or-do-something-when-an-appliance-like-a-dishwasher-or-washing-machine-finishes.yaml` |

</div>

<p class="page-status">Definition aus Backup vom 12. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
