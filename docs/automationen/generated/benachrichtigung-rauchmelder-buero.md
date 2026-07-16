<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Benachrichtigung Rauchmelder Büro

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

!!! warning "Wichtig"
    Die Handy-Meldung ist nur eine Zusatzwarnung. Bei Rauch oder Feuer Menschen in Sicherheit bringen und im Zweifel 112 wählen.

**Ort:** Büro · Erdgeschoss

## Das bemerkst du im Alltag

Sendet Max und Meike eine zusätzliche Alarmmeldung, wenn der Rauchmelder im Büro Rauch erkennt.

## Sie startet, wenn …

1. Der Rauchmelder im Büro erkennt Rauch.

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Push-Nachricht an Max' iPhone senden
2. Push-Nachricht an Meikes iPhone senden
3. Push-Nachricht an Meikes iPhone senden
4. Beide Versandwege werden unabhängig voneinander versucht.

## So kannst du reagieren

Nicht auf die App warten: Den hörbaren Rauchmelder und die Situation vor Ort ernst nehmen. Nur bei sicher erkanntem Fehlalarm lüften und den Melder nach Herstelleranleitung prüfen.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Benachrichtigung Rauchmelder Büro |
    | Home-Assistant-ID | 1768313703595 |
    | Modus | single |
    | Kategorie | Sicherheit & Zugang |
    | Verwendete Entities | Rauch (`binary_sensor.rauchmelder_buro_smoke`) |

</div>

<p class="page-status">Definition aus Backup vom 16. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
