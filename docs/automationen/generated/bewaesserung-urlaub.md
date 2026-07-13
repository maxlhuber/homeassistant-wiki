<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Gartenbewässerung täglich um 09:00 Uhr

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

!!! warning "Wichtig"
    Der Name in Home Assistant ist missverständlich: Die Bewässerung läuft täglich, nicht nur im Urlaub.

**Ort:** Garten · Außenbereich

## Das bemerkst du im Alltag

Wenn diese Automation eingeschaltet ist, öffnet sie das Gartenventil jeden Tag um 09:00 Uhr für zwei Minuten. Ein Urlaubsmodus wird derzeit nicht geprüft.

## Sie startet, wenn …

1. Es ist 09:00:00 Uhr

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Wasserventil garten einschalten
2. 2 Min. warten
3. Wasserventil garten ausschalten

## So kannst du reagieren

In Home Assistant kann die Automation ausgeschaltet werden. Nach einer manuellen Betätigung prüfen, ob das Gartenventil wieder geschlossen ist.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Bewässerung Urlaub |
    | Home-Assistant-ID | `1780053635371` |
    | Modus | `single` |
    | Kategorie | Garten & Wasser |
    | Verwendete Entities | Wasserventil garten (`switch.wasserventil_garten`) |

</div>

<p class="page-status">Definition aus Backup vom 12. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
