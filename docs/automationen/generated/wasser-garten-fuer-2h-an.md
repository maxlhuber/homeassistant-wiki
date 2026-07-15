<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wasser Garten für 2h an

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Garten · Außenbereich

## Das bemerkst du im Alltag

Schaltet das Garten\-Wasserventil per Helfer\-Taste für 2 Stunden ein, sofern es aktuell ausgeschaltet ist.

## Sie startet, wenn …

1. Wasser 2h wechselt

## Sie läuft nur weiter, wenn …

- Wasserventil garten ist „ausgeschaltet“

## Dann passiert …

1. Wasserventil garten einschalten
2. 2 Std. warten
3. Wasserventil garten ausschalten

## So kannst du reagieren

Die betroffene Funktion in Home Assistant direkt bedienen. Bei Wasser immer vor Ort prüfen, ob das Ventil anschließend wirklich geschlossen ist.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Wasser Garten für 2h an |
    | Home-Assistant-ID | 1750963246422 |
    | Modus | single |
    | Kategorie | Garten & Wasser |
    | Verwendete Entities | Wasser 2h (`input_button.wasser_2h`), Wasserventil garten (`switch.wasserventil_garten`) |

</div>

<p class="page-status">Definition aus Backup vom 15. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
