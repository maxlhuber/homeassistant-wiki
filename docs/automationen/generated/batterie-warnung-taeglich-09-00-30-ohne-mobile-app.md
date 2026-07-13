<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Batterie-Warnung täglich 09:00 (< 30%, ohne Mobile-App)

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** kein fester Raum – betrifft das ganze Haus

## Das bemerkst du im Alltag

Prüft täglich um 09:00 alle Batterie-Sensoren unter 30 Prozent, ignoriert Mobile-App-Geräte und sendet für jedes betroffene Gerät eine Push-Nachricht.

## Sie startet, wenn …

1. Es ist 09:00:00 Uhr

## Sie läuft nur weiter, wenn …

- Mindestens ein berücksichtigter Batterie-Sensor meldet weniger als 30 Prozent.

## Dann passiert …

1. Home Assistant ermittelt die betroffenen Geräte.
2. Für jedes betroffene Gerät wird eine Push-Nachricht mit dem Batteriestand gesendet.

## So kannst du reagieren

Das genannte Gerät aufsuchen und Batterie beziehungsweise Ladezustand direkt prüfen. Eine fehlende Meldung ändert den Gerätezustand nicht.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Batterie-Warnung täglich 09:00 (< 30%, ohne Mobile-App) |
    | Home-Assistant-ID | `1765563499671` |
    | Modus | `single` |
    | Kategorie | Energie & Auto |

</div>

<p class="page-status">Definition aus Backup vom 12. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
