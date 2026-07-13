<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Benachrichtigung Fensterkontakt Bad

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Bad · Erdgeschoss

## Das bemerkst du im Alltag

Benachrichtigt beide iPhones, wenn das Badfenster 30 Minuten offen steht.

## Sie startet, wenn …

1. Das Badfenster wird geöffnet und bleibt 30 Minuten offen.

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
    | Ursprünglicher Name | Benachrichtigung Fensterkontakt Bad |
    | Home-Assistant-ID | `1768313851346` |
    | Modus | `single` |
    | Kategorie | Sicherheit & Zugang |
    | Verwendete Entities | Tür (`binary_sensor.fensterkontakt_bad_contact`) |

</div>

<p class="page-status">Definition aus Backup vom 12. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
