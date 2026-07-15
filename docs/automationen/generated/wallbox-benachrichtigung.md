<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Ladebeginn an Max melden

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Garage · Außenbereich

## Das bemerkst du im Alltag

Informiert Max, wenn die Wallbox aktiv lädt, das Auto angeschlossen ist und noch nicht voll geladen wurde.

## Sie startet, wenn …

1. Die Wallbox wechselt in den Lademodus.

## Sie läuft nur weiter, wenn …

- Das Auto ist angeschlossen, lädt gerade und ist noch nicht voll.

## Dann passiert …

1. Max erhält eine Push-Nachricht zum Ladebeginn mit dem aktuellen Strompreis in ct/kWh.
2. Die Nachricht nennt den aktuellen Strompreis in ct/kWh.

## So kannst du reagieren

Den tatsächlichen Ladezustand im Fahrzeug oder an der Wallbox prüfen. Eine fehlende Nachricht stoppt oder startet keinen Ladevorgang.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Wallbox Benachrichtigung |
    | Home-Assistant-ID | 1763020246492 |
    | Modus | single |
    | Kategorie | Energie & Auto |
    | Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Force state (`select.go_echarger_252938_frc`), Aktueller Strompreis (`sensor.am_anger_3_aktueller_strompreis`), Ladezustand (`sensor.born_ladezustand_4`) |

</div>

<p class="page-status">Definition aus Backup vom 15. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
