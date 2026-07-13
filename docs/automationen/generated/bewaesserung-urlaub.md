<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Bewässerung Urlaub
## Kurz erklärt
Wenn zeitpunkt `09:00:00` ist erreicht, wird anschließend `switch.wasserventil_garten` einschalten.
## Auslöser
1. Zeitpunkt `09:00:00` ist erreicht

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. `switch.wasserventil_garten` einschalten
2. 2 Min. warten
3. `switch.wasserventil_garten` ausschalten

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1780053635371` |
| Modus | `single` |
| Kategorie | Garten & Wasser |
| Verwendete Entities | `switch.wasserventil_garten` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
