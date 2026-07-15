<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Haustür öffnen, wenn Max oder Meike ankommen

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

!!! warning "Wichtig"
    Eine ungenaue Standorterkennung kann die Tür unerwartet öffnen. Bei einer unerwarteten Öffnung Haustür sichern und Max informieren.

**Ort:** Flur · Erdgeschoss

## Das bemerkst du im Alltag

Öffnet den Nuki-Öffner, wenn das iPhone von Max oder Meike nach einer Abwesenheit seit 30 Sekunden wieder als zu Hause erkannt wird. Weitere Bedingungen sind nicht hinterlegt.

## Sie startet, wenn …

1. Max’ iPhone oder Meikes iPhone wird nach einer Abwesenheit 30 Sekunden lang als „zu Hause“ erkannt.

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Den Nuki-Öffner öffnen

## So kannst du reagieren

Wenn die automatische Öffnung ausbleibt, Schlüssel oder Nuki-Bedienung verwenden. Nicht wiederholt durch Weggehen und Zurückkommen testen.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Tür öffnen wenn Max zuhause ankommt |
    | Home-Assistant-ID | 1768477812326 |
    | Modus | single |
    | Kategorie | Sicherheit & Zugang |
    | Verwendete Entities | Hase (`device_tracker.max_iphone`), Meikes iPhone (`device_tracker.meikes_iphone`), Nuki Öffner Lock (`lock.nuki_offner_lock`) |

</div>

<p class="page-status">Definition aus Backup vom 15. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
