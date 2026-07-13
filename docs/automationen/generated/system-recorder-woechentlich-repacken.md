---
search:
  exclude: true
---

<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# System - Recorder wöchentlich repacken

!!! info "Status: ausgeschaltet"
    Ausgeschaltet; dieser zusätzliche Wartungsschritt ist derzeit nicht erforderlich.

**Ort:** kein fester Raum – betrifft das ganze Haus

## Das bemerkst du im Alltag

Repackt die MariaDB wöchentlich nach der 30-Tage-Purge, damit freigegebener Speicher tatsächlich zurückgewonnen wird. Bewusst nur wöchentlich, weil Repack I/O-intensiv ist.

## Sie startet, wenn …

1. Es ist 04:00:00 Uhr

## Sie läuft nur weiter, wenn …

- Der festgelegte Zeitraum ist aktiv

## Dann passiert …

1. Die Home-Assistant-Datenbank warten

## So kannst du reagieren

Keine Bedienung im Alltag. Diese Funktion ist ausschließlich für die technische Wartung durch Max gedacht.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | System - Recorder wöchentlich repacken |
    | Home-Assistant-ID | `1778143687709` |
    | Modus | `single` |
    | Kategorie | System |

</div>

<p class="page-status">Definition aus Backup vom 12. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
