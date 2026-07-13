<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wallbox Override Reset
!!! warning "Derzeit ausgeschaltet"
    Die verwendete Entity `switch.wallbox_override` existiert nicht mehr. Die Automation bleibt deshalb ausgeschaltet, bis eine passende Ersatz-Entity festgelegt wurde.

## Kurz erklärt
Setzt den Wallbox-Override nach 2 Stunden wieder aus und informiert Max per Push-Nachricht.
## Auslöser
1. Status von `switch.wallbox_override` ändert sich auf `on` für 2 Std.

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. `switch.wallbox_override` ausschalten
2. Push-Nachricht an Max' iPhone senden

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1742245735922` |
| Modus | `single` |
| Kategorie | Energie & Auto |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Live-Status am 13. Juli 2026 bestätigt</p>
