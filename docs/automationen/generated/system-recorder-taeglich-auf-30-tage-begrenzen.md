<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# System - Recorder täglich auf 30 Tage begrenzen
!!! info "Derzeit ausgeschaltet"
    Diese zusätzliche Bereinigung wurde am 13. Juli 2026 ausgeschaltet, weil der Recorder die festgelegte Aufbewahrung bereits selbst verwaltet.

## Kurz erklärt
Hält die kurzfristige Recorder-History bei 30 Tagen. Long-term statistics bleiben erhalten und werden vom Energy-Dashboard weiter genutzt.
## Auslöser
1. Zeitpunkt `03:10:00` ist erreicht

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. festgelegtes Ziel Dienst `recorder.purge` ausführen

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1778143654356` |
| Modus | `single` |
| Kategorie | System |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Am 13. Juli 2026 live ausgeschaltet</p>
