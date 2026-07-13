<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# System - Recorder wöchentlich repacken
!!! info "Derzeit ausgeschaltet"
    Diese zusätzliche, I/O-intensive Bereinigung wurde am 13. Juli 2026 ausgeschaltet. Sie kann bei einem späteren Wartungsbedarf gezielt wieder aktiviert werden.

## Kurz erklärt
Repackt die MariaDB wöchentlich nach der 30-Tage-Purge, damit freigegebener Speicher tatsächlich zurückgewonnen wird. Bewusst nur wöchentlich, weil Repack I/O-intensiv ist.
## Auslöser
1. Zeitpunkt `04:00:00` ist erreicht

## Bedingungen
- der festgelegte Zeitraum ist aktiv

## Ablauf
1. festgelegtes Ziel Dienst `recorder.purge` ausführen

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1778143687709` |
| Modus | `single` |
| Kategorie | System |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Am 13. Juli 2026 live ausgeschaltet</p>
