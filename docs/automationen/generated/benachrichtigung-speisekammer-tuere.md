<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Benachrichtigung Speisekammer Türe

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Speisekammer · Erdgeschoss

## Das bemerkst du im Alltag

Benachrichtigt beide iPhones, wenn die Speisekammertür 30 Minuten offen steht.

## Sie startet, wenn …

1. Die Speisekammertür wird geöffnet und bleibt 30 Minuten offen.

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Push-Nachricht an Meikes iPhone senden
2. Push-Nachricht an Max' iPhone senden

## So kannst du reagieren

Zuerst die reale Situation vor Ort prüfen. Türen und Fenster von Hand sichern; eine App-Meldung ersetzt keine unmittelbare Sicherheitsmaßnahme.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Benachrichtigung Speisekammer Türe |
    | Home-Assistant-ID | 1768313917380 |
    | Modus | single |
    | Kategorie | Sicherheit & Zugang |
    | Verwendete Entities | Tür (`binary_sensor.turkontakt_speisekammer_contact`) |

</div>

<p class="page-status">Definition aus Backup vom 15. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
